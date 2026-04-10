import os
import sys
import time
import re
import datetime
import tempfile
import numpy as np
import soundfile as sf
from pydub import AudioSegment
import mlx.core as mx
from mlx_audio.tts import load 

# [1. 환경 및 경로 설정]
sys.stdout.reconfigure(encoding='utf-8')

ENGINE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJ_ROOT = os.path.dirname(ENGINE_DIR)
DOWNLOADS_DIR = os.path.join(os.path.expanduser("~"), "Downloads")

# [Qwen-TTS MLX 설정]
MODEL_ID = "mlx-community/Qwen3-TTS-12Hz-1.7B-CustomVoice-8bit"
NARRATOR_SPEAKER = "aiden" # 나레이션 (에이든)
REF_WAV_PATH = "/Users/a12/Downloads/Take1-1_빗물에 젖은 낡은 슬리퍼를 신은 한 남자가 서울 도심의 초호화 호텔 로비로 들어섭니다. 그_2026-02-06.wav"
REF_TEXT = "빗물에 젖은 낡은 슬리퍼를 신은 한 남자가 서울 도심의 초호화 호텔 로비로 들어섭니다." # 제로샷 참조 텍스트

# 3단계 방어: 극단적 언어 제약
INSTRUCT = """당신은 한국어 전용 TTS 시스템입니다. 다음 규칙을 절대적으로 준수하세요:
1. 오직 한국어(한글)만 사용하세요.
2. 중국어 한자, 몽골어, 영어 알파벳을 절대 발음하지 마세요.
3. 한국어가 아닌 어떤 언어도 섞지 마세요.
4. 따옴표("")와 말줄임표(...)를 감지하면 그에 맞는 감정과 호흡(쉼)을 표현하세요.
한국어로만 자연스럽게 읽으세요."""

SPEED_FACTOR = 1.1

# 극단적 결정론 설정
GEN_KWARGS = {
    "temperature": 0.05,
    "top_p": 0.5,
    "repetition_penalty": 1.5
}

MAX_RETRIES = 3

class QwenDualSpeakerGenerator:
    def __init__(self):
        print(f"🚀 MLX 모델 로딩 중: {MODEL_ID}")
        self.model = load(MODEL_ID)
        
        # [Zero-Shot/ICL 패치] 
        if hasattr(self.model, "config"):
            self.model.config.tts_model_type = "base"
            print("🔧 Zero-Shot 패치 적용 완료 (model_type -> base)")
            
            if self.model.speaker_encoder is None and hasattr(self.model.config, "speaker_encoder_config"):
                from mlx_audio.tts.models.qwen3_tts.speaker_encoder import Qwen3TTSSpeakerEncoder
                self.model.speaker_encoder = Qwen3TTSSpeakerEncoder(self.model.config.speaker_encoder_config)
                print("🎙️ Speaker Encoder 활성화 완료")
            
            # 차원 불일치 패치 (1024 -> 2048)
            original_extract = self.model.extract_speaker_embedding
            def patched_extract(audio, sr=24000):
                emb = original_extract(audio, sr)
                if emb.shape[-1] == 1024:
                    emb = mx.concatenate([emb, emb], axis=-1)
                return emb
            self.model.extract_speaker_embedding = patched_extract
            print("📐 차원 불일치 패치 완료 (1024 -> 2048)")
        
        if not os.path.exists(REF_WAV_PATH):
            print(f"⚠️ 경고: 커스텀 보이스 파일을 찾을 수 없습니다. 대사도 성우로 대체됩니다: {REF_WAV_PATH}")

    def clean_text(self, text):
        # 괄호 안의 내용 및 지문 제거
        text = re.sub(r'\[(BGM|묘사|지문|설명|배경|음악|CHAPTER|챕터|SFX):?.*?\]', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\(.*?\)', '', text)
        return text.strip()

    def split_smart_chunks(self, text):
        """나레이션과 대사(따옴표)를 분리하여 청크 생성"""
        # 따옴표를 기준으로 텍스트 분할하되 따옴표는 유지
        # 예: 나레이션 "대사" 나레이션 -> [나레이션, "대사", 나레이션]
        raw_chunks = re.split(r'("[^"]*")', text)
        chunks = []
        for c in raw_chunks:
            c = c.strip()
            if not c: continue
            # 너무 긴 나레이션은 구두점으로 한 번 더 분리
            if '"' not in c:
                sub_chunks = re.split(r'(?<=[.,!?])\s*', c)
                chunks.extend([sc.strip() for sc in sub_chunks if sc.strip()])
            else:
                chunks.append(c)
        return chunks

    def format_srt_time(self, seconds):
        td = datetime.datetime.fromtimestamp(seconds, datetime.UTC)
        return td.strftime('%H:%M:%S,%f')[:-3]

    def validate_korean_only(self, text):
        korean_pattern = re.compile(r'^[가-힣0-9\s.,!?\-"\'\'\"]+$')
        return korean_pattern.match(text) is not None
    
    def generate_chunk_with_retry(self, chunk, chunk_idx):
        # 대사 여부 확인
        is_dialogue = '"' in chunk
        speaker_mode = "CustomVoice" if is_dialogue else "Aiden"
        
        for attempt in range(MAX_RETRIES):
            try:
                if is_dialogue and os.path.exists(REF_WAV_PATH):
                    # 커스텀 보이스 (Dialogue)
                    results = self.model.generate(
                        text=chunk, 
                        ref_audio=REF_WAV_PATH, 
                        ref_text=REF_TEXT,
                        language="Korean",
                        instruct=INSTRUCT,
                        **GEN_KWARGS
                    )
                else:
                    # 에이든 (Narration) - generate_custom_voice 대신 generate 호출
                    results = self.model.generate(
                        text=chunk, 
                        voice=NARRATOR_SPEAKER, 
                        language="Korean", 
                        instruct=INSTRUCT,
                        **GEN_KWARGS
                    )
                
                segment_audio_mx = None
                sr = 24000
                for res in results:
                    if segment_audio_mx is None:
                        segment_audio_mx = res.audio
                    else:
                        segment_audio_mx = mx.concatenate([segment_audio_mx, res.audio])
                
                if segment_audio_mx is not None:
                    return segment_audio_mx, sr, speaker_mode
                else:
                    print(f"   ⚠️ 시도 {attempt + 1}/{MAX_RETRIES}: 오디오 생성 실패")
                    
            except Exception as e:
                print(f"   ⚠️ 시도 {attempt + 1}/{MAX_RETRIES}: 에러 - {e}")
        
        return None, None, speaker_mode

    def run(self, script_text, output_path):
        chunks = self.split_smart_chunks(self.clean_text(script_text))
        print(f"🎭 Total Dual-Speaker Chunks: {len(chunks)}")
        
        combined_audio = AudioSegment.empty()
        srt_entries = []
        current_time_ms = 0
        start_time = time.time()
        
        for i, chunk in enumerate(chunks):
            if not self.validate_korean_only(chunk):
                # 허용되지 않은 문자 제거 (보수적 필터링)
                chunk = re.sub(r'[^가-힣0-9\s.,!?\-"\'\'\"]+', '', chunk)
            
            print(f"⚡ [Dual {i+1}/{len(chunks)}] Generating: {chunk[:30]}...")
            
            segment_audio_mx, sr, speaker_mode = self.generate_chunk_with_retry(chunk, i)
            
            if segment_audio_mx is None:
                print(f"   ⏭️ 청크 {i+1} 스킵")
                continue
            
            print(f"   ✅ Speaker: {speaker_mode}")
            
            audio_np = np.array(segment_audio_mx)
            shared_buf = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
            sf.write(shared_buf.name, audio_np, sr)
            shared_buf.close()
            
            segment = AudioSegment.from_wav(shared_buf.name)
            os.unlink(shared_buf.name)
            
            if SPEED_FACTOR != 1.0:
                segment = segment.speedup(playback_speed=SPEED_FACTOR, chunk_size=150, crossfade=25)
            
            duration_ms = len(segment)
            combined_audio += segment
            
            # SRT
            start_sec = current_time_ms / 1000.0
            end_sec = (current_time_ms + duration_ms) / 1000.0
            srt_entries.append(f"{i + 1}\n{self.format_srt_time(start_sec)} --> {self.format_srt_time(end_sec)}\n[{speaker_mode}] {chunk}\n\n")
            
            current_time_ms += duration_ms
            
            if i < len(chunks) - 1:
                # 대사와 나레이션 사이의 호흡 조절
                pause_ms = 600 if '"' in chunk else 300
                combined_audio += AudioSegment.silent(duration=pause_ms)
                current_time_ms += pause_ms

        combined_audio.export(output_path, format="mp3", bitrate="192k")
        srt_path = output_path.replace(".mp3", ".srt")
        with open(srt_path, "w", encoding="utf-8-sig") as f:
            f.writelines(srt_entries)
            
        elapsed = time.time() - start_time
        print(f"🏆 Dual Speaker 완료: {os.path.basename(output_path)} ({elapsed:.1f}s)")

if __name__ == "__main__":
    target_file = sys.argv[1] if len(sys.argv) > 1 else os.path.join(PROJ_ROOT, "대본.txt")
    if os.path.exists(target_file):
        with open(target_file, "r", encoding="utf-8") as f:
            script_text = f.read().strip()
        if script_text:
            timestamp = datetime.datetime.now().strftime("%m%d_%H%M")
            base_filename = os.path.splitext(os.path.basename(target_file))[0]
            output_name = f"{base_filename}_Dual_Speaker_{timestamp}.mp3"
            output_path = os.path.join(DOWNLOADS_DIR, output_name)
            
            generator = QwenDualSpeakerGenerator()
            generator.run(script_text, output_path)
        else: print("❌ 빈 대본")
    else: print("❌ 파일 없음")

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
CHUNKS_DIR = os.path.join(DOWNLOADS_DIR, "chunks")  # 청크 개별 저장 폴더

# [Qwen-TTS MLX 설정 - 커스텀 보이스 모드 + 청크 저장]
MODEL_ID = "mlx-community/Qwen3-TTS-12Hz-1.7B-CustomVoice-8bit"

# 사용자의 녹음 파일 경로
REF_WAV_PATH = "/Users/a12/Downloads/Take1-1_빗물에 젖은 낡은 슬리퍼를 신은 한 남자가 서울 도심의 초호화 호텔 로비로 들어섭니다. 그_2026-02-06.wav"

# 3단계 방어: 극단적 언어 제약
INSTRUCT = """당신은 한국어 전용 TTS 시스템입니다. 다음 규칙을 절대적으로 준수하세요:
1. 오직 한국어(한글)만 사용하세요.
2. 중국어 한자, 몽골어, 영어 알파벳을 절대 발음하지 마세요.
3. 한국어가 아닌 어떤 언어도 섞지 마세요.
4. 따옴표("")와 말줄임표(...)를 감지하면 그에 맞는 감정과 호흡(쉼)을 표현하세요.
한국어로만 자연스럽게 읽으세요."""

SPEED_FACTOR = 1.1

# 극단적 결정론 설정 (환각 완전 차단)
GEN_KWARGS = {
    "temperature": 0.05,      # 거의 greedy decoding (환각 0%)
    "top_p": 0.5,             # 상위 50%만 샘플링
    "repetition_penalty": 1.5 # 반복 강력 억제
}

MAX_RETRIES = 3

class QwenCustomVoiceWithChunks:
    def __init__(self):
        print(f"🚀 MLX 모델 로딩 중: {MODEL_ID}")
        self.model = load(MODEL_ID)
        
        # [Zero-Shot 패치] MLX-Audio의 Qwen3-TTS 래퍼는 'custom_voice' 모델일 경우 
        # 반드시 미리 정의된 voice 이름을 요구합니다. 이를 'base' 타입으로 속여 
        # zero-shot(ICL) 기능이 작동하게 합니다.
        if hasattr(self.model, "config"):
            self.model.config.tts_model_type = "base"
            print("🔧 Zero-Shot 패치 적용 완료 (model_type -> base)")
            
            # Speaker Encoder 초기화 (Base 모델이 아니면 None일 수 있음)
            if self.model.speaker_encoder is None and hasattr(self.model.config, "speaker_encoder_config"):
                from mlx_audio.tts.models.qwen3_tts.speaker_encoder import Qwen3TTSSpeakerEncoder
                self.model.speaker_encoder = Qwen3TTSSpeakerEncoder(self.model.config.speaker_encoder_config)
                print("🎙️ Speaker Encoder 활성화 완료")
            
            # [차원 불일치 패치] Speaker Encoder는 1024차원을 출력하지만, 
            # Talker 모델은 2048차원을 기대합니다 (Concatenate 에러 발생).
            # 이를 위해 출력을 2048차원으로 확장하는 래퍼를 씌웁니다.
            original_extract = self.model.extract_speaker_embedding
            def patched_extract(audio, sr=24000):
                emb = original_extract(audio, sr)
                # 1024 -> 2048 (단순 반복 또는 제로 패딩)
                # 여기서는 가장 안전한 방식인 반복(Repeat)을 시도합니다.
                if emb.shape[-1] == 1024:
                    emb = mx.concatenate([emb, emb], axis=-1)
                return emb
            
            self.model.extract_speaker_embedding = patched_extract
            print("📐 차원 불일치 패치 완료 (1024 -> 2048)")
        
        if not os.path.exists(REF_WAV_PATH):
            print(f"❌ 커스텀 보이스 파일을 찾을 수 없습니다: {REF_WAV_PATH}")
            sys.exit(1)
        
        # 청크 저장 폴더 생성
        os.makedirs(CHUNKS_DIR, exist_ok=True)
        print(f"📁 청크 저장 폴더: {CHUNKS_DIR}")
        print(f"🎙️ 커스텀 보이스 로드 완료: {os.path.basename(REF_WAV_PATH)}")
        print("✅ MLX 로딩 완료! (Zero-Shot Cloning Ready)")

    def clean_text(self, text):
        # 괄호 안의 내용 및 지문 제거
        text = re.sub(r'\[(BGM|묘사|지문|설명|배경|음악|CHAPTER|챕터|SFX):?.*?\]', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\(.*?\)', '', text)
        return text.strip()

    def split_chunks(self, text):
        chunks = re.split(r'(?<=[.,!?])\s*', text)
        return [c.strip() for c in chunks if c.strip()]

    def format_srt_time(self, seconds):
        td = datetime.datetime.fromtimestamp(seconds, datetime.UTC)
        return td.strftime('%H:%M:%S,%f')[:-3]

    def validate_korean_only(self, text):
        korean_pattern = re.compile(r'^[가-힣0-9\s.,!?\-"\'\'\"]+$')
        return korean_pattern.match(text) is not None
    
    def generate_chunk_with_retry(self, chunk, chunk_idx):
        for attempt in range(MAX_RETRIES):
            try:
                # generate 함수를 직접 사용하여 ref_audio 및 ref_text 전달 (ICL 모드 활성화)
                # 커스텀 녹음 파일의 내용을 첫 번째 문장으로 참조 텍스트(ref_text)로 제공
                ref_text = "빗물에 젖은 낡은 슬리퍼를 신은 한 남자가 서울 도심의 초호화 호텔 로비로 들어섭니다."
                
                results = self.model.generate(
                    text=chunk, 
                    ref_audio=REF_WAV_PATH, 
                    ref_text=ref_text,
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
                    # ✅ 청크별 개별 파일 저장 (마음에 드는 걸 골라 쓰기 위함)
                    chunk_filename = os.path.join(CHUNKS_DIR, f"chunk_{chunk_idx:03d}.wav")
                    audio_np = np.array(segment_audio_mx)
                    sf.write(chunk_filename, audio_np, sr)
                    print(f"   💾 청크 저장됨: chunk_{chunk_idx:03d}.wav")
                    
                    return segment_audio_mx, sr
                else:
                    print(f"   ⚠️ 시도 {attempt + 1}/{MAX_RETRIES}: 오디오 생성 실패")
                    
            except Exception as e:
                print(f"   ⚠️ 시도 {attempt + 1}/{MAX_RETRIES}: 에러 - {e}")
                import traceback
                traceback.print_exc()
        
        return None, None

    def run(self, script_text, output_path):
        chunks = self.split_chunks(self.clean_text(script_text))
        print(f"📦 Total Custom Voice Chunks: {len(chunks)}")
        print(f"💾 각 청크는 {CHUNKS_DIR}에 개별 저장됩니다.")
        
        combined_audio = AudioSegment.empty()
        srt_entries = []
        current_time_ms = 0
        
        start_time = time.time()
        
        for i, chunk in enumerate(chunks):
            if not self.validate_korean_only(chunk):
                chunk = re.sub(r'[^가-힣0-9\s.,!?\-"\'\'\"]+', '', chunk)
            
            print(f"⚡ [Custom {i+1}/{len(chunks)}] Generating: {chunk[:30]}...")
            
            segment_audio_mx, sr = self.generate_chunk_with_retry(chunk, i)
            
            if segment_audio_mx is None:
                print(f"   ⏭️ 청크 {i+1} 스킵")
                continue
            
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
            srt_entries.append(f"{i + 1}\n{self.format_srt_time(start_sec)} --> {self.format_srt_time(end_sec)}\n{chunk}\n\n")
            
            current_time_ms += duration_ms
            
            if i < len(chunks) - 1:
                pause_ms = 500 if any(chunk.endswith(p) for p in ['.', '?', '!']) else 200
                combined_audio += AudioSegment.silent(duration=pause_ms)
                current_time_ms += pause_ms

        combined_audio.export(output_path, format="mp3", bitrate="192k")
        srt_path = output_path.replace(".mp3", ".srt")
        with open(srt_path, "w", encoding="utf-8-sig") as f:
            f.writelines(srt_entries)
            
        elapsed = time.time() - start_time
        print(f"🏆 Custom Voice 완료: {os.path.basename(output_path)} ({elapsed:.1f}s)")
        print(f"📂 개별 청크: {CHUNKS_DIR}")

if __name__ == "__main__":
    target_file = sys.argv[1] if len(sys.argv) > 1 else os.path.join(PROJ_ROOT, "대본.txt")
    if os.path.exists(target_file):
        with open(target_file, "r", encoding="utf-8") as f:
            script_text = f.read().strip()
        if script_text:
            timestamp = datetime.datetime.now().strftime("%m%d_%H%M")
            base_filename = os.path.splitext(os.path.basename(target_file))[0]
            output_name = f"{base_filename}_Custom_Chunks_{timestamp}.mp3"
            output_path = os.path.join(DOWNLOADS_DIR, output_name)
            
            generator = QwenCustomVoiceWithChunks()
            generator.run(script_text, output_path)
        else: print("❌ 빈 대본")
    else: print("❌ 파일 없음")

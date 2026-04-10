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
VOICE_LIB_DIR = os.path.join(PROJ_ROOT, "voices")

# [Qwen-TTS MLX 설정 - 고정 라이브러리 듀얼 모드]
MODEL_ID = "mlx-community/Qwen3-TTS-12Hz-1.7B-CustomVoice-8bit"

# 황금 목소리 참조 (Library)
NARRATOR_WAV = os.path.join(VOICE_LIB_DIR, "golden_voice_8.wav") # 8번 청크 기반 (나레이션)
NARRATOR_TEXT = "남자는 바닥에 엎드러지며 당황한 기색으로 입을 엽니다."

DIALOGUE_WAV = os.path.join(VOICE_LIB_DIR, "golden_voice_2.wav") # 2번 청크 기반 (대사)
DIALOGUE_TEXT = "그의 손에는 때 묻은 비닐봉지 하나가 들려 있었습니다."

# 3단계 방어: 극단적 언어 제약 (사용자 제안: 20년 경력 KBS 앵커 페르소나)
INSTRUCT = """당신은 서울 표준어를 사용하는 20년 경력의 한국인 성우입니다. 
중국어나 영어 억양을 절대 섞지 말고, KBS 뉴스 앵커처럼 정확하고 단호한 한국어 어조로만 낭독하세요. 
40대 중저음으로 비장하면서도 차분하게 읽으세요. 어떤 외국어도 섞지 마세요."""

SPEED_FACTOR = 1.1

GEN_KWARGS = {
    "temperature": 0.0,  # 극단적 결정론 (환각 및 톤 이탈 원천 차단)
    "top_p": 1.0,
    "repetition_penalty": 1.5
}

MAX_RETRIES = 3

# [패치 완료] MLX-Audio 및 차원 교정 패치만 유지합니다. (시드는 run 루프에서 mx.random.seed로 제어)
print("🎲 시드 제어 준비 완료 (Global Seed Strategy)")

# 기존 _generate_with_instruct 및 _generate_icl 등도 시드를 전달받도록 래핑해야 하지만,
# 여기서는 가장 많이 쓰이는 generate()와 그 내부 호출을 수정하는 대신, 
# 전역 mx.random.seed를 호출 시점마다 설정하는 방식으로 보완합니다.

class QwenStableDualGenerator:
    def __init__(self):
        print(f"🚀 MLX 모델 로딩 중: {MODEL_ID}")
        self.model = load(MODEL_ID)
        
        # [Zero-Shot/ICL 패치]
        if hasattr(self.model, "config"):
            self.model.config.tts_model_type = "base"
            if self.model.speaker_encoder is None and hasattr(self.model.config, "speaker_encoder_config"):
                from mlx_audio.tts.models.qwen3_tts.speaker_encoder import Qwen3TTSSpeakerEncoder
                self.model.speaker_encoder = Qwen3TTSSpeakerEncoder(self.model.config.speaker_encoder_config)
            
            # 차원 불일치 패치
            original_extract = self.model.extract_speaker_embedding
            def patched_extract(audio, sr=24000):
                emb = original_extract(audio, sr)
                if emb.shape[-1] == 1024:
                    emb = mx.concatenate([emb, emb], axis=-1)
                return emb
            self.model.extract_speaker_embedding = patched_extract
            print("🔧 MLX 패치 및 차원 교정 완료")
        
        # 라이브러리 체크
        if not os.path.exists(NARRATOR_WAV) or not os.path.exists(DIALOGUE_WAV):
            print(f"❌ 보이스 라이브러리 파일을 찾을 수 없습니다: {VOICE_LIB_DIR}")
            sys.exit(1)
        print("✅ 보이스 라이브러리 연결 완료 (G8 & G2)")

    def clean_text(self, text):
        text = re.sub(r'\[(BGM|묘사|지문|설명|배경|음악|CHAPTER|챕터|SFX):?.*?\]', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\(.*?\)', '', text)
        return text.strip()

    def split_smart_chunks(self, text):
        raw_chunks = re.split(r'("[^"]*")', text)
        chunks = []
        for c in raw_chunks:
            c = c.strip()
            if not c: continue
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
        is_dialogue = '"' in chunk
        ref_wav = DIALOGUE_WAV if is_dialogue else NARRATOR_WAV
        ref_text = DIALOGUE_TEXT if is_dialogue else NARRATOR_TEXT
        speaker_mode = "Golden_2 (Dialogue)" if is_dialogue else "Golden_8 (Narrator)"
        
        # [시드 고정] 8번과 2번의 행운을 재현하기 위해 고정 시드 사용
        current_seed = 8 if not is_dialogue else 2
        mx.random.seed(current_seed)
        
        for attempt in range(MAX_RETRIES):
            try:
                # generate 내부에서 _sample_token을 호출할 때 MLX의 전역 랜덤 상태를 사용함
                results = self.model.generate(
                    text=chunk, 
                    ref_audio=ref_wav, 
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
                    return segment_audio_mx, sr, speaker_mode
                else:
                    print(f"   ⚠️ 시도 {attempt + 1}/{MAX_RETRIES}: 오디오 생성 실패")
            except Exception as e:
                print(f"   ⚠️ 시도 {attempt + 1}/{MAX_RETRIES}: 에러 - {e}")
        
        return None, None, speaker_mode

    def run(self, script_text, output_path):
        chunks = self.split_smart_chunks(self.clean_text(script_text))
        print(f"🏛️ Total Library Chunks: {len(chunks)}")
        
        combined_audio = AudioSegment.empty()
        srt_entries = []
        current_time_ms = 0
        start_time = time.time()
        
        for i, chunk in enumerate(chunks):
            if not self.validate_korean_only(chunk):
                chunk = re.sub(r'[^가-힣0-9\s.,!?\-"\'\'\"]+', '', chunk)
            
            print(f"⚡ [Dual {i+1}/{len(chunks)}] Generating: {chunk[:30]}...")
            segment_audio_mx, sr, speaker_mode = self.generate_chunk_with_retry(chunk, i)
            
            if segment_audio_mx is None:
                print(f"   ⏭️ 청크 {i+1} 스킵")
                continue
            
            print(f"   ✅ Mode: {speaker_mode}")
            
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
                pause_ms = 600 if '"' in chunk else 300
                combined_audio += AudioSegment.silent(duration=pause_ms)
                current_time_ms += pause_ms

        combined_audio.export(output_path, format="mp3", bitrate="192k")
        srt_path = output_path.replace(".mp3", ".srt")
        with open(srt_path, "w", encoding="utf-8-sig") as f:
            f.writelines(srt_entries)
            
        elapsed = time.time() - start_time
        print(f"🏆 Library Completed: {os.path.basename(output_path)} ({elapsed:.1f}s)")

if __name__ == "__main__":
    target_file = sys.argv[1] if len(sys.argv) > 1 else os.path.join(PROJ_ROOT, "대본.txt")
    if os.path.exists(target_file):
        with open(target_file, "r", encoding="utf-8") as f:
            script_text = f.read().strip()
        if script_text:
            timestamp = datetime.datetime.now().strftime("%m%d_%H%M")
            base_filename = os.path.splitext(os.path.basename(target_file))[0]
            output_name = f"{base_filename}_LIB_Dual_{timestamp}.mp3"
            output_path = os.path.join(DOWNLOADS_DIR, output_name)
            
            generator = QwenStableDualGenerator()
            generator.run(script_text, output_path)
        else: print("❌ 빈 대본")
    else: print("❌ 파일 없음")

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
from mlx_audio.tts import load # mlx-audio의 공식 진입점

# [1. 환경 및 경로 설정]
sys.stdout.reconfigure(encoding='utf-8')

ENGINE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJ_ROOT = os.path.dirname(ENGINE_DIR)
DOWNLOADS_DIR = os.path.join(os.path.expanduser("~"), "Downloads")

# [Qwen-TTS MLX 설정 - 외국어 환각 완전 차단 모드]
MODEL_ID = "mlx-community/Qwen3-TTS-12Hz-1.7B-CustomVoice-8bit"
SPEAKER = "aiden" # 더 깊고 무게감 있는 남성 성우 (eric에서 변경)

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

# 재시도 설정
MAX_RETRIES = 3  # 청크당 최대 재시도 횟수

class QwenMLXGenerator:
    def __init__(self):
        print(f"🚀 MLX 모델 로딩 중: {MODEL_ID}")
        # mlx-audio의 공식 load 함수 사용
        self.model = load(MODEL_ID)
        print("✅ MLX 로딩 완료! (Apple Silicon Native)")

    def clean_text(self, text):
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
        """한국어 외 문자 감지 (중국어 한자, 몽골 키릴 등)"""
        # 한국어 허용 범위: 한글, 숫자, 기본 구두점, 공백
        korean_pattern = re.compile(r'^[가-힣0-9\s.,!?\-"\'\'\"]+$')
        return korean_pattern.match(text) is not None
    
    def generate_chunk_with_retry(self, chunk, chunk_idx):
        """재시도 로직이 포함된 청크 생성"""
        for attempt in range(MAX_RETRIES):
            try:
                results = self.model.generate_custom_voice(
                    text=chunk, 
                    speaker=SPEAKER, 
                    language="Korean", 
                    instruct=INSTRUCT,
                    **GEN_KWARGS
                )
                
                # 오디오 수집
                segment_audio_mx = None
                sr = 24000
                
                for res in results:
                    if segment_audio_mx is None:
                        segment_audio_mx = res.audio
                    else:
                        segment_audio_mx = mx.concatenate([segment_audio_mx, res.audio])
                
                if segment_audio_mx is not None:
                    # 성공적으로 생성됨
                    return segment_audio_mx, sr
                else:
                    print(f"   ⚠️ 시도 {attempt + 1}/{MAX_RETRIES}: 오디오 생성 실패")
                    
            except Exception as e:
                print(f"   ⚠️ 시도 {attempt + 1}/{MAX_RETRIES}: 에러 - {e}")
        
        # 모든 재시도 실패
        print(f"   ❌ 청크 {chunk_idx + 1} 생성 실패 (최대 재시도 초과)")
        return None, None

    def run(self, script_text, output_path):
        chunks = self.split_chunks(self.clean_text(script_text))
        print(f"📦 Total MLX Chunks: {len(chunks)}")
        print(f"🛡️ 외국어 차단 모드: 활성화 (Temperature: {GEN_KWARGS['temperature']})")
        
        combined_audio = AudioSegment.empty()
        srt_entries = []
        current_time_ms = 0
        
        start_time = time.time()
        
        for i, chunk in enumerate(chunks):
            # 입력 텍스트 검증
            if not self.validate_korean_only(chunk):
                print(f"⚠️ [MLX {i+1}/{len(chunks)}] 외국어 문자 감지, 정제 중...")
                chunk = re.sub(r'[^가-힣0-9\s.,!?\-"\'\'\"]+', '', chunk)
            
            print(f"⚡ [MLX {i+1}/{len(chunks)}] Generating: {chunk[:30]}...")
            
            # 재시도 로직으로 생성
            segment_audio_mx, sr = self.generate_chunk_with_retry(chunk, i)
            
            if segment_audio_mx is None:
                print(f"   ⏭️ 청크 {i+1} 스킵")
                continue

            
            # MLX array를 numpy로 변환 후 pydub로
            audio_np = np.array(segment_audio_mx)
            shared_buf = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
            sf.write(shared_buf.name, audio_np, sr)
            shared_buf.close()
            
            segment = AudioSegment.from_wav(shared_buf.name)
            os.unlink(shared_buf.name)
            
            # 속도 조절
            if SPEED_FACTOR != 1.0:
                segment = segment.speedup(playback_speed=SPEED_FACTOR, chunk_size=150, crossfade=25)
            
            duration_ms = len(segment)
            combined_audio += segment
            
            # SRT
            start_sec = current_time_ms / 1000.0
            end_sec = (current_time_ms + duration_ms) / 1000.0
            srt_entries.append(f"{i + 1}\n{self.format_srt_time(start_sec)} --> {self.format_srt_time(end_sec)}\n{chunk}\n\n")
            
            current_time_ms += duration_ms
            
            # 휴식 추가
            if i < len(chunks) - 1:
                pause_ms = 500 if any(chunk.endswith(p) for p in ['.', '?', '!']) else 200
                combined_audio += AudioSegment.silent(duration=pause_ms)
                current_time_ms += pause_ms

        # 저장
        combined_audio.export(output_path, format="mp3", bitrate="192k")
        srt_path = output_path.replace(".mp3", ".srt")
        with open(srt_path, "w", encoding="utf-8-sig") as f:
            f.writelines(srt_entries)
            
        elapsed = time.time() - start_time
        print(f"🏆 MLX 완료: {os.path.basename(output_path)} ({elapsed:.1f}s)")

if __name__ == "__main__":
    target_file = sys.argv[1] if len(sys.argv) > 1 else os.path.join(PROJ_ROOT, "대본.txt")
    if os.path.exists(target_file):
        with open(target_file, "r", encoding="utf-8") as f:
            script_text = f.read().strip()
        if script_text:
            timestamp = datetime.datetime.now().strftime("%m%d_%H%M")
            base_filename = os.path.splitext(os.path.basename(target_file))[0]
            output_name = f"{base_filename}_Qwen_MLX_{timestamp}.mp3"
            output_path = os.path.join(DOWNLOADS_DIR, output_name)
            
            generator = QwenMLXGenerator()
            generator.run(script_text, output_path)
        else: print("❌ 빈 대본")
    else: print("❌ 파일 없음")

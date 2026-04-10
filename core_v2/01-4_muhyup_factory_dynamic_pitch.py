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

# [Qwen-TTS MLX 설정 - 고정 성우 모드]
MODEL_ID = "mlx-community/Qwen3-TTS-12Hz-1.7B-CustomVoice-8bit"

# 사용자 요청: 중후한 40-50대 남성 성우 (uncle_fu)
# 중국어 혼입 방지를 위해 인스트럭션을 더 강화합니다.
SPEAKER = "uncle_fu"

# 3단계 방어: 극단적 언어 제약 (중국어 배제 강조)
INSTRUCT = """당신은 서울 표준어를 사용하는 20년 경력의 한국인 성우입니다. 
중국어나 영어 억양을 절대 섞지 말고, KBS 뉴스 앵커처럼 정확하고 단호한 한국어 어조로만 낭독하세요. 
40대 중저음으로 비장하면서도 차분하게 읽으세요. 어떤 외국어도 섞지 마세요."""

SPEED_FACTOR = 1.2
NARRATION_PITCH = 0.2  # 해설: 중고음
DIALOGUE_PITCH = -0.1   # 대화: 중저음 (요청대로 내림)
PITCH_SHIFT = 0.2      # 기본값 (초기화용)

# 극단적 결정론 설정 (환각/중국어 혼입 및 톤 이탈 완전 차단)
GEN_KWARGS = {
    "temperature": 0.0,      # 완전 결정론적 생성
    "top_p": 1.0,            # 최고 확률 토큰만 선택
    "repetition_penalty": 1.6 # 반복 및 이상 발음 억제 강화
}

MAX_RETRIES = 3

class QwenStableVoiceGenerator:
    def __init__(self):
        print(f"🚀 MLX 모델 로딩 중: {MODEL_ID}")
        self.model = load(MODEL_ID)
        print(f"✅ 성우 설정 완료: {SPEAKER} (40대 남성 중음)")

    def clean_text(self, text):
        text = re.sub(r'\[(BGM|묘사|지문|설명|배경|음악|CHAPTER|챕터|SFX):?.*?\]', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\(.*?\)', '', text)
        return text.strip()

    def split_chunks(self, text, max_chars=45):
        """텍스트를 자연스러운 청크로 분할 (문장 부호 + 길이 기반)"""
        sentences = re.split(r'([.!?]\s*)', text)
        chunks = []
        current_chunk = ""
        
        for i in range(0, len(sentences), 2):
            sentence = sentences[i]
            punctuation = sentences[i+1] if i+1 < len(sentences) else ""
            full_sentence = sentence + punctuation
            
            if len(full_sentence) > max_chars:
                words = full_sentence.split()
                temp = ""
                for word in words:
                    if len(temp) + len(word) + 1 <= max_chars:
                        temp += word + " "
                    else:
                        if temp:
                            chunks.append(temp.strip())
                        temp = word + " "
                if temp:
                    chunks.append(temp.strip())
            else:
                if len(current_chunk) + len(full_sentence) <= max_chars:
                    current_chunk += full_sentence
                else:
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                    current_chunk = full_sentence
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return [c for c in chunks if c]

    def format_srt_time(self, seconds):
        td = datetime.datetime.fromtimestamp(seconds, datetime.UTC)
        return td.strftime('%H:%M:%S,%f')[:-3]

    def validate_korean_only(self, text):
        korean_pattern = re.compile(r'^[가-힣0-9\s.,!?\-"\'\'\"]+$')
        return korean_pattern.match(text) is not None
    
    def change_pitch(self, sound, octaves):
        """음높이 체인저: 샘플 레이터 변환을 통해 피치를 조절합니다."""
        new_sample_rate = int(sound.frame_rate * (2.0 ** octaves))
        low_pitch_sound = sound._spawn(sound.raw_data, overrides={'frame_rate': new_sample_rate})
        return low_pitch_sound.set_frame_rate(sound.frame_rate)
    
    def generate_chunk_with_retry(self, chunk, chunk_idx):
        for attempt in range(MAX_RETRIES):
            try:
                # 고정 성우(Built-in)는 voice 인자를 사용합니다.
                results = self.model.generate(
                    text=chunk, 
                    voice=SPEAKER, 
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
                    return segment_audio_mx, sr
                else:
                    print(f"   ⚠️ 시도 {attempt + 1}/{MAX_RETRIES}: 오디오 생성 실패")
                    
            except Exception as e:
                print(f"   ⚠️ 시도 {attempt + 1}/{MAX_RETRIES}: 에러 - {e}")
        
        return None, None

    def run(self, script_text, output_path):
        chunks = self.split_chunks(self.clean_text(script_text))
        print(f"📦 Total Stable Voice Chunks: {len(chunks)}")
        
        combined_audio = AudioSegment.empty()
        srt_entries = []
        current_time_ms = 0
        start_time = time.time()
        
        for i, chunk in enumerate(chunks):
            if not self.validate_korean_only(chunk):
                chunk = re.sub(r'[^가-힣0-9\s.,!?\-"\'\'\"]+', '', chunk)
            
            print(f"⚡ [Stable {i+1}/{len(chunks)}] Generating: {chunk[:30]}...")
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
            
            # [동적 피치 로직] 따옴표 혹은 대화형 종결어미/키워드 감지
            conversational_markers = ["?", "!", "아저씨", "실장님", "할아버지", "회장님", "대표님", "너 ", "나 ", "내가 ", "자네"]
            is_dialogue = any(q in chunk for q in ['"', "'", "“", "”"]) or \
                          any(m in chunk for m in conversational_markers)
            
            current_pitch = DIALOGUE_PITCH if is_dialogue else NARRATION_PITCH
            
            print(f"   🎭 {'[대화]' if is_dialogue else '[해설]'} -> Pitch: {current_pitch} | Chunk: {chunk[:20]}...")
            
            if current_pitch != 0.0:
                segment = self.change_pitch(segment, current_pitch)
            
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
                pause_ms = 400 if any(chunk.endswith(p) for p in ['.', '?', '!']) else 150
                combined_audio += AudioSegment.silent(duration=pause_ms)
                current_time_ms += pause_ms

        combined_audio.export(output_path, format="mp3", bitrate="192k")
        srt_path = output_path.replace(".mp3", ".srt")
        with open(srt_path, "w", encoding="utf-8-sig") as f:
            f.writelines(srt_entries)
            
        elapsed = time.time() - start_time
        print(f"🏆 Stable Voice 완료: {os.path.basename(output_path)} ({elapsed:.1f}s)")

if __name__ == "__main__":
    target_file = sys.argv[1] if len(sys.argv) > 1 else os.path.join(PROJ_ROOT, "대본.txt")
    if os.path.exists(target_file):
        with open(target_file, "r", encoding="utf-8") as f:
            script_text = f.read().strip()
        if script_text:
            timestamp = datetime.datetime.now().strftime("%m%d_%H%M")
            base_filename = os.path.splitext(os.path.basename(target_file))[0]
            output_name = f"{base_filename}_Stable_{SPEAKER}_{timestamp}.mp3"
            output_path = os.path.join(DOWNLOADS_DIR, output_name)
            
            generator = QwenStableVoiceGenerator()
            generator.run(script_text, output_path)
        else: print("❌ 빈 대본")
    else: print("❌ 파일 없음")

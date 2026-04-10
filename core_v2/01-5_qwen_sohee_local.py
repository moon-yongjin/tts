import os
import sys
import time
import re
import datetime
import numpy as np
import soundfile as sf
import tempfile
from pydub import AudioSegment
import mlx.core as mx
from mlx_audio.tts import load 

# ==========================================================
# [사용자 설정 구역] - 여기서 목소리 톤을 조절하세요
# ==========================================================

# 1. 목소리 기본 설정
SPEAKER = "sohee"

# 2. 톤 및 피치 조절
PITCH = -1.5     # 낮을수록 저음 (할머니 느낌: -1.0 ~ -2.0 권장)
SPEED = 1.1      # 1.0이 기본 속도 (약간 빠르게: 1.1 ~ 1.2 권장)

# 3. 문장 사이 쉬는 시간 (ms)
PAUSE_MS = 800   # 800ms = 0.8초

# 4. 연기 지시문 (AI에게 내리는 명령)
INSTRUCT = "70대 이상의 나이가 지긋한 할머니 목소리로 연기하세요. 인자하면서도 세월의 무게가 느껴지는 깊은 울림이 있는 어조로 느릿하게 낭독하세요."

# 5. 생성 파라미터
GEN_KWARGS = {
    "temperature": 0.0,
    "top_p": 1.0,
    "repetition_penalty": 1.5
}
# ==========================================================

# [1. 환경 및 경로 설정]
sys.stdout.reconfigure(encoding='utf-8')

ENGINE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJ_ROOT = os.path.dirname(ENGINE_DIR)
DOWNLOADS_DIR = os.path.join(os.path.expanduser("~"), "Downloads")
MODEL_ID = "mlx-community/Qwen3-TTS-12Hz-1.7B-CustomVoice-bf16"

class local_qwen_sohee_generator:
    def __init__(self):
        print(f"🚀 [LOCAL] Qwen-Sohee BF16 모델 로딩 중: {MODEL_ID}")
        self.model = load(MODEL_ID)
        print("✅ 모델 로딩 완료!")

    def clean_text(self, text):
        text = re.sub(r'\[(BGM|묘사|지문|설명|배경|음악|CHAPTER|챕터|SFX):?.*?\]', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\(.*?\)', '', text)
        text = text.replace('"', '').replace("'", "")
        # 사장님 요청: '2편'을 '이 편'으로 읽도록 치환
        text = text.replace("2편", "이 편").replace("2 편", "이 편")
        return text.strip()

    def split_chunks(self, text, max_chars=100):
        sentences = re.split(r'([.!?]\s*)', text)
        chunks = []
        current_chunk = ""
        for i in range(0, len(sentences), 2):
            sentence = sentences[i]
            punctuation = sentences[i+1] if i+1 < len(sentences) else ""
            full_sentence = sentence + punctuation
            if len(current_chunk) + len(full_sentence) <= max_chars:
                current_chunk += full_sentence
            else:
                if current_chunk: chunks.append(current_chunk.strip())
                current_chunk = full_sentence
        if current_chunk: chunks.append(current_chunk.strip())
        return [c for c in chunks if c]

    def format_srt_time(self, seconds):
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

    def shift_pitch(self, sound, semitones):
        """피치를 조절하는 함수"""
        if semitones == 0: return sound
        new_sample_rate = int(sound.frame_rate * (2.0 ** (semitones / 12.0)))
        return sound._spawn(sound.raw_data, overrides={'frame_rate': new_sample_rate}).set_frame_rate(sound.frame_rate)

    def run(self, script_path):
        if not os.path.exists(script_path):
            print(f"❌ 대본 파일을 찾을 수 없습니다: {script_path}")
            return

        with open(script_path, "r", encoding="utf-8") as f:
            full_text = f.read().strip()
        
        print(f"📄 대본 분석 완료 ({len(full_text)}자)")
        chunks = self.split_chunks(self.clean_text(full_text))
        print(f"📦 총 {len(chunks)}개 파트로 나누어 생성을 시작합니다.")

        timestamp = datetime.datetime.now().strftime("%m%d_%H%M")
        base_filename = f"Qwen_Sohee_S{SPEED}_P{PITCH}_" + timestamp
        
        combined_audio = AudioSegment.empty()
        srt_content = []
        current_time_ms = 0

        for i, chunk in enumerate(chunks):
            print(f"🎙️  [{i+1}/{len(chunks)}] 생성 중: {chunk[:30]}...")
            
            try:
                results = self.model.generate(
                    text=chunk, voice=SPEAKER, language="Korean", instruct=INSTRUCT, **GEN_KWARGS
                )
                
                segment_audio_mx = None
                for res in results:
                    if segment_audio_mx is None: segment_audio_mx = res.audio
                    else: segment_audio_mx = mx.concatenate([segment_audio_mx, res.audio])
                
                if segment_audio_mx is None: continue
                
                audio_np = np.array(segment_audio_mx)
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                    sf.write(tmp.name, audio_np, 24000)
                    audio_segment = AudioSegment.from_wav(tmp.name)
                os.unlink(tmp.name)

                # [고급 설정 적용: 피치 및 속도]
                if PITCH != 0:
                    audio_segment = self.shift_pitch(audio_segment, PITCH)
                
                # 피치 변경에 따른 속도 변화를 상쇄하고 사용자가 원하는 최종 속도를 맞춤
                pitch_speed_change = 2.0 ** (PITCH / 12.0)
                final_speedup = SPEED / pitch_speed_change
                if final_speedup != 1.0:
                    # pydub의 speedup은 1.0보다 큰 경우에 주로 쓰임
                    if final_speedup > 1.0:
                        audio_segment = audio_segment.speedup(playback_speed=final_speedup, chunk_size=150, crossfade=25)
                    else:
                        # 1.0보다 느린 경우 샘플링 레이트로 조절
                        new_rate = int(audio_segment.frame_rate / final_speedup)
                        audio_segment = audio_segment._spawn(audio_segment.raw_data, overrides={'frame_rate': new_rate}).set_frame_rate(audio_segment.frame_rate)

                # 쉼표(Pause) 추가
                pause = AudioSegment.silent(duration=PAUSE_MS)
                
                # SRT 정보 추가 (속도 조절된 후의 길이 기준)
                start_sec = current_time_ms / 1000.0
                duration_ms = len(audio_segment)
                end_sec = (current_time_ms + duration_ms) / 1000.0
                srt_content.append(f"{i+1}\n{self.format_srt_time(start_sec)} --> {self.format_srt_time(end_sec)}\n{chunk}\n")
                
                combined_audio += audio_segment + pause
                current_time_ms += duration_ms + PAUSE_MS
            except Exception as e:
                print(f"   ❌ 파트 {i+1} 생성 중 오류 발생: {e}")

        final_mp3_path = os.path.join(DOWNLOADS_DIR, base_filename + ".mp3")
        final_srt_path = os.path.join(DOWNLOADS_DIR, base_filename + ".srt")
        
        combined_audio.export(final_mp3_path, format="mp3", bitrate="192k")
        with open(final_srt_path, "w", encoding="utf-8-sig") as f:
            f.write("\n".join(srt_content))
            
        print(f"\n✨ 설정된 속도({SPEED}배)와 피치({PITCH})로 생성 완료!")
        print(f"📂 결과 MP3: {final_mp3_path}")
        print(f"📂 결과 SRT: {final_srt_path}")

if __name__ == "__main__":
    script = sys.argv[1] if len(sys.argv) > 1 else os.path.join(PROJ_ROOT, "대본.txt")
    gen = local_qwen_sohee_generator()
    gen.run(script)

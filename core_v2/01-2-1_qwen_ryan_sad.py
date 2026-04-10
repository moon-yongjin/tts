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

# [필요 환경 설정]
sys.stdout.reconfigure(encoding='utf-8')
DOWNLOADS_DIR = os.path.join(os.path.expanduser("~"), "Downloads")
MODEL_ID = "mlx-community/Qwen3-TTS-12Hz-1.7B-CustomVoice-bf16"
SPEAKER = "ryan"

# ==========================================================
# [사용자 설정 - 라이언피치 슬픔 v1-2-1]
# ==========================================================

# 1. 내레이션 (따옴표 밖) - 인자한 할아버지
NARRATION_PITCH = 0.0          # 기본 피치
NARRATION_SPEED = 1.1          # 1.1배속
NARRATION_INSTRUCT = "정확한 서울 표준어를 사용하는 70대 할아버지 성우입니다. 중국어나 외국어 억양을 절대 섞지 말고, 세월의 무게가 느껴지는 깊은 울림이 있는 순수 한국어 어조로 차분하게 낭독하세요."

# 2. 대사 (따옴표 안) - 날카로운 아들/청년
DIALOGUE_PITCH = 1.5           # 고음 변조
DIALOGUE_SPEED = 1.0           # 정속
DIALOGUE_INSTRUCT = "서울 표준어를 사용하는 20대 남성 성우입니다. 중국어 억양을 절대 배제하고, 짜증이나 서운함이 섞인 단호하고 날카로운 한국어 어조를 유지하세요."

# 3. 공통 설정
PAUSE_MS = 800       # 문장/세그먼트 사이 간격
MAX_CHUNK_CHARS = 80 # 생성 안정성을 위한 글자수 제한
# ==========================================================

class production_ryan_generator:
    def __init__(self):
        print(f"🚀 [v1-2-1] Qwen-Ryan (슬픔 테마) 모델 로딩 중...")
        self.model = load(MODEL_ID)
        print("✅ 로딩 완료! 생성을 시작합니다.")

    def split_into_chunks(self, text, max_len=MAX_CHUNK_CHARS):
        sentences = re.split(r'([.!?]\s*)', text)
        chunks = []
        current = ""
        for i in range(0, len(sentences), 2):
            s = sentences[i]
            p = sentences[i+1] if i+1 < len(sentences) else ""
            full = (s + p).strip()
            if not full: continue
            if len(current) + len(full) <= max_len:
                current += (" " + full if current else full)
            else:
                if current: chunks.append(current)
                current = full
        if current: chunks.append(current)
        return chunks

    def parse_script(self, text):
        segments = []
        raw_parts = re.split(r'("(?:[^"]*)")', text)
        for part in raw_parts:
            part = part.strip().replace("\n", " ")
            if not part: continue
            is_dialogue = part.startswith('"') and part.endswith('"')
            content = part[1:-1].strip() if is_dialogue else part
            chunks = self.split_into_chunks(content)
            settings = {
                "pitch": DIALOGUE_PITCH if is_dialogue else NARRATION_PITCH,
                "speed": DIALOGUE_SPEED if is_dialogue else NARRATION_SPEED,
                "instruct": DIALOGUE_INSTRUCT if is_dialogue else NARRATION_INSTRUCT,
                "type": "대사" if is_dialogue else "나레이션"
            }
            for chunk in chunks:
                segments.append({**settings, "text": chunk})
        return segments

    def shift_pitch(self, sound, semitones):
        if semitones == 0: return sound
        new_sample_rate = int(sound.frame_rate * (2.0 ** (semitones / 12.0)))
        return sound._spawn(sound.raw_data, overrides={'frame_rate': new_sample_rate}).set_frame_rate(sound.frame_rate)

    def format_srt_time(self, seconds):
        h = int(seconds // 3600); m = int((seconds % 3600) // 60)
        s = int(seconds % 60); ms = int((seconds % 1) * 1000)
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

    def run(self, script_path):
        if not os.path.exists(script_path):
            print(f"❌ 대본 없음: {script_path}")
            return
        with open(script_path, "r", encoding="utf-8") as f:
            full_text = f.read().strip()
        segments = self.parse_script(full_text)
        print(f"📦 총 {len(segments)}개의 파트로 분석 완료")
        timestamp = datetime.datetime.now().strftime("%m%d_%H%M")
        base_name = f"라이언피치_슬픔_{timestamp}"
        combined_audio = AudioSegment.empty()
        srt_lines = []
        current_ms = 0
        for i, seg in enumerate(segments):
            print(f"🎙️  [{i+1}/{len(segments)}] {seg['type']}: {seg['text'][:30]}...")
            try:
                results = self.model.generate(
                    text=seg['text'], voice=SPEAKER, language="Korean", instruct=seg['instruct'],
                    temperature=0.0, top_p=1.0, repetition_penalty=1.5
                )
                seg_mx = None
                for res in results:
                    if seg_mx is None: seg_mx = res.audio
                    else: seg_mx = mx.concatenate([seg_mx, res.audio])
                if seg_mx is None: continue
                audio_np = np.array(seg_mx)
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                    sf.write(tmp.name, audio_np, 24000)
                    audio_segment = AudioSegment.from_wav(tmp.name)
                os.unlink(tmp.name)
                if seg['pitch'] != 0:
                    audio_segment = self.shift_pitch(audio_segment, seg['pitch'])
                p_speed = 2.0 ** (seg['pitch'] / 12.0)
                final_s = seg['speed'] / p_speed
                if final_s > 1.0:
                    audio_segment = audio_segment.speedup(playback_speed=final_s, chunk_size=150, crossfade=25)
                elif final_s < 1.0:
                    new_rate = int(audio_segment.frame_rate / final_s)
                    audio_segment = audio_segment._spawn(audio_segment.raw_data, overrides={'frame_rate': new_rate}).set_frame_rate(audio_segment.frame_rate)
                start_s = current_ms / 1000.0
                dur_ms = len(audio_segment)
                end_s = (current_ms + dur_ms) / 1000.0
                srt_lines.append(f"{len(srt_lines)+1}\n{self.format_srt_time(start_s)} --> {self.format_srt_time(end_s)}\n{seg['text']}\n")
                combined_audio += audio_segment + AudioSegment.silent(duration=PAUSE_MS)
                current_ms += dur_ms + PAUSE_MS
            except Exception as e:
                print(f"   ❌ 오류: {e}")
        mp3_path = os.path.join(DOWNLOADS_DIR, base_name + ".mp3")
        srt_path = os.path.join(DOWNLOADS_DIR, base_name + ".srt")
        combined_audio.export(mp3_path, format="mp3", bitrate="192k")
        with open(srt_path, "w", encoding="utf-8-sig") as f:
            f.write("\n".join(srt_lines))
        print(f"\n✨ 생성 완료!\n📂 MP3: {mp3_path}\n📂 SRT: {srt_path}")

if __name__ == "__main__":
    script = sys.argv[1] if len(sys.argv) > 1 else "/Users/a12/projects/tts/대본.txt"
    gen = production_ryan_generator()
    gen.run(script)

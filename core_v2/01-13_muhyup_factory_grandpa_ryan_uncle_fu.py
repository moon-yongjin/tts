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

def format_srt_time(ms):
    s, ms = divmod(ms, 1000)
    m, s = divmod(s, 60)
    h, m = divmod(m, 60)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

# [1. 환경 및 경로 설정]
sys.stdout.reconfigure(encoding='utf-8')

ENGINE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJ_ROOT = os.path.dirname(ENGINE_DIR)
DOWNLOADS_DIR = os.path.join(os.path.expanduser("~"), "Downloads")

# [Qwen-TTS MLX 설정 - BF16 HIGH PRECISION 모델]
MODEL_ID = "mlx-community/Qwen3-TTS-12Hz-1.7B-CustomVoice-bf16"

# 성우 보이스 설정
NARRATOR_VOICE = "ryan"
DIALOGUE_VOICE = "uncle_fu"

# 페르소나별 명령문(Instruct)
NARRATOR_INSTRUCT = """70대 이상의 나이가 지긋한 할아버지 목소리로 연기하세요. 
인자하면서도 세월의 무게가 느껴지는 깊은 울림이 있는 어조로 느릿하게 낭독하세요."""

DIALOGUE_INSTRUCT = """당신은 서울 표준어를 사용하는 성우입니다. 
정확하고 단호한 한국어 어조로만 낭독하세요."""

# 사용자 지정 변조 값
SPEED_FACTOR = 1.2
NARRATOR_PITCH = -1.5 # 할아버지 느낌을 위한 낮은 피치
DIALOGUE_PITCH = 0.5  # 대사는 좀 더 밝게

GEN_KWARGS = {
    "temperature": 0.0,
    "top_p": 1.0,
    "repetition_penalty": 1.5
}

MAX_RETRIES = 2

class QwenGrandpaMixedGenerator:
    def __init__(self):
        print(f"🚀 BF16 모델 로딩 중: {MODEL_ID}")
        self.model = load(MODEL_ID)
        print("✅ 모델 로딩 완료!")

    def clean_text(self, text):
        text = re.sub(r'\[(BGM|묘사|지문|설명|배경|음악|CHAPTER|챕터|SFX):?.*?\]', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\(.*?\)', '', text)
        return text.strip()

    def parse_segments(self, text):
        raw_parts = re.split(r'(".*?")', text, flags=re.DOTALL)
        segments = []
        for part in raw_parts:
            part = part.strip()
            if not part: continue
            if part.startswith('"') and part.endswith('"'):
                content = part[1:-1].strip()
                if content: segments.append({"type": "dialogue", "text": content})
            else:
                segments.append({"type": "narration", "text": part})
        return segments

    def split_chunks(self, text, max_chars=60):
        """사용자 쉼표 존중: 병합 로직 제거"""
        raw_chunks = re.split(r'([.!?,\n]\s*)', text)
        chunks = []
        for i in range(0, len(raw_chunks), 2):
            part = raw_chunks[i]
            punc = raw_chunks[i+1] if i+1 < len(raw_chunks) else ""
            full = (part + punc).strip()
            if not full: continue
            
            if len(full) > max_chars:
                words = full.split()
                temp = ""
                for w in words:
                    if len(temp) + len(w) + 1 <= max_chars: temp += w + " "
                    else:
                        if temp: chunks.append(temp.strip())
                        temp = w + " "
                if temp: chunks.append(temp.strip())
            else:
                chunks.append(full)
        return chunks

    def shift_pitch(self, sound, semitones):
        if semitones == 0: return sound
        new_sample_rate = int(sound.frame_rate * (2.0 ** (semitones / 12.0)))
        return sound._spawn(sound.raw_data, overrides={'frame_rate': new_sample_rate}).set_frame_rate(sound.frame_rate)

    def run(self, script_text, base_filename):
        timestamp = datetime.datetime.now().strftime("%m%d_%H%M")
        output_name = f"{base_filename}_GrandpaRyan+UncleFu_{timestamp}.mp3"
        output_path = os.path.join(DOWNLOADS_DIR, output_name)
        
        segments = self.parse_segments(self.clean_text(script_text))
        print(f"\n🎙️  할아버지 나레이션({NARRATOR_VOICE}) + 대사({DIALOGUE_VOICE}) 생성 시작")
        
        combined_audio = AudioSegment.empty()
        all_srt_entries = []
        current_time_ms = 0
        srt_idx = 1
        
        for idx, seg in enumerate(segments):
            is_diag = (seg["type"] == "dialogue")
            speaker = DIALOGUE_VOICE if is_diag else NARRATOR_VOICE
            instruct = DIALOGUE_INSTRUCT if is_diag else NARRATOR_INSTRUCT
            pitch = DIALOGUE_PITCH if is_diag else NARRATOR_PITCH
            
            print(f"   [{idx+1}/{len(segments)}] {seg['type'].upper()} ({speaker}): {seg['text'][:20]}...")
            
            chunks = self.split_chunks(seg["text"])
            for chunk in chunks:
                segment_audio_mx = None
                for attempt in range(MAX_RETRIES):
                    try:
                        results = self.model.generate(
                            text=chunk, voice=speaker, language="Korean",
                            instruct=instruct, **GEN_KWARGS
                        )
                        segment_audio_mx = None
                        for res in results:
                            if segment_audio_mx is None: segment_audio_mx = res.audio
                            else: segment_audio_mx = mx.concatenate([segment_audio_mx, res.audio])
                        if segment_audio_mx is not None: break
                    except Exception as e: print(f"   ⚠️ attempt {attempt + 1}: {e}")
                
                if segment_audio_mx is None: continue
                    
                audio_np = np.array(segment_audio_mx)
                shared_buf = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
                sf.write(shared_buf.name, audio_np, 24000)
                shared_buf.close()
                segment = AudioSegment.from_wav(shared_buf.name)
                os.unlink(shared_buf.name)
                
                if pitch != 0:
                    segment = self.shift_pitch(segment, pitch)
                
                pitch_speed_change = 2.0 ** (pitch / 12.0)
                target_speedup = SPEED_FACTOR / pitch_speed_change
                if target_speedup > 1.0:
                    segment = segment.speedup(playback_speed=target_speedup, chunk_size=150, crossfade=25)
                elif target_speedup < 1.0:
                    new_sample_rate = int(segment.frame_rate / target_speedup)
                    segment = segment._spawn(segment.raw_data, overrides={'frame_rate': new_sample_rate}).set_frame_rate(segment.frame_rate)
                
                # SRT 정보 추가
                duration_ms = len(segment)
                start_time = format_srt_time(current_time_ms)
                end_time = format_srt_time(current_time_ms + duration_ms)
                all_srt_entries.append(f"{srt_idx}\n{start_time} --> {end_time}\n{chunk}\n\n")
                
                combined_audio += segment
                current_time_ms += duration_ms
                srt_idx += 1
                
            pause_ms = 400 if is_diag else 200
            combined_audio += AudioSegment.silent(duration=pause_ms)
            current_time_ms += pause_ms

        combined_audio.export(output_path, format="mp3", bitrate="192k")
        srt_path = output_path.replace(".mp3", ".srt")
        with open(srt_path, "w", encoding="utf-8-sig") as f:
            f.writelines(all_srt_entries)
            
        print(f"✅ 완료: {output_name}")
        print(f"✅ 자막 파일 생성: {os.path.basename(srt_path)}")

if __name__ == "__main__":
    target_file = sys.argv[1] if len(sys.argv) > 1 else os.path.join(PROJ_ROOT, "대본.txt")
    if os.path.exists(target_file):
        with open(target_file, "r", encoding="utf-8") as f: script_text = f.read().strip()
        generator = QwenGrandpaMixedGenerator()
        generator.run(script_text, os.path.splitext(os.path.basename(target_file))[0])

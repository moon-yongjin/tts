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

# [Qwen-TTS MLX 설정 - BF16 HIGH PRECISION 모델]
MODEL_ID = "mlx-community/Qwen3-TTS-12Hz-1.7B-CustomVoice-bf16"

# 할아버지 페르소나 설정
INSTRUCT = """70대 이상의 나이가 지긋한 할아버지 목소리로 연기하세요. 
인자하면서도 세월의 무게가 느껴지는 깊은 울림이 있는 어조로 느릿하게 낭독하세요. 
모든 문장을 노인의 말투와 호흡으로 자연스럽게 표현하세요."""

# 속도는 느릿하게, 피치는 낮게 조정
SPEED_FACTOR = 0.95
PITCH_SHIFT = -1.5

GEN_KWARGS = {
    "temperature": 0.0,
    "top_p": 1.0,
    "repetition_penalty": 1.5
}

MAX_RETRIES = 2

class QwenPersonaGenerator:
    def __init__(self):
        print(f"🚀 BF16 모델 로딩 중: {MODEL_ID}")
        self.model = load(MODEL_ID)
        print("✅ 모델 로딩 완료!")

    def clean_text(self, text):
        text = re.sub(r'\[(BGM|묘사|지문|설명|배경|음악|CHAPTER|챕터|SFX):?.*?\]', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\(.*?\)', '', text)
        return text.strip()

    def split_chunks(self, text, max_chars=45):
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
                        if temp: chunks.append(temp.strip())
                        temp = word + " "
                if temp: chunks.append(temp.strip())
            else:
                if len(current_chunk) + len(full_sentence) <= max_chars:
                    current_chunk += full_sentence
                else:
                    if current_chunk: chunks.append(current_chunk.strip())
                    current_chunk = full_sentence
        if current_chunk: chunks.append(current_chunk.strip())
        return [c for c in chunks if c]

    def shift_pitch(self, sound, semitones):
        if semitones == 0: return sound
        new_sample_rate = int(sound.frame_rate * (2.0 ** (semitones / 12.0)))
        return sound._spawn(sound.raw_data, overrides={'frame_rate': new_sample_rate}).set_frame_rate(sound.frame_rate)

    def run(self, speaker, script_text, base_filename):
        timestamp = datetime.datetime.now().strftime("%m%d_%H%M")
        output_name = f"{base_filename}_{speaker}_Grandpa_{timestamp}.mp3"
        output_path = os.path.join(DOWNLOADS_DIR, output_name)
        
        chunks = self.split_chunks(self.clean_text(script_text))
        print(f"\n🎙️  페르소나 생성 시작: {speaker} (Grandfather Mode)")
        
        combined_audio = AudioSegment.empty()
        
        for i, chunk in enumerate(chunks):
            print(f"   ⚡ [{i+1}/{len(chunks)}] {chunk[:30]}...")
            segment_audio_mx = None
            for attempt in range(MAX_RETRIES):
                try:
                    results = self.model.generate(
                        text=chunk, voice=speaker, language="Korean",
                        instruct=INSTRUCT, **GEN_KWARGS
                    )
                    segment_audio_mx = None
                    for res in results:
                        if segment_audio_mx is None: segment_audio_mx = res.audio
                        else: segment_audio_mx = mx.concatenate([segment_audio_mx, res.audio])
                    if segment_audio_mx is not None: break
                except Exception as e: print(f"   ⚠️ 시도 {attempt + 1}: {e}")
            
            if segment_audio_mx is None: continue
                
            audio_np = np.array(segment_audio_mx)
            shared_buf = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
            sf.write(shared_buf.name, audio_np, 24000)
            shared_buf.close()
            segment = AudioSegment.from_wav(shared_buf.name)
            os.unlink(shared_buf.name)
            
            if PITCH_SHIFT != 0:
                segment = self.shift_pitch(segment, PITCH_SHIFT)
            
            pitch_speed_change = 2.0 ** (PITCH_SHIFT / 12.0)
            target_speedup = SPEED_FACTOR / pitch_speed_change
            if target_speedup > 1.0:
                segment = segment.speedup(playback_speed=target_speedup, chunk_size=150, crossfade=25)
            elif target_speedup < 1.0:
                new_sample_rate = int(segment.frame_rate / target_speedup)
                segment = segment._spawn(segment.raw_data, overrides={'frame_rate': new_sample_rate}).set_frame_rate(segment.frame_rate)
            
            combined_audio += segment
            pause_ms = 600 if any(chunk.endswith(p) for p in ['.', '?', '!']) else 200
            combined_audio += AudioSegment.silent(duration=pause_ms)

        combined_audio.export(output_path, format="mp3", bitrate="192k")
        print(f"✅ 완료: {output_name}")

if __name__ == "__main__":
    target_file = sys.argv[1] if len(sys.argv) > 1 else os.path.join(PROJ_ROOT, "대본.txt")
    if os.path.exists(target_file):
        with open(target_file, "r", encoding="utf-8") as f: script_text = f.read().strip()
        generator = QwenPersonaGenerator()
        generator.run("ryan", script_text, os.path.splitext(os.path.basename(target_file))[0])

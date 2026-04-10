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

# 성우 설정
NARRATOR_VOICE = "ryan"
DIALOGUE_VOICE = "sohee"

# 3단계 방어: 극단적 언어 제약
INSTRUCT = """당신은 서울 표준어를 사용하는 성우입니다. 
중국어나 영어 억양을 절대 섞지 말고, 정확하고 단호한 한국어 어조로만 낭독하세요. 
어떤 외국어도 섞지 마세요."""

# 사용자 지정 변조 값
SPEED_FACTOR = 1.2
PITCH_SHIFT = 0.5

GEN_KWARGS = {
    "temperature": 0.0,
    "top_p": 1.0,
    "repetition_penalty": 1.5
}

MAX_RETRIES = 2

class QwenMultiSpeakerGenerator:
    def __init__(self):
        print(f"🚀 BF16 모델 로딩 중: {MODEL_ID}")
        self.model = load(MODEL_ID)
        print("✅ 모델 로딩 완료!")

    def clean_text(self, text):
        # [SFX: ...] 등 특수 태그 및 (괄호 지문) 제거
        text = re.sub(r'\[(BGM|묘사|지문|설명|배경|음악|CHAPTER|챕터|SFX):?.*?\]', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\(.*?\)', '', text)
        return text.strip()

    def parse_segments(self, text):
        """따옴표 기준 세그먼트 분리 (따옴표 포함 루프)"""
        # 정규표현식으로 따옴표 앞뒤 분리
        raw_parts = re.split(r'(".*?")', text, flags=re.DOTALL)
        segments = []
        for part in raw_parts:
            part = part.strip()
            if not part: continue
            
            # 따옴표로 시작하고 끝나면 대화(Dialogue)
            if part.startswith('"') and part.endswith('"'):
                content = part[1:-1].strip() # 따옴표 제거
                if content:
                    segments.append({"type": "dialogue", "text": content})
            else:
                # 일반 텍스트(Narration)
                segments.append({"type": "narration", "text": part})
        return segments

    def split_chunks(self, text, max_chars=45):
        """긴 문장을 안정적인 조각으로 분리 (01-3 방식)"""
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
        return chunks

    def shift_pitch(self, sound, semitones):
        if semitones == 0: return sound
        new_sample_rate = int(sound.frame_rate * (2.0 ** (semitones / 12.0)))
        return sound._spawn(sound.raw_data, overrides={'frame_rate': new_sample_rate}).set_frame_rate(sound.frame_rate)

    def run(self, script_text, base_filename):
        timestamp = datetime.datetime.now().strftime("%m%d_%H%M")
        output_name = f"{base_filename}_Mixed_R+S_{timestamp}.mp3"
        output_path = os.path.join(DOWNLOADS_DIR, output_name)
        
        # 1. 텍스트 세그먼트 분석
        clean_script = self.clean_text(script_text)
        segments = self.parse_segments(clean_script)
        
        print(f"\n🎙️  혼합 성우 생성 시작 (나레이션: {NARRATOR_VOICE} / 대사: {DIALOGUE_VOICE})")
        
        combined_audio = AudioSegment.empty()
        
        for idx, seg in enumerate(segments):
            speaker = DIALOGUE_VOICE if seg["type"] == "dialogue" else NARRATOR_VOICE
            print(f"   [{idx+1}/{len(segments)}] {seg['type'].upper()} ({speaker}): {seg['text'][:20]}...")
            
            # 긴 세그먼트는 청크로 나눔
            chunks = self.split_chunks(seg["text"])
            
            for chunk in chunks:
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
                    except Exception as e: print(f"   ⚠️ attempt {attempt + 1}: {e}")
                
                if segment_audio_mx is None: continue
                    
                audio_np = np.array(segment_audio_mx)
                shared_buf = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
                sf.write(shared_buf.name, audio_np, 24000)
                shared_buf.close()
                segment = AudioSegment.from_wav(shared_buf.name)
                os.unlink(shared_buf.name)
                
                # 변조 적용
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
                
            # 세그먼트 간 호흡
            pause_ms = 400 if seg["type"] == "dialogue" else 200
            combined_audio += AudioSegment.silent(duration=pause_ms)

        combined_audio.export(output_path, format="mp3", bitrate="192k")
        print(f"✅ 완료: {output_name}")

if __name__ == "__main__":
    target_file = sys.argv[1] if len(sys.argv) > 1 else os.path.join(PROJ_ROOT, "대본.txt")
    if os.path.exists(target_file):
        with open(target_file, "r", encoding="utf-8") as f: script_text = f.read().strip()
        generator = QwenMultiSpeakerGenerator()
        generator.run(script_text, os.path.splitext(os.path.basename(target_file))[0])

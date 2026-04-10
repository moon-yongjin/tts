import os
import sys
import time
import re
import datetime
import tempfile
import json
import io
import subprocess
import numpy as np
import soundfile as sf
from pydub import AudioSegment
import mlx.core as mx
from mlx_audio.tts import load
from google import genai
from google.genai import types

# [1. 환경 및 경로 설정]
sys.stdout.reconfigure(encoding='utf-8')
ENGINE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJ_ROOT = os.path.dirname(ENGINE_DIR)
DOWNLOADS_DIR = os.path.join(os.path.expanduser("~"), "Downloads")
CONFIG_PATH = os.path.join(PROJ_ROOT, "config.json")

# 1-2. Config 로드
with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    config = json.load(f)
    GEMINI_API_KEY = config.get("Gemini_API_KEY")

# [2. 모델 설정]
# Qwen Ryan (해설/할아버지용)
QWEN_MODEL_ID = "mlx-community/Qwen3-TTS-12Hz-1.7B-CustomVoice-bf16"
QWEN_VOICE = "ryan"
QWEN_INSTRUCT = """70대 이상의 나이가 지긋한 할아버지 목소리로 연기하세요. 
인자하면서도 세월의 무게가 느껴지는 깊은 울림이 있는 어조로 느릿하게 낭독하세요."""
QWEN_SPEED = 0.95
QWEN_PITCH = -1.5 # 할아버지 느낌을 위한 낮은 피치

# Gemini (대사용)
GEMINI_MODEL_ID = "gemini-2.5-flash-preview-tts"
GEMINI_INSTRUCT = """당신은 70대 할머니입니다. 슬픈 감정이 듬뿍 담긴 차분하고 애절한 목소리로 대사를 연기하세요. 
모든 출력은 한국어로만 생성하십시오."""

def format_srt_time(ms):
    s, ms = divmod(ms, 1000)
    m, s = divmod(s, 60)
    h, m = divmod(m, 60)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

class QwenRyanGeminiHybridGenerator:
    def __init__(self):
        print(f"🚀 Qwen 모델 로딩 중: {QWEN_MODEL_ID}")
        self.qwen_model = load(QWEN_MODEL_ID)
        print("✅ Qwen 로드 완료!")
        
        print(f"🚀 Gemini 클라이언트 초기화 중...")
        self.gemini_client = genai.Client(api_key=GEMINI_API_KEY, http_options={'api_version': 'v1alpha'})
        print("✅ Gemini 초기화 완료!")

    def clean_text(self, text):
        text = re.sub(r'\[(BGM|묘사|지문|설명|배경|음악|CHAPTER|챕터|SFX):?.*?\]', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\(.*?\)', '', text)
        return text.strip()

    def parse_hybrid_segments(self, text):
        parts = re.split(r'([\"|\'].*?[\"|\'])', text, flags=re.DOTALL)
        segments = []
        for p in parts:
            p = p.strip()
            if not p: continue
            if (p.startswith('"') and p.endswith('"')) or (p.startswith("'") and p.endswith("'")):
                segments.append({"type": "dialogue", "text": p[1:-1].strip()})
            else:
                segments.append({"type": "narration", "text": p})
        return segments

    def generate_qwen(self, text, output_path):
        """Qwen Ryan 할아버지 생성"""
        results = self.qwen_model.generate(
            text=text, voice=QWEN_VOICE, language="Korean",
            instruct=QWEN_INSTRUCT, max_tokens=1024, top_p=1.0, repetition_penalty=1.5
        )
        audio_mx = None
        for res in results:
            if audio_mx is None: audio_mx = res.audio
            else: audio_mx = mx.concatenate([audio_mx, res.audio])
            
        if audio_mx is not None:
            audio_np = np.array(audio_mx)
            sf.write(output_path, audio_np, 24000)
            return True
        return False

    def generate_gemini(self, text, output_path):
        """제미나이 2.5 대사 생성"""
        try:
            prompt = f"{GEMINI_INSTRUCT}\n\n[대사]\n{text}"
            response = self.gemini_client.models.generate_content(
                model=GEMINI_MODEL_ID,
                contents=prompt,
                config=types.GenerateContentConfig(response_modalities=["AUDIO"])
            )
            raw_data = bytearray()
            for part in response.candidates[0].content.parts:
                if part.inline_data:
                    raw_data.extend(part.inline_data.data)
            if raw_data:
                segment = AudioSegment.from_raw(io.BytesIO(raw_data), sample_width=2, frame_rate=24000, channels=1)
                segment.export(output_path, format="wav")
                return True
        except Exception as e:
            print(f"❌ Gemini 오류: {e}")
        return False

    def shift_pitch(self, sound, semitones):
        if semitones == 0: return sound
        new_sample_rate = int(sound.frame_rate * (2.0 ** (semitones / 12.0)))
        return sound._spawn(sound.raw_data, overrides={'frame_rate': new_sample_rate}).set_frame_rate(sound.frame_rate)

    def run(self, raw_text, base_name="QwenRyan_Gemini_Hybrid"):
        timestamp = datetime.datetime.now().strftime("%m%d_%H%M")
        output_name = f"{base_name}_{timestamp}.mp3"
        final_path = os.path.join(DOWNLOADS_DIR, output_name)
        
        cleaned = self.clean_text(raw_text)
        segments = self.parse_hybrid_segments(cleaned)
        
        print(f"📋 하이브리드(퀜 리안+제미나이) 생성 시작")
        combined_audio = AudioSegment.empty()
        srt_entries = []
        current_ms = 0
        idx = 1

        with tempfile.TemporaryDirectory() as tmp_dir:
            for s_idx, seg in enumerate(segments):
                text = seg["text"]
                print(f"   [{s_idx+1}/{len(segments)}] {seg['type'].upper()}: {text[:30]}...")
                tmp_wav = os.path.join(tmp_dir, f"seg_{s_idx}.wav")
                
                if seg["type"] == "narration":
                    success = self.generate_qwen(text, tmp_wav)
                else:
                    success = self.generate_gemini(text, tmp_wav)
                
                if success and os.path.exists(tmp_wav):
                    segment = AudioSegment.from_file(tmp_wav)
                    
                    if seg["type"] == "narration":
                        # 피치 및 속도 보정
                        segment = self.shift_pitch(segment, QWEN_PITCH)
                        pitch_speed_change = 2.0 ** (QWEN_PITCH / 12.0)
                        target_speedup = QWEN_SPEED / pitch_speed_change
                        if target_speedup < 1.0:
                             new_sample_rate = int(segment.frame_rate / target_speedup)
                             segment = segment._spawn(segment.raw_data, overrides={'frame_rate': new_sample_rate}).set_frame_rate(segment.frame_rate)
                    
                    duration = len(segment)
                    start = format_srt_time(current_ms)
                    end = format_srt_time(current_ms + duration)
                    display_text = f"\"{text}\"" if seg["type"] == "dialogue" else text
                    srt_entries.append(f"{idx}\n{start} --> {end}\n{display_text}\n\n")
                    
                    combined_audio += segment
                    current_ms += duration
                    idx += 1
                    combined_audio += AudioSegment.silent(duration=500)
                    current_ms += 500

        print("🔧 최종 오디오 볼륨 최적화 중...")
        combined_audio = combined_audio.normalize(headroom=1.0)
        combined_audio.export(final_path, format="mp3", bitrate="192k")
        srt_path = final_path.replace(".mp3", ".srt")
        with open(srt_path, "w", encoding="utf-8-sig") as f:
            f.writelines(srt_entries)
            
        print(f"✨ 완료: {output_name}")
        
        print(f"🎵 생성된 오디오를 재생합니다...")
        try:
            subprocess.run(["open", final_path])
        except:
            pass

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else os.path.join(PROJ_ROOT, "대본.txt")
    if os.path.exists(target):
        with open(target, "r", encoding="utf-8") as f:
            text = f.read().strip()
        generator = QwenRyanGeminiHybridGenerator()
        generator.run(text, os.path.splitext(os.path.basename(target))[0])

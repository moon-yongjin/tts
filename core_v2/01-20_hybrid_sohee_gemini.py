import os
import sys
import time
import re
import datetime
import tempfile
import json
import io
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
# Qwen (해설용)
QWEN_MODEL_ID = "mlx-community/Qwen3-TTS-12Hz-1.7B-CustomVoice-bf16"
QWEN_VOICE = "sohee"
QWEN_INSTRUCT = "당신은 70대 할머니 성우입니다. 정 많고 따뜻하게 이야기를 들려주듯 낭독하세요."
QWEN_SPEED = 0.9
QWEN_PITCH = 0.0 # 보통 톤 요청

# Gemini (대사용)
GEMINI_MODEL_ID = "gemini-2.5-flash-preview-tts"
# 대사는 좀 더 감정적으로 지시
GEMINI_INSTRUCT = "당신은 70대 할머니입니다. 따옴표 안의 대사를 상황에 맞는 감정을 듬뿍 담아 실제로 말하듯 연기하세요. 인자하면서도 때로는 단호한 할머니의 목소리입니다."

def format_srt_time(ms):
    s, ms = divmod(ms, 1000)
    m, s = divmod(s, 60)
    h, m = divmod(m, 60)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

class HybridTTSGenerator:
    def __init__(self):
        print(f"🚀 Qwen 모델 로딩 중: {QWEN_MODEL_ID}")
        self.qwen_model = load(QWEN_MODEL_ID)
        print("✅ Qwen 로드 완료!")
        
        print(f"🚀 Gemini 클라이언트 초기화 중...")
        self.gemini_client = genai.Client(api_key=GEMINI_API_KEY, http_options={'api_version': 'v1alpha'})
        print("✅ Gemini 초기화 완료!")

    def clean_text(self, text):
        text = re.sub(r'\[(BGM|묘사|지문|설명|배경|음악|CHAPTER|챕터|SFX):?.*?\]', '', text, flags=re.IGNORECASE)
        # 괄호 지문은 제거 (연기 지시용이므로)
        text = re.sub(r'\(.*?\)', '', text)
        return text.strip()

    def parse_hybrid_segments(self, text):
        """해설과 대사를 분리하는 정교한 파서"""
        # 따옴표 기준 분할 (" " 또는 ' ')
        parts = re.split(r'([\"|\'].*?[\"|\'])', text, flags=re.DOTALL)
        segments = []
        for p in parts:
            p = p.strip()
            if not p: continue
            
            if (p.startswith('"') and p.endswith('"')) or (p.startswith("'") and p.endswith("'")):
                # 대사 (따옴표 제거 후 저장)
                clean_p = p[1:-1].strip()
                if clean_p:
                    segments.append({"type": "dialogue", "text": clean_p})
            else:
                # 해설
                segments.append({"type": "narration", "text": p})
        return segments

    def generate_qwen(self, text, output_path):
        """소희(Qwen) 엔진 생성"""
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
        """제미나이 2.5 엔진 생성 (Raw PCM 처리 포함)"""
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
                # Raw PCM (24kHz Mono 16bit) -> AudioSegment
                segment = AudioSegment.from_raw(
                    io.BytesIO(raw_data), 
                    sample_width=2, 
                    frame_rate=24000, 
                    channels=1
                )
                segment.export(output_path, format="wav")
                return True
        except Exception as e:
            print(f"❌ Gemini 생성 오류: {e}")
        return False

    def run(self, raw_text, base_name="Hybrid_Result"):
        timestamp = datetime.datetime.now().strftime("%m%d_%H%M")
        output_name = f"{base_name}_{timestamp}.mp3"
        final_path = os.path.join(DOWNLOADS_DIR, output_name)
        
        cleaned = self.clean_text(raw_text)
        segments = self.parse_hybrid_segments(cleaned)
        
        print(f"📋 하이브리드 생성 시작: 총 {len(segments)}개 세그먼트 탐지")
        combined_audio = AudioSegment.empty()
        srt_entries = []
        current_ms = 0
        idx = 1

        with tempfile.TemporaryDirectory() as tmp_dir:
            for s_idx, seg in enumerate(segments):
                text = seg["text"]
                msg = f"[{s_idx+1}/{len(segments)}] {seg['type'].upper()}: {text[:30]}..."
                print(f"   {msg}")
                
                tmp_wav = os.path.join(tmp_dir, f"seg_{s_idx}.wav")
                
                if seg["type"] == "narration":
                    success = self.generate_qwen(text, tmp_wav)
                else:
                    success = self.generate_gemini(text, tmp_wav)
                
                if success and os.path.exists(tmp_wav):
                    segment = AudioSegment.from_file(tmp_wav)
                    
                    # 소희 해설일 경우에만 속도 조절 적용 (제미나이는 자체 감정 속도 존중)
                    if seg["type"] == "narration" and QWEN_SPEED != 1.0:
                         segment = segment._spawn(segment.raw_data, overrides={
                                 "frame_rate": int(segment.frame_rate * QWEN_SPEED)
                             }).set_frame_rate(segment.frame_rate)
                    
                    # 자막 생성 (한 문장/세그먼트 단위)
                    duration = len(segment)
                    start = format_srt_time(current_ms)
                    end = format_srt_time(current_ms + duration)
                    display_text = f"\"{text}\"" if seg["type"] == "dialogue" else text
                    srt_entries.append(f"{idx}\n{start} --> {end}\n{display_text}\n\n")
                    
                    combined_audio += segment
                    current_ms += duration
                    idx += 1
                    
                    # 문간 쉼표 (대사와 해설 사이의 자연스러운 간격)
                    pause = AudioSegment.silent(duration=400)
                    combined_audio += pause
                    current_ms += 400

        # 후처리: Normalization
        print("🔧 최종 오디오 볼륨 최적화 중...")
        combined_audio = combined_audio.normalize(headroom=1.0)
        
        combined_audio.export(final_path, format="mp3", bitrate="192k")
        srt_path = final_path.replace(".mp3", ".srt")
        with open(srt_path, "w", encoding="utf-8-sig") as f:
            f.writelines(srt_entries)
            
        print(f"✨ 완료: {output_name}")
        print(f"📄 자막: {os.path.basename(srt_path)}")

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else os.path.join(PROJ_ROOT, "대본.txt")
    if os.path.exists(target):
        with open(target, "r", encoding="utf-8") as f:
            text = f.read().strip()
        generator = HybridTTSGenerator()
        generator.run(text, os.path.splitext(os.path.basename(target))[0])

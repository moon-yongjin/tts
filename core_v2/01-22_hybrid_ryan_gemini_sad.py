import os
import sys
import time
import re
import datetime
import tempfile
import json
import io
import subprocess
import azure.cognitiveservices.speech as speechsdk
from pydub import AudioSegment
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
    AZURE_KEY = config.get("Azure_Speech_Key")
    AZURE_REGION = config.get("Azure_Region")
    GEMINI_API_KEY = config.get("Gemini_API_KEY")

# [2. 모델 설정]
# Azure Male (리안/그랜파 느낌 - 차분하고 낮은 톤)
AZURE_VOICE = "ko-KR-InJoonNeural" 
AZURE_SPEED = 0.9  # 슬픈 분위기이므로 약간 느리게
AZURE_PITCH = "-5%" # 약간 낮게

# Gemini (대사용 - 할머니 연기톤)
GEMINI_MODEL_ID = "gemini-2.5-flash-preview-tts"
# 지침 강화: 외국어 금지, 차분하면서 슬픈 감정 유지
GEMINI_INSTRUCT = """당신은 70대 할머니입니다. 슬픈 감정이 듬뿍 담긴 차분하고 애절한 목소리로 대사를 연기하세요. 
[절대 규칙] 모든 출력은 반드시 '한국어'로만 생성해야 하며, 영어 등 외국어를 절대 섞지 마십시오. 오직 사람의 자연스러운 목소리만 출력하세요."""

def format_srt_time(ms):
    s, ms = divmod(ms, 1000)
    m, s = divmod(s, 60)
    h, m = divmod(m, 60)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

class RyanGeminiSadGenerator:
    def __init__(self):
        print(f"🚀 Azure Speech SDK 초기화 중: {AZURE_VOICE}")
        self.speech_config = speechsdk.SpeechConfig(subscription=AZURE_KEY, region=AZURE_REGION)
        self.speech_config.set_speech_synthesis_output_format(speechsdk.SpeechSynthesisOutputFormat.Audio48Khz192KBitRateMonoMp3)
        print("✅ Azure 초기화 완료!")
        
        print(f"🚀 Gemini 클라이언트 초기화 중...")
        self.gemini_client = genai.Client(api_key=GEMINI_API_KEY, http_options={'api_version': 'v1alpha'})
        print("✅ Gemini 초기화 완료!")

    def clean_text(self, text):
        text = re.sub(r'\[(BGM|묘사|지문|설명|배경|음악|CHAPTER|챕터|SFX):?.*?\]', '', text, flags=re.IGNORECASE)
        # 괄호 지문 제거
        text = re.sub(r'\(.*?\)', '', text)
        return text.strip()

    def parse_hybrid_segments(self, text):
        """해설(밖)과 대사(안) 분리 파서"""
        parts = re.split(r'([\"|\'].*?[\"|\'])', text, flags=re.DOTALL)
        segments = []
        for p in parts:
            p = p.strip()
            if not p: continue
            
            if (p.startswith('"') and p.endswith('"')) or (p.startswith("'") and p.endswith("'")):
                # 대사 (150자 단위로 쪼개기)
                raw_dialogue = p[1:-1].strip()
                if len(raw_dialogue) > 150:
                    sub_chunks = re.split(r'(?<=[.!?])\s+', raw_dialogue)
                    for sc in sub_chunks:
                        if sc: segments.append({"type": "dialogue", "text": sc})
                else:
                    segments.append({"type": "dialogue", "text": raw_dialogue})
            else:
                # 해설 (Azure는 비교적 긴 청크도 잘 처리하나 200자 정도로 분리)
                sub_narrations = re.split(r'(?<=[.!?])\s+', p)
                for sn in sub_narrations:
                    if sn: segments.append({"type": "narration", "text": sn})
        return segments

    def generate_azure(self, text, output_path):
        """Azure 남자 성우 해설 생성 (슬픈 톤)"""
        ssml_text = f'''
        <speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="ko-KR">
            <voice name="{AZURE_VOICE}">
                <prosody rate="{(AZURE_SPEED-1)*100:+.2f}%" pitch="{AZURE_PITCH}">{text}</prosody>
            </voice>
        </speak>
        '''
        audio_config = speechsdk.audio.AudioOutputConfig(filename=output_path)
        synthesizer = speechsdk.SpeechSynthesizer(speech_config=self.speech_config, audio_config=audio_config)
        result = synthesizer.speak_ssml_async(ssml_text).get()
        return result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted

    def generate_gemini(self, text, output_path):
        """제미나이 2.5 할머니 대사 생성 (극초단 청크 + 한국어 전용)"""
        try:
            prompt = f"{GEMINI_INSTRUCT}\n\n[한국어 대사 전용]\n{text}"
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
            print(f"   ❌ Gemini 생성 오류: {e}")
        return False

    def run(self, raw_text, base_name="Sad_Hybrid"):
        timestamp = datetime.datetime.now().strftime("%m%d_%H%M")
        output_name = f"{base_name}_{timestamp}.mp3"
        final_path = os.path.join(DOWNLOADS_DIR, output_name)
        
        cleaned = self.clean_text(raw_text)
        segments = self.parse_hybrid_segments(cleaned)
        
        print(f"📋 하이브리드(슬픈 톤) 생성 시작: 총 {len(segments)}개 세그먼트")
        combined_audio = AudioSegment.empty()
        srt_entries = []
        current_ms = 0
        idx = 1

        with tempfile.TemporaryDirectory() as tmp_dir:
            for s_idx, seg in enumerate(segments):
                text = seg["text"]
                msg = f"[{s_idx+1}/{len(segments)}] {seg['type'].upper()}: {text[:30]}..."
                print(f"   {msg}")
                
                tmp_audio = os.path.join(tmp_dir, f"seg_{s_idx}.wav")
                
                if seg["type"] == "narration":
                    success = self.generate_azure(text, tmp_audio)
                else:
                    success = self.generate_gemini(text, tmp_audio)
                
                if success and os.path.exists(tmp_audio):
                    segment = AudioSegment.from_file(tmp_audio)
                    duration = len(segment)
                    start = format_srt_time(current_ms)
                    end = format_srt_time(current_ms + duration)
                    display_text = f"\"{text}\"" if seg["type"] == "dialogue" else text
                    srt_entries.append(f"{idx}\n{start} --> {end}\n{display_text}\n\n")
                    
                    combined_audio += segment
                    current_ms += duration
                    idx += 1
                    
                    # 슬픈 연출을 위해 문간 쉼표를 약간 길게 (550ms)
                    pause = AudioSegment.silent(duration=550)
                    combined_audio += pause
                    current_ms += 550

        print("🔧 최종 오디오 볼륨 최적화 중...")
        combined_audio = combined_audio.normalize(headroom=1.0)
        combined_audio.export(final_path, format="mp3", bitrate="192k")
        srt_path = final_path.replace(".mp3", ".srt")
        with open(srt_path, "w", encoding="utf-8-sig") as f:
            f.writelines(srt_entries)
            
        print(f"✨ 완료: {output_name}")
        print(f"📄 자막: {os.path.basename(srt_path)}")
        
        # 생성 완료 후 자동 실행 요청 처리
        print(f"🎵 생성된 오디오를 재생합니다...")
        try:
            subprocess.run(["open", final_path]) # Mac 환경
        except:
            pass

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else os.path.join(PROJ_ROOT, "대본.txt")
    if os.path.exists(target):
        with open(target, "r", encoding="utf-8") as f:
            text = f.read().strip()
        generator = RyanGeminiSadGenerator()
        generator.run(text, os.path.splitext(os.path.basename(target))[0])

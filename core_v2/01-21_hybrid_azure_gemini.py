import os
import sys
import time
import re
import datetime
import tempfile
import json
import io
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
# Azure Male (해설용)
AZURE_VOICE = "ko-KR-BongJinNeural" # 좀 더 밝고 톤이 높은 남자 성우 (BongJin)
AZURE_SPEED = 1.05
AZURE_PITCH = "+15%" # 톤 올림

# Gemini (대사용)
GEMINI_MODEL_ID = "gemini-2.5-flash-preview-tts"
GEMINI_INSTRUCT = "당신은 70대 할머니입니다. 따옴표 안의 대사를 상황에 맞는 감정을 듬뿍 담아 실제로 말하듯 연기하세요. 인자하면서도 때로는 단호한 할머니의 목소리입니다."

def format_srt_time(ms):
    s, ms = divmod(ms, 1000)
    m, s = divmod(s, 60)
    h, m = divmod(m, 60)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

class AzureGeminiHybridGenerator:
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
                # 대사
                segments.append({"type": "dialogue", "text": p[1:-1].strip()})
            else:
                # 해설 (콤마 단위로 한 번 더 쪼개서 Azure 가독성 높이기 가능하나, 일단 통째로 처리)
                segments.append({"type": "narration", "text": p})
        return segments

    def generate_azure(self, text, output_path):
        """Azure 남자 성우 해설 생성 (톤 강화 + 말끝 내리기)"""
        # contour=(80%, +0%) (100%, -15%) -> 문장 끝부분에서 급격히 톤을 낮춤
        ssml_text = f'''
        <speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="ko-KR">
            <voice name="{AZURE_VOICE}">
                <prosody rate="{(AZURE_SPEED-1)*100:+.2f}%" pitch="{AZURE_PITCH}" contour="(80%, +0%) (100%, -15%)">
                    {text}
                </prosody>
            </voice>
        </speak>
        '''
        audio_config = speechsdk.audio.AudioOutputConfig(filename=output_path)
        synthesizer = speechsdk.SpeechSynthesizer(speech_config=self.speech_config, audio_config=audio_config)
        result = synthesizer.speak_ssml_async(ssml_text).get()
        return result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted

    def generate_gemini(self, text, output_path):
        """제미나이 2.5 할머니 대사 생성"""
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

    def run(self, raw_text, base_name="Azure_Gemini_Hybrid"):
        timestamp = datetime.datetime.now().strftime("%m%d_%H%M")
        output_name = f"{base_name}_{timestamp}.mp3"
        final_path = os.path.join(DOWNLOADS_DIR, output_name)
        
        cleaned = self.clean_text(raw_text)
        segments = self.parse_hybrid_segments(cleaned)
        
        print(f"📋 하이브리드(아주르+제미나이) 생성 시작: 총 {len(segments)}개 세그먼트")
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
                    
                    # 싱크 및 자막 처리
                    duration = len(segment)
                    start = format_srt_time(current_ms)
                    end = format_srt_time(current_ms + duration)
                    display_text = f"\"{text}\"" if seg["type"] == "dialogue" else text
                    srt_entries.append(f"{idx}\n{start} --> {end}\n{display_text}\n\n")
                    
                    combined_audio += segment
                    current_ms += duration
                    idx += 1
                    
                    # 자연스러운 쉼표 (400ms)
                    pause = AudioSegment.silent(duration=450)
                    combined_audio += pause
                    current_ms += 450

        # 최종 노멀라이징
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
        generator = AzureGeminiHybridGenerator()
        generator.run(text, os.path.splitext(os.path.basename(target))[0])

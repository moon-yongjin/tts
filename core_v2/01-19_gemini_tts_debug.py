import os
import json
from google import genai
from google.genai import types
from pydub import AudioSegment
import io

# 1. Config 로드
CONFIG_PATH = "/Users/a12/projects/tts/config.json"
with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    config = json.load(f)
    API_KEY = config.get("Gemini_API_KEY")

client = genai.Client(api_key=API_KEY, http_options={'api_version': 'v1alpha'})

# 2. 대본 로드
TEST_TEXT = "제미나이 2.5 플래시 프리뷰 티티에스 테스트입니다. 오냐, 너희가 판 무덤에 직접 들어가 봐라."

DOWNLOADS_DIR = os.path.join(os.path.expanduser("~"), "Downloads")

def test_gemini_25_preview_tts():
    """Gemini 2.5 Flash Preview TTS 결과물의 인코딩 확인 및 변환"""
    model_id = "gemini-2.5-flash-preview-tts"
    print(f"🎙️ [재검증] {model_id} 테스트 시작...")
    output_path = os.path.join(DOWNLOADS_DIR, "Gemini_25_TTS_Fixed.mp3")
    
    try:
        response = client.models.generate_content(
            model=model_id,
            contents=TEST_TEXT,
            config=types.GenerateContentConfig(
                response_modalities=["AUDIO"]
            )
        )
        
        audio_found = False
        full_audio_data = bytearray()
        
        for part in response.candidates[0].content.parts:
            if part.inline_data:
                mime_type = part.inline_data.mime_type
                data = part.inline_data.data
                print(f"📡 수신된 데이터 MIME: {mime_type}, 크기: {len(data)} bytes")
                full_audio_data.extend(data)
                audio_found = True
        
        if audio_found:
            # 만약 MIME 타입이 audio/mpeg가 아니거나 헤더가 없는 raw 데이터라면 pydub으로 변환 시도
            # 일반적으로 Gemini Native/TTS는 24000Hz or 48000Hz PCM인 경우가 많음
            # 하지만 SDK 레벨에서 audio/mpeg를 요청했을 때 실패했으므로, 
            # 현재 수신된 데이터가 무엇인지에 따라 처리가 필요함.
            
            # 우선 파일로 그대로 저장 (비교용)
            raw_path = os.path.join(DOWNLOADS_DIR, "Gemini_25_TTS_Raw_Data.dat")
            with open(raw_path, "wb") as f:
                f.write(full_audio_data)
            
            # MP3로 변환 시도 (Raw PCM 16bit 24kHz Mono 가정 - 구글 머티리얼 표준)
            try:
                # 만약 header가 없다면 아래와 같이 raw로 읽어야 함
                audio = AudioSegment.from_raw(
                    io.BytesIO(full_audio_data), 
                    sample_width=2, 
                    frame_rate=24000, 
                    channels=1
                )
                audio.export(output_path, format="mp3")
                print(f"✅ 변환 완료: {output_path}")
            except Exception as e:
                print(f"⚠️ Raw 변환 실패 (이미 헤더가 있을 수 있음): {e}")
                with open(output_path, "wb") as f:
                    f.write(full_audio_data)
                print(f"✅ 원본 데이터로 저장됨: {output_path}")
                
        return audio_found
    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
        return False

if __name__ == "__main__":
    test_gemini_25_preview_tts()

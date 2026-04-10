import os
import requests
import json
from dotenv import load_dotenv

# .env 파일에서 API 키 로드
load_dotenv("/Users/a12/projects/tts/core_v2/.env")

SUPERTONE_API_KEY = os.getenv("SUPERTONE_API_KEY")
VOICE_ID = "6HL8gGg8PYdE8qDpTbF26E" # 형님 클로닝 보이스 ID
OUTPUT_PATH = "/Users/a12/Downloads/supertone_me_sample_10s.wav"

def generate_sample():
    url = f"https://supertoneapi.com/v1/text-to-speech/{VOICE_ID}"
    
    headers = {
        "x-sup-api-key": SUPERTONE_API_KEY,
        "Content-Type": "application/json"
    }

    # 약 10초 정도의 분량 (배속 1.2 기준)
    text = "안녕하세요, 형님 목소리 클로닝 테스트 입니 다. 지금 이 목소리는 슈퍼톤 에이피아이를 통해 생성되고 있으며, 약 10초 정도의 샘플을 만들기 위해 적당한 길이의 문장을 낭독하고 있습니다."

    payload = {
        "text": text,
        "language": "ko",
        "model": "sona_speech_1",
        "voice_settings": {
            "speed": 1.2
        }
    }
    
    print(f"🎙️ Generating sample for voice 'me' (ID: {VOICE_ID})...")
    try:
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            with open(OUTPUT_PATH, "wb") as f:
                f.write(response.content)
            print(f"✅ Success! Sample saved to: {OUTPUT_PATH}")
        else:
            print(f"❌ API Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"⚠️ Request failed: {e}")

if __name__ == "__main__":
    generate_sample()

import json
import os
from google import genai

# Config 로드
CONFIG_PATH = "/Users/a12/projects/tts/config.json"
with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    config = json.load(f)
    GEMINI_API_KEY = config.get("Gemini_API_KEY")

client = genai.Client(api_key=GEMINI_API_KEY)

print("🔍 사용 가능한 모델 리스트 확인 중...")
try:
    models = client.models.list()
    for m in models:
        if "image" in m.name.lower() or "flash" in m.name.lower():
            print(f"- {m.name} (Supported: {m.supported_actions})")
except Exception as e:
    print(f"❌ 모델 리스트 확인 실패: {e}")

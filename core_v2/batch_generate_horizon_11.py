import os
import json
import time
import sys
import re
import requests
import base64
import shutil
from google import genai
from google.genai import types

# [설정]
BASE_PATH = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(BASE_PATH)
CONFIG_PATH = os.path.join(ROOT_DIR, "config.json")

# 1. API Key 로드
GEMINI_KEYS = []
if os.path.exists(CONFIG_PATH):
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            config = json.load(f)
            GEMINI_KEYS = [v for k, v in config.items() if "Gemini_API_KEY" in k and v]
    except: pass

if not GEMINI_KEYS:
    print("❌ API Key를 찾을 수 없습니다.")
    sys.exit(1)

client = genai.Client(api_key=GEMINI_KEYS[0])

# 2. 로컬 이미지 생성 API 설정
SD_API_URL = "http://127.0.0.1:7860/sdapi/v1/txt2img"

# 저장 디렉토리 설정
_timestamp = time.strftime("%m%d_%H%M")
DOWNLOAD_DIR = os.path.join(os.path.expanduser("~"), "Downloads", f"가로형_배치생성_{_timestamp}")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)
print(f"📂 저장 폴더: {DOWNLOAD_DIR}")

# [고정 스타일] 요청 기반 조정
FIXED_STYLE = "Photorealistic, hyper-realistic, 8k RAW photo, Fujifilm XT4, cinematic lighting, crisp and clear atmosphere, natural skin texture"

def get_consistent_prompts(script_chunk, prev_summary="None", current_location="Unknown"):
    """Gemini를 사용해 플럭스 전용 프롬프트 생성"""
    prompt = f"""
    당신은 Stable Diffusion을 위한 비주얼 디렉터입니다.
    아래 대본 청크를 바탕으로 한 장의 영화 같은 실사 사진(가로형)을 위한 영문 프롬프트를 생성하세요.

    [대본 청크]: {script_chunk}
    [이전 상황]: {prev_summary}
    [장소]: {current_location}

    [조건]:
    - 주인공: 한국인 할머니(Korean elderly woman, 흰머리가 있는 번 헤어, 검은 겨울 패딩), 한국인 어린 남자아이(Korean young boy, 녹색 줄무늬 티셔츠)
    - 인종: 반드시 한국인(Korean, Asian)의 얼굴과 외모 특징을 묘사할 것. 서양인/백인(Western, Caucasian)은 절대 금지.
    - 분위기: 밤, 겨울, 외곽 휴게소, 따스함과 쓸쓸함 공존.
    - 절대 금지어: Beautiful, Masterpiece, Perfect.
    - 스타일: {FIXED_STYLE}

    [출력 JSON 규격 ONLY]:
    {{
      "visual_prompt": "Detailed English descriptive prompt (Exclude quality buzzwords)",
      "summary": "Brief summary of this scene",
      "location": "location name"
    }}
    """
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash", 
            contents=prompt,
            config=types.GenerateContentConfig(response_mime_type="application/json")
        )
        return json.loads(response.text)
    except Exception as e:
        print(f"⚠️ 프롬프트 생성 실패: {e}")
        return None

def generate_single_image(prompt_text, index):
    """Draw Things App API 호출 (6스텝, 가로형)"""
    filename = f"scene_{index:03d}.png"
    filepath = os.path.join(DOWNLOAD_DIR, filename)

    # 💡 가로형 가속 세팅 보강
    payload = {
        "prompt": f"{FIXED_STYLE}, masterpiece, high-end cinematic, ultra-detailed textures, {prompt_text}",
        "negative_prompt": "text, watermark, low quality, blurry, distorted, anime, cartoon, illustration, bad anatomy, caucasian, western, white person, blonde hair, blue eyes",
        "steps": 6,
        "width": 1216,         # 가로형
        "height": 684,         # 가로형
        "seed": -1,
        "guidance_scale": 1.0,
        "sampler": "Euler A AYS", # 🚀 스크린샷 기반 고정
        "shift": 3.0,           # 🚀 스크린샷에서 3.00 확인됨
        "sharpness": 5,
        "seed_mode": "Scale Alike"
    }

    try:
        print(f"📤 [{index}/11] 생성 요청 중...")
        response = requests.post(SD_API_URL, json=payload, timeout=300)
        
        if response.status_code == 200:
            r = response.json()
            if "images" in r and len(r["images"]) > 0:
                with open(filepath, "wb") as f:
                    f.write(base64.b64decode(r["images"][0]))
                print(f"   ✅ 생성 완료: {filename}")
                return True
            else:
                print(f"   ❌ 이미지 데이터 없음: {r}")
        else:
            print(f"   ❌ HTTP 에러: {response.status_code}")
    except Exception as e:
        print(f"   ❌ 통신 실패: {e}")
    return False

if __name__ == "__main__":
    script_path = "/Users/a12/projects/tts/대본.txt"
    if not os.path.exists(script_path):
        print("❌ 대본.txt가 없습니다.")
        sys.exit(1)

    with open(script_path, "r", encoding="utf-8") as f:
        full_text = f.read().strip()

    # 🌟 전체 33장 분할 (텍스트 길이 기준 33등분)
    limit = max(20, len(full_text) // 33)
    chunks = []
    text = ' '.join(full_text.split())
    for i in range(33):
        start = i * limit
        end = (i+1) * limit if i < 32 else len(text)
        if start < len(text):
            chunks.append(text[start:end].strip())

    print(f"📊 대본 분할 완료: 총 {len(chunks)}장 분량")

    # 루프 가동 (초반 11장만)
    current_summary = "Start"
    current_location = "Unknown"
    success_count = 0

    for i, chunk in enumerate(chunks[:11]):  # 🚀 딱 11장까지만
        print(f"\n🎬 Scene {i+1} 가공 및 생성")
        data = get_consistent_prompts(chunk, current_summary, current_location)
        if data:
            current_summary = data.get("summary", "")
            current_location = data.get("location", "")
            res = generate_single_image(data.get("visual_prompt", ""), i+1)
            if res: success_count += 1
        else:
            print("   ⚠️ 프롬프트 생성 스킵")

    print(f"\n🎉 작업 완료: {success_count}/11 개 이미지 생성됨")
    print(f"📂 저장 경로: {DOWNLOAD_DIR}")

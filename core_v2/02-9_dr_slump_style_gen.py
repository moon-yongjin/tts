import os
import requests
import json
import base64

# [설정]
DRAWTHINGS_URL = "http://127.0.0.1:7860/sdapi/v1/txt2img"
OUTPUT_PATH = os.path.expanduser("~/Downloads/dr_slump_style.png")

# [프롬프트] - 닥터슬럼프 (아키라 토리야마) 스타일
# Arale Norimaki, 80s anime, vibrant colors, clean cel-shading.
PROMPT = (
    "A vibrant, high-quality anime illustration of Arale Norimaki from Dr. Slump, "
    "classic Akira Toriyama 1980s anime style, wearing a red hat with winged 'ARALE' text, "
    "large round glasses, enthusiastic and cute expression, purple hair, "
    "clean cel-shading, bright colors, retro anime aesthetic, 8k resolution, masterpiece"
)

payload = {
    "prompt": PROMPT,
    "negative_prompt": "photorealistic, 3d render, realistic, blurry, low resolution, deformed face, bad anatomy, dark, moody",
    "steps": 4, 
    "cfg_scale": 1.0,
    "width": 1024,
    "height": 1024,
    "sampler_name": "Euler a",
    "seed": 5555,
}

def generate_dr_slump():
    print(f"👓 '닥터슬럼프' 스타일로 생성을 시작합니다...")
    try:
        response = requests.post(DRAWTHINGS_URL, json=payload, timeout=600)
        if response.status_code == 200:
            result = response.json()
            if "images" in result and len(result["images"]) > 0:
                img_data = base64.b64decode(result["images"][0])
                with open(OUTPUT_PATH, "wb") as f:
                    f.write(img_data)
                print(f"✅ 생성 성공: {OUTPUT_PATH}")
            else:
                print(f"❌ 에러: 이미지 데이터가 없습니다. {result}")
        else:
            print(f"❌ API 요청 실패: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ 예외 발생: {e}")

if __name__ == "__main__":
    generate_dr_slump()

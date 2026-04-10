import os
import requests
import json
import base64

# [설정]
DRAWTHINGS_URL = "http://127.0.0.1:7860/sdapi/v1/txt2img"
OUTPUT_PATH = os.path.expanduser("~/Downloads/tiger_manhwa_style.png")

# [프롬프트] - 호랑이 형님 (호랑이 만화) 스타일
# 핵심: 역동적인 호랑이, 세밀한 털 묘사, 거친 붓 터치, 동양적 판타지 분위기.
PROMPT = (
    "A legendary, epic Korean tiger (Sang-gun) with glowing eyes from 'Horang-hyungnim' manhwa style, "
    "intricate and detailed fur texture, powerful and dynamic pose, "
    "bold and expressive ink brush strokes, textured ink wash style, "
    "dark and atmospheric traditional Korean mountain landscape background with misty fog, "
    "high contrast black and white with subtle earthy tones, 8k resolution, cinematic masterpiece"
)

payload = {
    "prompt": PROMPT,
    "negative_prompt": "photorealistic, 3d render, digital painting, smooth gradients, cartoon, blurry, low resolution, cute tiger",
    "steps": 6, 
    "cfg_scale": 1.0,
    "width": 1024,
    "height": 1024,
    "sampler_name": "Euler a",
    "seed": 1234,
}

def generate_tiger_manhwa():
    print(f"🐯 '호랑이 만화' 스타일로 생성을 시작합니다 (호랑이형님 스타일)...")
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
    generate_tiger_manhwa()

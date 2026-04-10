import os
import requests
import json
import base64

# [설정]
DRAWTHINGS_URL = "http://127.0.0.1:7860/sdapi/v1/txt2img"
OUTPUT_PATH = os.path.expanduser("~/Downloads/cinematic_tiger_flux.png")

# [프롬프트] - 시네마틱 하이퍼 리얼리즘 호랑이
# 핵심: Hyper-realistic fur, cinematic lighting, national geographic style, 8k, bokeh background.
PROMPT = (
    "A majestic, hyper-realistic portrait of a Siberian tiger, "
    "cinematic lighting, dramatic shadows, extreme detail in fur and whiskers, "
    "piercing orange eyes, national geographic photography style, 8k resolution, "
    "shallow depth of field with a blurred snowy forest background, masterpiece, "
    "vibrant colors, sharp focus, professionally color graded"
)

payload = {
    "prompt": PROMPT,
    "negative_prompt": "cartoon, 3d, cg, anime, blurry, low resolution, deformed, bad eyes, painting, drawing, sketch",
    "steps": 4, 
    "cfg_scale": 1.0,
    "width": 1024,
    "height": 1024,
    "sampler_name": "Euler a",
    "seed": 4321,
}

def generate_cinematic_tiger():
    print(f"🐯 '시네마틱 호랑이' 생성을 시작합니다 (하이퍼 리얼리즘)...")
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
    generate_cinematic_tiger()

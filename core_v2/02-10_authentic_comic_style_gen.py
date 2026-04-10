import os
import requests
import json
import base64

# [설정]
DRAWTHINGS_URL = "http://127.0.0.1:7860/sdapi/v1/txt2img"
OUTPUT_PATH = os.path.expanduser("~/Downloads/authentic_comic_style.png")

# [프롬프트] - 진짜 만화책 인쇄물 느낌 (Authentic Scanned Manga/Comic)
# 핵심: Screentone, Halftone dots, Ink bleed, Rough paper.
PROMPT = (
    "A masterful black and white authentic manga scan of an old Korean martial arts master, "
    "classic 1990s comic book aesthetic, professional screentone patterns for shading, "
    "halftone dots, visible ink bleeding on rough yellowish paper texture, "
    "high contrast black and white ink, G-pen ink pressure lines, No digital gradients, "
    "authentic comic book scan, vintage manga magazine style, hand-drawn masterpiece, "
    "sharp focus on ink details and screen tones"
)

payload = {
    "prompt": PROMPT,
    "negative_prompt": "photorealistic, realistic, 3d render, digital painting, smooth gradients, color, grey scales, blurry, clean digital lines, modern anime",
    "steps": 6, # 스타일 밀도를 위해 약간 높임
    "cfg_scale": 1.0,
    "width": 1024,
    "height": 1024,
    "sampler_name": "Euler a",
    "seed": 2024,
}

def generate_authentic_comic():
    print(f"📖 '진짜 인쇄 만화책' 스타일로 생성을 시작합니다 (망점/스크린톤)...")
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
    generate_authentic_comic()

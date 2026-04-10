import os
import requests
import json
import base64

# [설정]
DRAWTHINGS_URL = "http://127.0.0.1:7860/sdapi/v1/txt2img"
OUTPUT_PATH = os.path.expanduser("~/Downloads/wuxia_line_art_style.png")

# [프롬프트] - 채색 없는 순수 선화 (Black & White line art) 만화책 스타일
PROMPT = (
    "A masterful black and white line art illustration of an old 60-year-old Korean martial arts master, "
    "classic comic book style, pure ink drawing, clean bold lines, no colors, high contrast, "
    "manga aesthetic, professional manhwa ink work, cross-hatching for shadows, "
    "on white background, sharp details, cinematic composition, masterpiece ink illustration"
)

payload = {
    "prompt": PROMPT,
    "negative_prompt": "color, shaded, digital painting, photorealistic, 3d, gradient, blurry, gray scale, grey",
    "steps": 4, 
    "cfg_scale": 1.0,
    "width": 1024,
    "height": 1024,
    "sampler_name": "Euler a",
    "seed": 8888,
}

def generate_line_art():
    print(f"🖋️ '흑백 선화 만화' 스타일로 생성을 시작합니다...")
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
    generate_line_art()

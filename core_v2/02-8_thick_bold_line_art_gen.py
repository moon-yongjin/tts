import os
import requests
import json
import base64

# [설정]
DRAWTHINGS_URL = "http://127.0.0.1:7860/sdapi/v1/txt2img"
OUTPUT_PATH = os.path.expanduser("~/Downloads/wuxia_thick_bold_line_art.png")

# [프롬프트] - 굵은 선, 명암 절대 없음 (Pure Thick Bold Line Art, No Shading)
# Focusing on: marker style, coloring book style, stenciled, flat black and white.
PROMPT = (
    "A minimalist black and white line art illustration of an old Korean martial arts master, "
    "extremely thick bold black lines, sharp outlines, absolutely no shading, no shadows, "
    "no cross-hatching, no grayscale, pure white background, coloring book style, "
    "stencil art aesthetic, flat composition, high contrast, bold marker drawing, "
    "masterpiece minimalist outline"
)

payload = {
    "prompt": PROMPT,
    "negative_prompt": "shading, shadow, gray, grey, gradient, color, photorealistic, 3d, blurry, soft lines, thin lines, cross-hatching, hatching",
    "steps": 4, 
    "cfg_scale": 1.0,
    "width": 1024,
    "height": 1024,
    "sampler_name": "Euler a",
    "seed": 9999,
}

def generate_thick_line_art():
    print(f"🖋️ '굵은 선명한 선화' 스타일로 생성을 시작합니다 (명암 없음)...")
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
    generate_thick_line_art()

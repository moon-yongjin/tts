import os
import requests
import json
import base64

# [설정]
DRAWTHINGS_URL = "http://127.0.0.1:7860/sdapi/v1/txt2img"
OUTPUT_PATH = os.path.expanduser("~/Downloads/wuxia_fountain_pen_sketch.png")

# [프롬프트] - 거친 만년필 스케치 (Rough Fountain Pen Sketch)
# 핵심: Loose lines, quick shading (슥슥), ink on paper, raw hand-drawn.
PROMPT = (
    "A raw, hand-drawn ink sketch of an old Korean martial arts master on a textured paper, "
    "drawn with a fountain pen, loose and organic outlines, messy ink lines, "
    "quick and rough scribbled shading, minimal detail, messy ink splatters, "
    "sketchbook aesthetic, no digital perfection, direct fountain pen on paper, "
    "imperfections, visible pen pressure, artistic and expressive line work, "
    "white background with paper texture"
)

payload = {
    "prompt": PROMPT,
    "negative_prompt": "photorealistic, 3d, digital art, smooth gradients, screentones, halftone, clean lines, perfect symmetry, gradient, gray shading",
    "steps": 4, 
    "cfg_scale": 1.0,
    "width": 1024,
    "height": 1024,
    "sampler_name": "Euler a",
    "seed": 1111,
}

def generate_fountain_pen_sketch():
    print(f"🖋️ '거친 만년필 스케치' 스타일로 생성을 시작합니다 (슥슥 그린 느낌)...")
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
    generate_fountain_pen_sketch()

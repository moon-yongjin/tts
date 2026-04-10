import os
import requests
import json
import base64

# [설정]
DRAWTHINGS_URL = "http://127.0.0.1:7860/sdapi/v1/txt2img"
OUTPUT_PATH = os.path.expanduser("~/Downloads/wuxia_minhwa_style.png")

# [프롬프트] - 한국 고전 민화(Minhwa) 및 옛날 만화 스타일 결합
# Minhwa: traditional folk painting, flat perspective, vibrant but aged colors, ink outlines.
# Retro Manhwa: 1970-80s style, coarse lines, printed paper texture.
PROMPT = (
    "A traditional Korean Minhwa folk painting of a powerful old martial arts master, "
    "vintage Korean manhwa style from the 1970s, ink wash and light color on aged mulberry paper (Hanji), "
    "bold and coarse ink brush outlines, flat perspective, vibrant but muted colors, "
    "mulberry paper texture, hand-drawn aesthetic, high detail in style, cinematic composition"
)

payload = {
    "prompt": PROMPT,
    "negative_prompt": "modern 3d render, photorealistic, photography, digital painting, glossy, neon, futuristic",
    "steps": 6, # 스타일 표현을 위해 약간 더 높임
    "cfg_scale": 1.0,
    "width": 1024,
    "height": 1024,
    "sampler_name": "Euler a",
    "seed": 7777,
}

def generate_minhwa():
    print(f"🎨 '민화/고전 만화' 스타일로 생성을 시작합니다...")
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
    generate_minhwa()

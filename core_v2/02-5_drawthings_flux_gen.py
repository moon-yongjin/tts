import os
import requests
import json
import time

# [설정]
DRAWTHINGS_URL = "http://127.0.0.1:7860/sdapi/v1/txt2img"
OUTPUT_DIR = os.path.expanduser("~/Downloads/Flux_Samples_DrawThings")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# [프롬프트 리스트] - 대본 기반 최적화
PROMPTS = [
    {
        "name": "01_conflict.png",
        "prompt": "A cinematic, photorealistic portrait (9:16) of a frustrated Korean woman (Kim Ji-soo, late 20s) in a dim, cluttered old apartment. She is pinching her nose with her fingers, looking disgusted at the smell. In the background, a hunched elderly woman is blurred, scraping a spoon on a worn wooden table. Warm sunlight filters through a dusty window. High fashion photography style, detailed skin texture, pores, realistic eyes, 8k resolution, Flux model masterpiece.",
        "seed": 1234
    },
    {
        "name": "02_remorse.png",
        "prompt": "Emotional close-up portrait (9:16) of Kim Ji-soo (Korean woman, late 20s) sitting on a dark bathroom floor, quietly sobbing. She is clutching a crumpled plastic bag containing old certificates and school awards. Her eyes are red and wet with tears, reflecting deep regret. Moody, dramatic lighting, high contrast, focus on facial expression and realistic skin details. Cinematic film still, extremely high detail, Flux photorealism.",
        "seed": 5678
    },
    {
        "name": "03_icu_farewell.png",
        "prompt": "A somber, realistic side-view (9:16) of Kim Ji-soo holding the thin, weathered hand of her unresponsive elderly mother in an ICU hospital bed. sterile background with out-of-focus medical equipment. Soft, cool lighting. Ji-soo's expression is one of deep sorrow and apology. Masterpiece, high detail on skin aging vs youth, cinematic atmosphere, photorealistic portrait, sharp focus on the hands and face.",
        "seed": 9012
    }
]

def generate_image(item):
    print(f"🚀 생성 중: {item['name']}...")
    
    payload = {
        "prompt": item["prompt"],
        "negative_prompt": "cartoon, 3d, cg, anime, blurry, low resolution, deformed, bad eyes, extra fingers, low quality, worst quality",
        "steps": 6,        # Juggernaut XL Lightning 권장 (4~8)
        "cfg_scale": 2.0,    # Lightning용 약간의 CFG
        "width": 896,        # SDXL 표준 세로 해상도
        "height": 1152,      # SDXL 표준 세로 해상도
        "seed": item["seed"],
        "sampler_name": "DPM++ 2M Karras", # Juggernaut/SDXL 권장
    }

    try:
        response = requests.post(DRAWTHINGS_URL, json=payload, timeout=300)
        if response.status_code == 200:
            result = response.json()
            # Draw Things API usually returns base64 list in 'images'
            if "images" in result and len(result["images"]) > 0:
                import base64
                img_data = base64.b64decode(result["images"][0])
                filepath = os.path.join(OUTPUT_DIR, item["name"])
                with open(filepath, "wb") as f:
                    f.write(img_data)
                print(f"✅ 저장 완료: {filepath}")
            else:
                print(f"❌ 에러: 응답에 이미지 데이터가 없습니다. {result}")
        else:
            print(f"❌ API 요청 실패: {response.status_code}, {response.text}")
    except Exception as e:
        print(f"❌ 예외 발생: {e}")

if __name__ == "__main__":
    print("🎨 Draw Things API를 통한 Flux 이미지 생성을 시작합니다.")
    for p in PROMPTS:
        generate_image(p)
    print("\n✨ 모든 작업이 완료되었습니다. Downloads/Flux_Samples_DrawThings 폴더를 확인하세요.")

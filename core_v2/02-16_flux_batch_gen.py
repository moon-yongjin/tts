import os
import requests
import json
import base64
import time
import concurrent.futures

# [설정]
DRAWTHINGS_URL = "http://127.0.0.1:7860/sdapi/v1/txt2img"
OUTPUT_DIR = os.path.expanduser("~/Downloads/Flux_Script_Batch")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# [공통 스타일 프롬프트] - Enhanced Realism (Flux + LoRA)
STYLE_PROMPT = (
    "cinematic lighting, hyper-realistic, 8k resolution, raw photography, "
    "masterpiece, best quality, ultra detailed, depth of field, <lora:flux-RealismLora:0.8>"
)

NEGATIVE_PROMPT = "cartoon, 3d, painting, drawing, sketch, blurry, plastic, smooth, doll, low resolution, bad anatomy"

# [5가지 장면 정의]
scenes = [
    {
        "filename": "01_disgust.png",
        "prompt": (
            "A young Korean woman pinching her nose in disgust, disgusted facial expression, frowning, "
            "standing in a messy old room, "
            f"{STYLE_PROMPT}"
        )
    },
    {
        "filename": "02_mom_hand.png",
        "prompt": (
            "Close-up of an old woman's hand with liver spots and curved fingernails scraping dried rice off a table, "
            "sad and depressing atmosphere, macro shot, detailed skin texture, "
            f"{STYLE_PROMPT}"
        )
    },
    {
        "filename": "03_phone_memo.png",
        "prompt": (
            "Close-up of an old shattered smartphone screen showing a memo list, held by a trembling hand, "
            "dim lighting, emotional atmosphere, focus on the phone screen, "
            f"{STYLE_PROMPT}"
        )
    },
    {
        "filename": "04_bathroom_cry.png",
        "prompt": (
            "A young Korean woman sitting on a bathroom floor crying, holding wrinkled old paper certificates, "
            "tears on face, messy hair, despair, cold bathroom tile background, "
            f"{STYLE_PROMPT}"
        )
    },
    {
        "filename": "05_icu_goodbye.png",
        "prompt": (
            "Hospital ICU room scene, an old woman lying in bed entcubated, a young woman holding her hand crying, "
            "sad goodbye, medical equipment background, dramatic lighting, "
            f"{STYLE_PROMPT}"
        )
    }
]

def generate_image(scene):
    print(f"🚀 요청 시작: {scene['filename']}...")
    payload = {
        "prompt": scene["prompt"],
        "negative_prompt": NEGATIVE_PROMPT,
        "steps": 6, 
        "cfg_scale": 1.0,
        "width": 1024,
        "height": 1024,
        "sampler_name": "Euler a",
        "seed": -1
    }
    
    try:
        response = requests.post(DRAWTHINGS_URL, json=payload, timeout=600)
        if response.status_code == 200:
            result = response.json()
            if "images" in result and len(result["images"]) > 0:
                img_data = base64.b64decode(result["images"][0])
                file_path = os.path.join(OUTPUT_DIR, scene["filename"])
                with open(file_path, "wb") as f:
                    f.write(img_data)
                print(f"✅ 저장 완료: {file_path}")
                return True
            else:
                print(f"❌ 에러 ({scene['filename']}): 데이터 없음")
        else:
            print(f"❌ 실패 ({scene['filename']}): {response.status_code}")
    except Exception as e:
        print(f"❌ 예외 ({scene['filename']}): {e}")
    return False

def main():
    print(f"🎬 대본 기반 5장 배치 생성 시작 (병렬 요청)...")
    print(f"📂 저장 경로: {OUTPUT_DIR}")
    
    start_time = time.time()
    
    # 병렬 처리 (Draw Things 큐에 밀어넣기)
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(generate_image, scene): scene for scene in scenes}
        
        for future in concurrent.futures.as_completed(futures):
            scene = futures[future]
            try:
                future.result()
            except Exception as exc:
                print(f"❌ {scene['filename']} 처리 중 예외 발생: {exc}")

    end_time = time.time()
    total_time = end_time - start_time
    
    print(f"\n✨ 모든 작업 완료!")
    print(f"⏱️ 총 소요 시간: {total_time:.2f}초")
    print(f"📊 장당 평균 시간: {total_time/len(scenes):.2f}초")

if __name__ == "__main__":
    main()

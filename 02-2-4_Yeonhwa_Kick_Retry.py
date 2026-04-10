import requests
import json
import base64
import os
import time
from datetime import datetime

# 1. 설정
DRAWTHINGS_URL = "http://127.0.0.1:7860/sdapi/v1/txt2img"
OUTPUT_BASE_DIR = os.path.expanduser("~/Downloads")
TIMESTAMP = datetime.now().strftime("%m%d_%H%M")
SAVE_DIR = os.path.join(OUTPUT_BASE_DIR, f"Yeonhwa_Kick_Retry_{TIMESTAMP}")
os.makedirs(SAVE_DIR, exist_ok=True)

# 2. 공통 설정 (사용자 요청 고정값: Steps 6, CFG 1.0)
COMMON_NEGATIVE = "easynegative, human_low_quality, bad_anatomy, distorted_face, blurry, lowres, text, watermark, signature, modern_clothing, western_features, 3d, render, illustration"
COMMON_PARAMS = {
    "sampler_name": "Euler A AYS",
    "steps": 6,
    "cfg_scale": 1.0,
    "width": 720,
    "height": 1280,
    "negative_prompt": COMMON_NEGATIVE,
    "model": "z_image_turbo_1.0_q8p.ckpt",
    "shift": 3.0,
    "sharpness": 6
}

# 3. 캐릭터 및 배경 고정
IDO_YOUNG = "A drunk 20-year-old Korean nobleman (IDO), fine purple silk hanbok, traditional topknot (SANGTU), furious and cruel facial features, sharp chin."
YEONHWA_YOUNG = "A beautiful 18-year-old Korean woman (YEONHWA), humble cotton hanbok, long dark hair, falling back in shock, terror in her eyes."
BG_HANOK_INTERIOR = "Inside a traditional Korean room (HANOK), wooden floor, candlelight casting long flickering shadows, spilled traditional table (SOBAN) with scattered food and brass dishes."

SCENES = [
    {
        "name": "Kick_Scene_v1",
        "prompt": f"(Dynamic action shot, side angle), {IDO_YOUNG} mid-air kick towards the camera, {YEONHWA_YOUNG} being struck in the chest and falling backward, {BG_HANOK_INTERIOR}, splattering food and flying dishes, cinematic lighting, masterpiece, photorealistic, historical drama style."
    },
    {
        "name": "Kick_Scene_v2",
        "prompt": f"(Low angle dramatic shot), {IDO_YOUNG} yelling with intense rage, his foot making contact with {YEONHWA_YOUNG}'s chest, {YEONHWA_YOUNG} gasping for air, {BG_HANOK_INTERIOR}, messy floor with spilled snacks, motion blur on the flying dishes, night time, ominous atmosphere."
    }
]

def generate_image(prompt, name, seed):
    print(f"🎨 생성 중: {name} (Seed: {seed})")
    payload = COMMON_PARAMS.copy()
    payload["prompt"] = prompt
    payload["seed"] = seed
    
    try:
        response = requests.post(DRAWTHINGS_URL, json=payload, timeout=200)
        if response.status_code == 200:
            result = response.json()
            image_data = base64.b64decode(result['images'][0])
            file_path = os.path.join(SAVE_DIR, f"{name}.png")
            with open(file_path, "wb") as f:
                f.write(image_data)
            print(f"  ✅ 저장 완료: {file_path}")
            return True
        else:
            print(f"  ❌ API 오류: {response.status_code}")
    except Exception as e:
        print(f"  ❌ 에러: {e}")
    return False

def main():
    print(f"🚀 연화 발로 차는 장면 2장 재생성 시작")
    for i, scene in enumerate(SCENES):
        generate_image(scene["prompt"], scene["name"], seed=9999 + i)
    print(f"\n✅ 완료! {SAVE_DIR} 폴더를 확인하세요.")

if __name__ == "__main__":
    main()

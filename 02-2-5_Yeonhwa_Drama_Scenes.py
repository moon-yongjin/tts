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
SAVE_DIR = os.path.join(OUTPUT_BASE_DIR, f"Yeonhwa_Drama_Scenes_{TIMESTAMP}")
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
IDO_YOUNG = "A 20-year-old Korean nobleman (IDO), fine purple silk hanbok, traditional topknot (SANGTU), furious and cruel facial features."
YEONHWA_YOUNG = "A beautiful 18-year-old Korean woman (YEONHWA), humble cotton hanbok, long dark hair, falling in shock and pain."
FATHER_NOBLE = "An elderly Korean nobleman in white silk inner-wear, face full of despair and shame."
SOLDIERS = "Joseon Dynasty government soldiers (Uigeumbu) in red and black uniforms, holding torches and spears."

BG_HANOK_INTERIOR = "Inside a traditional Korean room, wooden floor, candlelight shadows, spilled food and brass dishes."
BG_HANOK_RUINS = "Burned and ruined traditional Korean house, scorched pillars, smoke and ashes, desolate courtyard."

SCENES = [
    # 발로 차는 장면 (프롬프트 강화)
    {
        "name": "01_KICK_Impact",
        "prompt": f"(Extreme dynamic action shot), {IDO_YOUNG} forcefully kicking {YEONHWA_YOUNG} in the chest, his silk boot mid-air hitting her, {YEONHWA_YOUNG} flying backward with a look of extreme pain and shock, broken porcelain and traditional snacks flying in the air, {BG_HANOK_INTERIOR}, dramatic flickering candlelight, high contrast, intense historical drama."
    },
    {
        "name": "02_KICK_Brutality",
        "prompt": f"(Low angle cinematic shot), focus on the physical impact, {IDO_YOUNG}'s foot making heavy contact with {YEONHWA_YOUNG}'s chest, fabric wrinkling from the force, {YEONHWA_YOUNG} coughing and gasping for air, messy floor with spilled brass dishes, motion blur on fragments, night time, tragic and violent atmosphere."
    },
    # 가문의 몰락 (3장)
    {
        "name": "03_FALL_Raid",
        "prompt": f"(Chaotic wide shot), A grand traditional Korean villa being raided by {SOLDIERS}, soldiers breaking the main wooden gate with torches, frantic family members running in white clothes, smoke and glowing ash in the air, ominous night, historical tragedy."
    },
    {
        "name": "04_FALL_Arrest",
        "prompt": f"(Dramatic focus), {FATHER_NOBLE} being dragged away in heavy wooden neck shackles (KAL) by {SOLDIERS}, soldiers surrounding him with torches, {IDO_YOUNG} hiding behind a scorched pillar in pure terror and tears, high contrast lighting, cinematic close-up."
    },
    {
        "name": "05_FALL_Desolation",
        "prompt": f"(Poetic wide shot), The once grand traditional Korean house now in complete ruins, black scorched wooden frame remains, abandoned and silent courtyard, gray cloudy sky, lonely and desolate mood, post-disaster atmosphere, 8k resolution."
    }
]

def generate_image(prompt, name, seed):
    print(f"🎨 생성 중: {name} (Seed: {seed})")
    payload = COMMON_PARAMS.copy()
    payload["prompt"] = prompt + ", (masterpiece, high quality, realistic skin texture, photorealistic, cinematic lighting)"
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
    print(f"🚀 연화 발차기 & 가문 몰락 장면 생성 시작")
    for i, scene in enumerate(SCENES):
        generate_image(scene["prompt"], scene["name"], seed=3000 + i)
    print(f"\n✅ 완료! {SAVE_DIR} 폴더를 확인하세요.")

if __name__ == "__main__":
    main()

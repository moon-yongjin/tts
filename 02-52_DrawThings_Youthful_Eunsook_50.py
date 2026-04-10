import json
import requests
import time
import os
import base64
import random

# [설정]
DRAW_THINGS_URL = "http://127.0.0.1:7860" 
TIMESTAMP = time.strftime('%m%d_%H%M')
DOWNLOADS_DIR = f"/Users/a12/Downloads/Eunsook_Youthful_50_{TIMESTAMP}"

if not os.path.exists(DOWNLOADS_DIR):
    os.makedirs(DOWNLOADS_DIR)

def check_and_start_draw_things():
    check_app = os.popen('pgrep -x "Draw Things"').read().strip()
    if not check_app:
        os.system('open -a "Draw Things"')
        time.sleep(10)
    try:
        requests.get(f"{DRAW_THINGS_URL}/sdapi/v1/options", timeout=2)
        return True
    except:
        return False

def generate_eunsook_variant(index, background_desc, pose_desc, filename_prefix):
    filename = f"{filename_prefix}_{index:02d}.png"
    
    # [동안 보정] 모델급(글래머) 배제하되, 52세->40대 후반 느낌의 깨끗한 피부 연출
    base_prompt = "A high-quality realistic photo of a normal ordinary late 40s Korean woman looking youthful for her age, sleek smooth skin, well-maintained modest complexion, neat short bob haircut, mild graceful facial features, natural ordinary body proportions, wearing neat modest casual daily clothes"
    
    style_prompt = "candid camera, raw photography style, natural daylight, photorealistic"

    payload = {
        "prompt": f"{base_prompt}, {pose_desc}, {background_desc}, {style_prompt}",
        "negative_prompt": "(wrinkles:1.4), (aged:1.4), grandma look, sagging skin, old, airbrushed, doll face, 3d, cg, naked, heavy makeup, sexy, voluptuous",
        "steps": 6,
        "width": 720,
        "height": 1280,
        "seed": -1,
        "model": "z_image_turbo_1.0_q8p.ckpt",
        "guidance_scale": 1.0,
        "sampler": "Euler A AYS",
        "shift": 3.0,
        "sharpness": 6,
        "seed_mode": "Scale Alike"
    }
    
    try:
        response = requests.post(f"{DRAW_THINGS_URL}/sdapi/v1/txt2img", json=payload, timeout=600)
        if response.status_code == 200:
            data = response.json()
            if "images" in data:
                filepath = os.path.join(DOWNLOADS_DIR, filename)
                with open(filepath, "wb") as f:
                    f.write(base64.b64decode(data["images"][0]))
                print(f"  ✅ [{index:02d}/50] {filename_prefix} 저장 완료!")
                return True
        print(f"  ❌ [{index:02d}/50] {filename_prefix} 실패: {response.status_code}")
    except Exception as e:
        print(f"  ❌ 드로띵 연결 오류: {e}")
    return False

if __name__ == "__main__":
    check_and_start_draw_things()

    # 다양성을 위한 10가지 포즈 및 배경 조합
    COMBOS = [
        ("standing in a clean modern kitchen, holding a recipe book", "standing near a sink"),
        ("sitting at a cozy indoor cafe with a table lamp", "sipping from a mug with a gentle smile"),
        ("walking calmly along a quiet neighborhood street in afternoon", "walking posture with a shopping bag"),
        ("sitting on an outdoor wooden park bench, peaceful gaze", "resting with legs together"),
        ("standing in front of a neat traditional marketplace stall", "arranging colorful plates or items"),
        ("reading a book in a sunlit cozy living room sofa", "holding eyeglasses with focus look"),
        ("entering a warm bookstore doorway, looking inside warmly", "soft smile expression"),
        ("standing outside a red-brick wall, looking at the camera", "casual standing pose"),
        ("walking near a riverside walking trail with greenery preset", "walking naturally forward"),
        ("sitting near a sun-drenched balcony window, serene vibe", "thoughtful graceful look")
    ]

    print("🎬 '박은숙 동안 보정 디자인 + 50장 연쇄 배리에이션' 생성을 시작합니다.")
    
    # 10개 세트를 5회씩 반복하여 총 50장 생성
    count = 1
    for i in range(5): 
        for pose_desc, bg_desc in COMBOS:
            generate_eunsook_variant(count, bg_desc, pose_desc, "Eunsook_Youthful")
            time.sleep(1)
            count += 1

    print(f"\n✨ [생성 완료] 총 50장 렌더링 끝!")
    print(f"📍 저장 위치: {DOWNLOADS_DIR}")
    os.system(f"open {DOWNLOADS_DIR}")

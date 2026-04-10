import json
import requests
import time
import os
import base64

# [설정]
DRAW_THINGS_URL = "http://127.0.0.1:7860" 
TIMESTAMP = time.strftime('%m%d_%H%M')
DOWNLOADS_DIR = f"/Users/a12/Downloads/Late30s_Mom_BigBust_{TIMESTAMP}"

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

def generate_mom(scene_num, prompt_text, filename_prefix):
    filename = f"{filename_prefix}_{scene_num}.png"
    
    # 공통 베이스: 160cm, 55kg, 30대 후반의 현실적인 체형, 단발머리(short bob)와 큰 가슴(large heavy bust)
    base_prompt = "A realistic ordinary late 30s Korean mother, looking like a real mom with one child, 160cm tall, 55kg weight, large heavy bust, big voluptuous breasts, chic short bob haircut, slightly soft but natural body shape, realistic normal beauty, bare minimal makeup, subtle wrinkles, realistic uneven skin texture, authentic everyday life"
    
    payload = {
        "prompt": f"{base_prompt}, {prompt_text}, soft natural lighting, RAW photo, 35mm lens, highly detailed photograph",
        "negative_prompt": "plastic surgery face, perfect flawless skin, overly beautiful, model, unnatural proportions, heavy makeup, sexy clothing, anime, 3d, nsfw, flat chest, long hair",
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
    
    print(f"🚀 [Draw Things] {filename_prefix} 생성 중...")
    try:
        response = requests.post(f"{DRAW_THINGS_URL}/sdapi/v1/txt2img", json=payload, timeout=600)
        if response.status_code == 200:
            data = response.json()
            if "images" in data:
                filepath = os.path.join(DOWNLOADS_DIR, filename)
                with open(filepath, "wb") as f:
                    f.write(base64.b64decode(data["images"][0]))
                print(f"  ✅ {filename_prefix} 저장 완료! -> {filepath}")
                return True
        print(f"  ❌ {filename_prefix} 대기 시간 초과 또는 실패: {response.status_code}")
    except Exception as e:
        print(f"  ❌ 드로띵 연결 오류: {e}")
    return False

if __name__ == "__main__":
    check_and_start_draw_things()

    # 1. 집 거실에서 편안한 홈웨어 차림
    SCENE_1 = "wearing a tight comfortable casual loungewear top and loose cardigan, large bust visible under clothes, standing in a cozy typical Korean apartment living room, warm indoor lighting, holding a coffee mug"

    # 2. 동네 마트 장보기
    SCENE_2 = "wearing a slightly tight comfortable sweater emphasizing large breasts and casual straight jeans, carrying a reusable grocery bag, standing in an aisle of a local Korean supermarket, messy short bob hair, bright fluorescent lights"

    # 3. 유치원/어린이집 하원 마중 (놀이터)
    SCENE_3 = "wearing a practical lightweight open beige jacket and tight t-shirt showing big bust, sneakers, waiting next to an apartment playground, looking gently forward, afternoon sunlight, wind slightly blowing her short bob hair"

    # 4. 동네 카페테라스 브런치 차림
    SCENE_4 = "sitting at a neighborhood cafe table, wearing a simple modest tight knit dress focusing on heavy bust, looking natural and slightly tired but warm smile, neat short bob haircut"

    # 5. 주방에서 저녁 준비
    SCENE_5 = "wearing an apron tied tightly over a simple plain t-shirt emphasizing large prominent breasts, standing in a domestic Korean kitchen, checking a recipe on her phone, slightly unkempt short bob hair, realistic kitchen background"

    SCENES = [
        (SCENE_1, "LivingRoom_Homewear"),
        (SCENE_2, "Supermarket_Casual"),
        (SCENE_3, "Playground_Pickup"),
        (SCENE_4, "Cafe_Rest"),
        (SCENE_5, "Kitchen_Cooking")
    ]

    print("🎬 '현실적인 30대 후반 미시(큰가슴+단발버전)' 5가지 일상 생성 시작!")
    for i, (p, name) in enumerate(SCENES):
        generate_mom(i+1, p, name)

    print(f"\n✨ [생성 완료] 5장 렌더링 끝!")
    print(f"📍 저장 위치: {DOWNLOADS_DIR}")
    os.system(f"open {DOWNLOADS_DIR}")

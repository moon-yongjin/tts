import json
import requests
import time
import os
import base64

# [설정]
DRAW_THINGS_URL = "http://127.0.0.1:7860" 
TIMESTAMP = time.strftime('%m%d_%H%M')
DOWNLOADS_DIR = f"/Users/a12/Downloads/Digicam_Poses_{TIMESTAMP}"

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

def generate_cam_pose(scene_num, pose_text, filename_prefix):
    filename = f"{filename_prefix}_{scene_num}.png"
    
    # 베이스: 5번 이미지의 30대 후반 미시 + 큰 가슴 + 단발머리 + 주방 배경 
    base_prompt = "A realistic ordinary late 30s Korean mother, 160cm tall, 55kg weight, large heavy bust, big voluptuous breasts, chic short bob haircut, slightly soft natural body shape, realistic normal beauty, bare minimal makeup, subtle wrinkles, wearing an apron tied tightly over a simple plain t-shirt emphasizing large prominent breasts, standing in a domestic Korean kitchen, short bob hair"
    
    # 사용자가 고른 3번 스타일 (빈티지 디카 플래시)
    style_prompt = "captured on a vintage 2000s digital camera with heavy flash on, overexposed highlights, flash glare on skin, retro digicam cyber aesthetic"

    payload = {
        "prompt": f"{base_prompt}, {pose_text}, {style_prompt}, casual indoor photo",
        "negative_prompt": "plastic surgery face, perfect flawless skin, overly beautiful, model, unnatural proportions, heavy makeup, sexy clothing, anime, 3d, nsfw, long hair",
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
        print(f"  ❌ {filename_prefix} 실패: {response.status_code}")
    except Exception as e:
        print(f"  ❌ 드로띵 연결 오류: {e}")
    return False

if __name__ == "__main__":
    check_and_start_draw_things()

    # 10가지 다양한 포즈 어레이
    POSES = [
        ("leaning back against the kitchen counter looking directly at camera", "Leaning_Back"),
        ("looking back over shoulder with a warm smile while holding a frying pan", "Over_Shoulder"),
        ("chopping vegetables with hands in frame, head tilted slightly, focused", "Chopping_Veg"),
        ("sitting at the kitchen table, resting chin on hand and looking thoughtful", "Sitting_Table"),
        ("holding a spatula and tasting soup from a spoon with eyes closed slightly", "Tasting_Soup"),
        ("reaching up to a high kitchen cabinet with both arms, body stretched", "Reaching_High"),
        ("wiping a drop of water from her cheek with the back of her hand, candid", "Wiping_Cheek"),
        ("tying the apron string behind her back looking natural", "Tying_Apron"),
        ("resting on a high bar stool in the kitchen looking relaxed with legs crossed", "Stool_Resting"),
        ("candidly laughing while checking a simmering pot on the stove", "Laughing_Cooking")
    ]

    print("🎬 '디카 플래시 10종 포즈 연쇄 생성' 가동을 시작합니다.")
    for i, (p, name) in enumerate(POSES):
        generate_cam_pose(i+1, p, name)

    print(f"\n✨ [생성 완료] 10장 포즈 렌더링 끝!")
    print(f"📍 저장 위치: {DOWNLOADS_DIR}")
    os.system(f"open {DOWNLOADS_DIR}")

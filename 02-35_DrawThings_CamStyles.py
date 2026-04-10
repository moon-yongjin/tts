import json
import requests
import time
import os
import base64

# [설정]
DRAW_THINGS_URL = "http://127.0.0.1:7860" 
TIMESTAMP = time.strftime('%m%d_%H%M')
DOWNLOADS_DIR = f"/Users/a12/Downloads/Mom_CamStyles_{TIMESTAMP}"

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

def generate_cam(scene_num, prompt_text, filename_prefix):
    filename = f"{filename_prefix}_{scene_num}.png"
    
    # 베이스: 5번 이미지의 30대 후반 미시 + 큰 가슴 + 단발머리 + 주방 배경 고정
    base_prompt = "A realistic ordinary late 30s Korean mother, 160cm tall, 55kg weight, large heavy bust, big voluptuous breasts, chic short bob haircut, slightly soft natural body shape, realistic normal beauty, bare minimal makeup, subtle wrinkles, wearing an apron tied tightly over a simple plain t-shirt emphasizing large prominent breasts, standing in a domestic Korean kitchen, checking a recipe on her phone, short bob hair"
    
    payload = {
        "prompt": f"{base_prompt}, {prompt_text}",
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
    
    print(f"🚀 [Draw Things] {filename_prefix} 카메라 연출 생성 중...")
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

    # 1. 아이폰 15 프로 촬영 (대중적인 SNS 셀카/스캔 느낌)
    CAM_1 = "captured on iPhone 15 Pro, smartphone camera aesthetic, TikTok video frame look, natural indoor overhead lighting, slightly imperfect lens flare, casual photo"

    # 2. 파파라치/캔디드 스냅샷 (주변에서 몰래 찍어준 듯한 자연스러움)
    CAM_2 = "candid snapshot, candid raw photography, slight motion blur, unposed natural moment, captured through a doorway looking into the kitchen, realistic action shot"

    # 3. 빈티지 디카 플래시샷 (Y2K 디카 플래시 감성)
    CAM_3 = "captured on a vintage 2000s digital camera with heavy flash on, overexposed highlights, flash glare on skin, retro digicam cyber aesthetic, nostalgic vibe"

    # 4. 소니 미러리스 브이로그 샷 (깔끔한 크리에이터 구도)
    CAM_4 = "Shot on Sony Alpha mirrorless camera with 24mm lens for vlog setup, bokeh blurred kitchen background, clean crisp light balance, professional content creator video look"

    # 5. 폴라로이드 플래시 샷 (폴라로이드 고유의 필름 느낌)
    CAM_5 = "vintage polaroid flash photography with square frame border effect, instant film print look, flash light reflection, warm faded cinematic film colors"

    CAMS = [
        (CAM_1, "iPhone_Style"),
        (CAM_2, "Candid_Snap"),
        (CAM_3, "Digicam_Flash"),
        (CAM_4, "Mirrorless_Vlog"),
        (CAM_5, "Polaroid_Vintage")
    ]

    print("🎬 '주방 미시 캐릭터' 5개 카메라 촬영 연쇄 생성을 시작합니다.")
    for i, (p, name) in enumerate(CAMS):
        generate_cam(i+1, p, name)

    print(f"\n✨ [생성 완료] 5장 카메라 연출 렌더링 끝!")
    print(f"📍 저장 위치: {DOWNLOADS_DIR}")
    os.system(f"open {DOWNLOADS_DIR}")

import json
import requests
import time
import os
import base64

# [설정]
DRAW_THINGS_URL = "http://127.0.0.1:7860" 
TIMESTAMP = time.strftime('%m%d_%H%M')
DOWNLOADS_DIR = f"/Users/a12/Downloads/Story_Cast_{TIMESTAMP}"

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

def generate_casting(scene_num, char_info, filename_prefix):
    filename = f"{filename_prefix}_{scene_num}.png"
    
    # [일반인 모드] 모델급 외모, 연예인 성향, 특정 신체 부위 강조를 완전 투입 배제
    base_prompt = "A high-quality realistic portrait photo of a normal ordinary Korean person, natural lighting, candid photo, average body type, realistic weights, modest ordinary clothes, captured on a real digital camera"
    
    style_prompt = "authentic photo, raw style, 8k resolution"

    payload = {
        "prompt": f"{char_info}, {base_prompt}, {style_prompt}",
        "negative_prompt": "perfect doll face, plastic surgery, model, glamour, fit body, voluptuous, large bust, unrealistic proportions, anime, 3d, airbrushed, naked",
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
    
    print(f"🚀 [Draw Things] 조연/주연 캐스팅-{scene_num} ({filename_prefix}) 생성 중...")
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

    # 등장 인물 캐스팅 카드 (6종)
    CAST = [
        # 1. 박은숙 (주인공, 52세)
        ("A 52-year-old Korean woman, modest graceful ordinary face, clean short bob haircut, wearing casual domestic clothes, standing warmly", "01_Main_Eunsook"),
        
        # 2. 정태 (전남편, 50대)
        ("A middle-aged 50s Korean man, slightly unkempt hair, looking tired and aged, wearing a casual gray jumper, rumpled regular look", "02_ExHusband_Jungtae"),
        
        # 3. 미영 (절친/절도녀, 50대)
        ("A middle-aged 50s Korean woman, wearing heavy makeup, curled highlighted hair, holding an arrogant slight smirk expression, wearing slightly tacky clothes", "03_Friend_Miyoung"),
        
        # 4. 옆집 할머니 (70대)
        ("An elderly 70s Korean grandmother, kind warm wrinkles, silver gray hair tied back, wearing a traditional flowery fleece vest", "04_Granny_Neighbor"),
        
        # 5. 아들 (20대 후반)
        ("A 28-year-old young Korean man, neat normal haircut, wearing a plain dark hoodie and jeans, supportive warm look", "05_Son"),
        
        # 6. 현우 (새 사랑, 50대)
        ("A kind-hearted 50s Korean man, wearing reading glasses with smooth intellect frame, clean ironed shirt, looks like a quiet bookstore owner", "06_NewLover_Hyunwoo")
    ]

    print("🎬 대본의 모든 '일반 사연 맞춤' 등장인물들 연쇄 캐스팅 렌더링을 시작합니다.")
    for i, (p, name) in enumerate(CAST):
        generate_casting(i+1, p, name)
        time.sleep(1)

    print(f"\n✨ [생성 완료] 등장인물 6종 렌더링 끝!")
    print(f"📍 저장 위치: {DOWNLOADS_DIR}")
    os.system(f"open {DOWNLOADS_DIR}")

import json
import requests
import time
import os
import base64

# [설정]
DRAW_THINGS_URL = "http://127.0.0.1:7860" 
TIMESTAMP = time.strftime('%m%d_%H%M')
DOWNLOADS_DIR = f"/Users/a12/Downloads/Eunsook_Shorts_{TIMESTAMP}"

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

def generate_scene(scene_num, pose_text, filename_prefix):
    filename = f"{filename_prefix}_{scene_num}.png"
    
    # [동안보정 고정] 30대 후반~40대 초반 같은 동안 페이스 + 글래머 체형 고정
    base_prompt = "A high-quality photo of a 160cm tall attractive late 30s fit Korean woman, looking extremely young for age, smooth youthful skin with well-maintained complexion, chic short bob haircut, voluptuous heavy bust, thick round hips with nice figure, beautiful face, soft features"
    
    style_prompt = "candid camera captures, raw photography, cinematic atmosphere, 8k resolution, photorealistic"

    payload = {
        "prompt": f"{base_prompt}, {pose_text}, {style_prompt}",
        "negative_prompt": "(wrinkles:1.4), (aged:1.4), grandma look, sagging skin, old, airbrushed, 3d, cg, naked, blur, duplicate",
        "steps": 6,
        "width": 720,
        "height": 1280,
        "seed": -1, # 연쇄 생성을 위해 일단 랜덤
        "model": "z_image_turbo_1.0_q8p.ckpt",
        "guidance_scale": 1.0,
        "sampler": "Euler A AYS",
        "shift": 3.0,
        "sharpness": 6,
        "seed_mode": "Scale Alike"
    }
    
    print(f"🚀 [Draw Things] 쇼츠 씬-{scene_num} ({filename_prefix}) 생성 중...")
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

    # 단축 대본 씬 구성 (8종)
    SCENES = [
        # 1. 헌신/피로 (집 안에서 주방일)
        ("wearing a humble kitchen apron, looking exhausted and tired, sitting at a simple wooden dining table in a small house, cleaning spices", "01_Exhausted_Devotion"),
        
        # 2. 이혼 통보 (슬픔/충격)
        ("sitting in a single chair, crying with weeping eyes holding a tissue, dark cinematic lighting, lonely atmosphere", "02_Divorce_Sadness"),
        
        # 3. 옆집 할머니의 칭찬 (희망)
        ("standing in a doorway, looking surprised with bright widened eyes, holding an plates of kimchi, warm backlighting", "03_Surprised_Hope"),
        
        # 4. 반찬가게 대박 (자신감/미소)
        ("standing proudly in front of a market stall with Haneunsook Banchan sign, wearing a neat white apron and shirt, smiling confidently, vibrant market colors", "04_Proud_Store_Owner"),
        
        # 5. 아들과의 재회
        ("holding hands with a young man in his late 20s, warm emotional gaze, supportive touch, calm and cozy indoor backdrops", "05_Son_Reunion"),
        
        # 6. 복수 준비 (지적인 집중)
        ("wearing reading glasses, looking focused at accurate numbers on banking ledger papers at a neat office desk, holding a pen", "06_Bookkeeping_Focus"),
        
        # 7. 승리 (당당함/커리어우먼)
        ("standing elegantly in a modern bright office room holding report folders with a small victorious calm smile", "07_Victorious_Stance"),
        
        # 8. 행복한 결말 (현우와의 연애/산책)
        ("smiling brightly with happy expression, holding hands with a gentle-looking man near a quiet bookstore alleyway in afternoon sunlight", "08_Happy_Ending")
    ]

    print("🎬 단축 대본 기반 '세로형 쇼츠 시퀀스 8종' 생성을 시작합니다.")
    for i, (p, name) in enumerate(SCENES):
        generate_scene(i+1, p, name)
        time.sleep(2) # 안정적 연속 트리거

    print(f"\n✨ [생성 완료] 쇼츠용 8단 렌더링 끝!")
    print(f"📍 저장 위치: {DOWNLOADS_DIR}")
    os.system(f"open {DOWNLOADS_DIR}")

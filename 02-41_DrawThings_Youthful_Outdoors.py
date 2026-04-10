import json
import requests
import time
import os
import base64

# [설정]
DRAW_THINGS_URL = "http://127.0.0.1:7860" 
TIMESTAMP = time.strftime('%m%d_%H%M')
DOWNLOADS_DIR = f"/Users/a12/Downloads/KnitDress_Youthful_{TIMESTAMP}"

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
    
    # [수정] 동안(Youthful) 키워드 적극 투입, 주름/노화 관련 단어 제거
    base_prompt = "A full body shot of realistic ordinary late 30s Korean mother, looking young-looking for her age, youthful beautiful face, well-maintained smooth skin, glowing complexion, beautiful distinct features, 160cm tall, 55kg weight, large heavy bust, big voluptuous breasts, chic short bob haircut, slightly soft natural figure, wearing a tight low-cut knit sweater dress revealing subtle cleavage, standing on an outdoor street"
    
    style_prompt = "candid raw photography, captured on a vintage digital camera with flash on, slightly motion blurred walk, authentic street step, casual photo"

    payload = {
        "prompt": f"{base_prompt}, {pose_text}, {style_prompt}",
        # [네거티브] 주름(wrinkles), 나이듦(aged, old) 가중치 대폭 강화 
        "negative_prompt": "(wrinkles:1.5), (aged:1.5), old face, grandma, mature look, sagging skin, plastic surgery face, perfect flawless airbrushed skin, overly beautiful, model, heavy makeup, anime, 3d, naked",
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
    
    print(f"🚀 [Draw Things] {filename_prefix} (동안보정) 생성 중...")
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

    # 10가지 야외 전신 시퀀스 (동일 세팅으로 퀄리티 비교용)
    SCENES = [
        ("walking elegantly down a quiet residential sidewalk in the afternoon", "Walking_Sidewalk"),
        ("standing in a neighborhood park on a pathway with autumn leaves in background", "Park_Autumn"),
        ("walking near a modern architectural building glass wall with city reflections", "Glass_Wall_Walk"),
        ("crossing a pedestrian crosswalk stripe marking in a small town center", "Crosswalk_Walking"),
        ("standing in front of a cozy neighborhood red brick cafe entrance", "Cafe_Entrance"),
        ("walking down a flight of outdoor outdoor concrete stairs", "Stairs_Descent"),
        ("standing near a riverside park jogging trail, afternoon sunlight", "Riverside_Path"),
        ("sitting down on an outdoor park wooden bench, looking thoughtful", "Bench_Sitting"),
        ("waiting at a modern glass-backed bus stop shelter, casual relaxed pose", "BusStop_Waiting"),
        ("entering a neighborhood flower shop doorway, looking inside with a style", "Florist_Entry")
    ]

    print("🎬 '동안 보정 + 10개 야외 전신' 연쇄 생성을 시작합니다.")
    for i, (p, name) in enumerate(SCENES):
        generate_cam_pose(i+1, p, name)

    print(f"\n✨ [생성 완료] 10장 동안 렌더링 끝!")
    print(f"📍 저장 위치: {DOWNLOADS_DIR}")
    os.system(f"open {DOWNLOADS_DIR}")

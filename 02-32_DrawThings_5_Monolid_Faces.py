import json
import requests
import time
import os
import base64

# [설정]
DRAW_THINGS_URL = "http://127.0.0.1:7860" 
TIMESTAMP = time.strftime('%m%d_%H%M')
DOWNLOADS_DIR = f"/Users/a12/Downloads/Monolid_Faces_{TIMESTAMP}"

if not os.path.exists(DOWNLOADS_DIR):
    os.makedirs(DOWNLOADS_DIR)

def check_and_start_draw_things():
    check_app = os.popen('pgrep -x "Draw Things"').read().strip()
    if not check_app:
        os.system('open -a "Draw Things"')
        time.sleep(10)
    for _ in range(5):
        try:
            requests.get(f"{DRAW_THINGS_URL}/sdapi/v1/options", timeout=2)
            return True
        except:
            time.sleep(5)
    return False

def generate_face(scene_num, prompt_text, filename_prefix):
    filename = f"{filename_prefix}_{scene_num}.png"
    payload = {
        # [수정] 얼굴 확대(Close-up)와 자연스러운 조광에 집중
        "prompt": f"{prompt_text}, natural light makeup, bare face look, soft cinematic studio lighting, highly detailed skin texture, pores, high photorealism, RAW format shot on 85mm portrait lens",
        # [수정/네거티브] 쌍꺼풀(double eyelid) 및 성형 느낌(plastic face) 차단
        "negative_prompt": "(double eyelid:1.5), (thick double eyelid:1.5), plastic surgery face, unnatural nose, text, watermark, low quality, blurry, distorted, anime, cartoon, illustration, drawing, nsfw",
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
    
    print(f"🚀 [Draw Things] {filename_prefix} 얼굴 생성 중...")
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

    # [수정] '무쌍꺼풀' 얼굴 클로즈업 5가지 타입 설정
    BASE = "Close up portrait of a attractive 20s Korean woman, unique beauty mask, realistic skin pores and texture"

    # 1. 고양이상 무쌍 (날렵, 카리스마) - [시크한 숏단발]
    FACE_1 = f"{BASE}, sharp attractive monolid eyes with slight upward tilt, charismatic cat-like gaze, elegant jawline, sleek short bob with sharp-cut bangs"

    # 2. 강아지상 무쌍 (둥글, 귀여움, 청초) - [긴 웨이브]
    FACE_2 = f"{BASE}, large round monolid eyes with soft gentle containing look, cute pure expression, light natural smile, soft lighting, long wavy hair with soft airy curtain bangs"

    # 3. 모델형 하이엔드 무쌍 (동양적 개성파) - [하이 포니테일]
    FACE_3 = f"{BASE}, unique high fashion model mask, high cheekbones, intense deep monolid gaze, avant-garde facial structure, high contrast, high tight sleek ponytail"

    # 4. 청순 순둥이 무쌍 (무보정 자연미) - [내추럴 똥머리]
    FACE_4 = f"{BASE}, gentle monolid eyes, innocent clear gaze, purely natural face without any makeup, authentic skin glow, natural loose bun with slight messy tendrils"

    # 5. 도회적/시크 무쌍 (고급스럽고 깔끔) - [중단발 생머리]
    FACE_5 = f"{BASE}, sophisticated long monolid eyes, calm deep expression, sleek modern aesthetic, shoulder-length straight hair with a clean side part"

    FACES = [
        (FACE_1, "Cat_Monolid"),
        (FACE_2, "Puppy_Monolid"),
        (FACE_3, "Model_Monolid"),
        (FACE_4, "Innocent_Monolid"),
        (FACE_5, "Sleek_Monolid")
    ]

    print("🎬 '100% 무쌍꺼풀 단독 얼굴' 5명 연쇄 생성을 시작합니다.")
    for i, (p, name) in enumerate(FACES):
        generate_face(i+1, p, name)

    print(f"\n✨ [얼굴팩 제작완료] 5장 생성 시도 마침!")
    print(f"📍 저장 위치: {DOWNLOADS_DIR}")
    os.system(f"open {DOWNLOADS_DIR}")

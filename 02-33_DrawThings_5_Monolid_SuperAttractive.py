import json
import requests
import time
import os
import base64

# [설정]
DRAW_THINGS_URL = "http://127.0.0.1:7860" 
TIMESTAMP = time.strftime('%m%d_%H%M')
DOWNLOADS_DIR = f"/Users/a12/Downloads/Super_Attractive_Monolid_{TIMESTAMP}"

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

def generate_face_pack(scene_num, prompt_text, filename_prefix):
    filename = f"{filename_prefix}_{scene_num}.png"
    payload = {
        "prompt": f"{prompt_text}, highly attractive and charming look, natural light makeup, clear facial lines, soft cinematic lighting, ultra-detailed skin texture with pores, realistic eyes, 85mm portrait, cinematic",
        # [네거티브] 쌍꺼풀(double eyelid) 차단 가중치 및 노화/성형 차단
        "negative_prompt": "(double eyelid:1.5), (thick double eyelid:1.5), plastic face, bloated cheeks, aged face, ugly, symmetrical artificial face, extra fingers, text, watermark, cartoon",
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
    
    print(f"🚀 [Draw Things] {filename_prefix} 매력 무쌍 생성 중...")
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

    # [수정] 피드백에 맞춰 한국인이 가장 매력적이라 평가하는 무쌍 연예인상 프롬프트 구성
    # 1. 김고은/김다미 스타일 (청초, 순수, 매력적 눈웃음)
    STYLE_1 = "Close up portrait of a highly attractive 20s Korean woman, soft round monolid eyes with clear charming aegyo-sal, beautiful gentle quiet smile, innocent natural faceResembling Kim Go-eun, thick straight black hair"

    # 2. 예지/슬기 스타일 (시크한 고양이상, 카리스마)
    STYLE_2 = "Close up portrait of a gorgeous 20s Korean girl, sharp feline monolid eyes with attractive outward tilt, charismatic deep confident gaze, V-line face, resembling ITZY Yeji, sleek high ponytail"

    # 3. 모델 박소담 스타일 (개성형, 청순 오묘)
    STYLE_3 = "Close up portrait of an elegant 20s Korean model, unique distinctive monolid eyes with warm expressive pupils, clear eye line, beautiful harmonious profile, resembling Park So-dam, chic short bob with bangs"

    # 4. 전통 동양미 무쌍 (기품 있고 고급스러운 마스크)
    STYLE_4 = "Close up portrait of a beautiful 20s Korean lady with traditional oriental large monolid eyes, dignified elegant facial structure, harmonious distinct features, highly charming and attractive model mask, natural long wavy hair"

    # 5. 트렌디 힙 무쌍 (풋풋한 과즙상, 동양형 미인)
    STYLE_5 = "Close up portrait of a gorgeous 20s Korean woman with bright round monolid eyes, cute cheek volume with bright attractive cheerful look, aesthetic trendy beauty face, shoulder-length straight hair with clean side part"

    FACES = [
        (STYLE_1, "KimGoEun_Style"),
        (STYLE_2, "Yeji_Cat_Style"),
        (STYLE_3, "ParkSoDam_Style"),
        (STYLE_4, "Traditional_Beauty"),
        (STYLE_5, "Trendy_Hip_Style")
    ]

    print("🎬 '한국 연예인형 매력 무쌍' 5종 생성을 시작합니다.")
    for i, (p, name) in enumerate(FACES):
        generate_face_pack(i+1, p, name)

    print(f"\n✨ [제작완료] 5장 연쇄 생성 완료!")
    print(f"📍 저장 위치: {DOWNLOADS_DIR}")
    os.system(f"open {DOWNLOADS_DIR}")

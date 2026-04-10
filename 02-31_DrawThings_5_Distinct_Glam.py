import json
import requests
import time
import os
import base64

# [설정]
DRAW_THINGS_URL = "http://127.0.0.1:7860" 
TIMESTAMP = time.strftime('%m%d_%H%M')
DOWNLOADS_DIR = f"/Users/a12/Downloads/Glamour_5_Characters_{TIMESTAMP}"

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

def generate_char(scene_num, prompt_text, filename_prefix):
    filename = f"{filename_prefix}_{scene_num}.png"
    payload = {
        "prompt": f"{prompt_text}, natural makeup, bare face look, soft cinematic lighting, ultra-detailed textures, realistic lighting, 8k professional photography, film grain",
        "negative_prompt": "heavy makeup, dark eyeliner, dark lips, text, watermark, banner, low quality, blurry, distorted, anime, cartoon, illustration, drawing, extra fingers, messy hands, distorted face, nsfw, naked, bad proportions, bad anatomy",
        "steps": 6,
        "width": 720,
        "height": 1280,
        "seed": -1, # 랜덤성 부여
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

    # [수정] 피드백 반영 "진짜 글래머" 5가지 타입 설정 (S라인, 골반, 피트핏)
    # 1. 필라테스 강사 타입 (유연근육, 넓은 골반, 고관절 발달) - [무쌍 매력상]
    CHAR_1 = "A attractive 20s Korean woman, unique beauty face with elegant monolid eyes, pronounced hourglass figure, wide hips, large round glutes, voluptuous S-line curve, toned slender waist, flexible fit body, wearing tight high-waisted charcoal leggings and a white crop top, stretching gracefully in a mat room"

    # 2. 짐 모델 타입 (탄탄한 피트니스) - [카리스마 고양이상]
    CHAR_2 = "A gorgeous 20s Korean woman with sharp charismatic feline eyes and attractive distinct features, thick-fit thighs, full large hips, pronounced curvature of the glutes, athletic curves, voluptuous build, healthy fit body, wearing sleek black compression workout leggings and a fitted long sleeve shirt, standing next to a indoor window, soft lighting"

    # 3. 모델형 베이글 (슬림속 볼륨) - [청초한 강아지상]
    CHAR_3 = "A tall 20s Korean model, cute distinct soft round facial features with warm cheerful expression, voluptuous proportions, narrow waist with prominent large bottom and full hips, elegant S-line frame, wearing smooth neutral beige leggings and an oversized light cardigan slipping off shoulder, sitting on a high stool in a sunlit loft"

    # 4. 건강미형 슬랜더-글래머 - [동양적 개성파 미인]
    CHAR_4 = "A 20s Korean woman with exotic unique facial structure and deep expressive eyes, RAW photo style with realistic skin texture, athletic hourglass build, voluptuous fit curves, fully curved lower body and large round glutes, wearing dark navy texture yoga pants and a simple tied t-shirt, standing casually on a quiet residential sunset street looking back over shoulder"

    # 5. 소프티 스타일 글래머 - [기품 있고 성숙한 매력]
    CHAR_5 = "A glamorous 20s Korean girl, sophisticated and attractive face with beautiful unique proportions, soft and voluptuous full body curve, full bust and slender fit waist, extremely wide hips and thick full glutes, hourglass proportions, wearing form-fitting smooth lavender yoga leggings and a matching top, relaxing on a simple plush sofa with legs crossed"

    CHARACTERS = [
        (CHAR_1, "Pilates_Instructor"),
        (CHAR_2, "Gym_Model"),
        (CHAR_3, "Tall_Glamour"),
        (CHAR_4, "Street_Hourglass"),
        (CHAR_5, "Soft_Voluptuous")
    ]

    print("🎬 '자연스러운 화장 + 피트니스 S라인' 5개 타입 연쇄 생성을 시작합니다.")
    for i, (p, name) in enumerate(CHARACTERS):
        generate_char(i+1, p, name)

    print(f"\n✨ [제작 완료] 5장 생성 시도 완료!")
    print(f"📍 저장 위치: {DOWNLOADS_DIR}")
    os.system(f"open {DOWNLOADS_DIR}")

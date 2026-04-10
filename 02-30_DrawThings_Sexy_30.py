import json
import requests
import time
import os
import base64
import random

# [설정]
DRAW_THINGS_URL = "http://127.0.0.1:7860" 
TIMESTAMP = time.strftime('%m%d_%H%M')
DOWNLOADS_DIR = f"/Users/a12/Downloads/Sexy_Leggings_Batch_{TIMESTAMP}"

if not os.path.exists(DOWNLOADS_DIR):
    os.makedirs(DOWNLOADS_DIR)

def check_and_start_draw_things():
    """드로띵 앱 상태 확인"""
    print("⏳ [자동화] 드로띵 앱 및 API 서버 상태 확인 중...")
    
    check_app = os.popen('pgrep -x "Draw Things"').read().strip()
    if not check_app:
        print("🚀 드로띵 앱이 꺼져 있어 자동으로 실행합니다...")
        os.system('open -a "Draw Things"')
        time.sleep(10)

    for i in range(5):
        try:
            requests.get(f"{DRAW_THINGS_URL}/sdapi/v1/options", timeout=2)
            print("✅ 드로띵 API 서버가 활성화되어 있습니다.")
            return True
        except:
            print(f"⏳ API 서버 대기 중... ({i+1}/5)")
            time.sleep(5)
    return False

def generate_scene(scene_num, prompt_text, seed_val):
    filename = f"Sexy_Leggings_{scene_num:02d}.png"
    
    payload = {
        # [자연스려운 화장 어필] 자연스러운 무메이크업/라이트메이크업 베이스
        "prompt": f"{prompt_text}, natural makeup, bare face look, soft cinematic, ultra-detailed textures, realistic lighting, 8k professional photography, film grain",
        "negative_prompt": "heavy makeup, dark eyeliner, dark lips, text, watermark, banner, low quality, blurry, distorted, anime, cartoon, illustration, drawing, extra fingers, messy hands, distorted face, nsfw, naked, bad proportions, bad anatomy",
        "steps": 6,          # [요청] 6스텝 
        "width": 720,
        "height": 1280,
        "seed": seed_val,    # [요청] 랜덤하게 (-1)
        "model": "z_image_turbo_1.0_q8p.ckpt",
        "guidance_scale": 1.0,
        "sampler": "Euler A AYS",
        "shift": 3.0,
        "sharpness": 6,
        "seed_mode": "Scale Alike"
    }
    
    print(f"🚀 [Draw Things] Image {scene_num}/30 전송 중...")
    print(f"📝 Prompt: {prompt_text[:60]}...")
    try:
        response = requests.post(f"{DRAW_THINGS_URL}/sdapi/v1/txt2img", json=payload, timeout=600)
        if response.status_code == 200:
            data = response.json()
            if "images" in data:
                filepath = os.path.join(DOWNLOADS_DIR, filename)
                with open(filepath, "wb") as f:
                    f.write(base64.b64decode(data["images"][0]))
                print(f"  ✅ Image {scene_num} 저장 완료! -> {filepath}")
                return True
        print(f"  ❌ Image {scene_num} 실패: {response.status_code}")
    except Exception as e:
        print(f"  ❌ 드로띵 연결 오류: {e}")
    return False

if __name__ == "__main__":
    if not check_and_start_draw_things():
        print("💡 API 서버를 자동으로 켜지 못했습니다. 앱에서 [HTTP API Server -> Start]를 직접 확인해주세요.")

    # [수정] 30가지 테마 프롬프트 구성 (레깅스, 은꼴, 자연스러운 화장)
    BASE_SUBJECT = "A gorgeous 20s Korean woman, curvy glamorous body, natural facial features, light natural makeup, bare face look"
    
    BACKGROUNDS = [
        "inside a sunlit modern Pilates studio with large windows",
        "sitting on a high stool in a sleek minimalist coffee shop",
        "walking outdoors in a quiet luxury residential neighborhood at sunset",
        "relaxing in a cozy sunlit bedroom with simple aesthetic",
        "stretching casually in a bright yoga studio",
        "standing in front of a warm sunlit balcony, soft depth of field",
        "leaning against a modern kitchen island, soft morning light",
        "sitting comfortably on a deep neutral colored plush sofa",
        "standing casually in a modern high-end rooftop garden",
        "relaxing in a sunlit art studio, soft cinematic atmosphere"
    ]

    OUTFITS = [
        "wearing high-waisted smooth fit black workout leggings and a simple white long sleeve top",
        "wearing sleek charcoal grey yoga pants and an oversized casual sweatshirt",
        "wearing tight-fitting soft beige leggings and a matching neutral crop tank top",
        "wearing dark navy compression leggings and a loose fitting grey hoodie",
        "wearing form-fitting deep burgundy sports leggings and a breathable cotton tee",
        "wearing smooth texture lavender leggings and a basic relaxed cardigan",
        "wearing high-rise compression workout pants in olive green",
        "wearing smooth fit tan yoga pants with a stylish clean fit top"
    ]

    POSES = [
        "stretching naturally on a mat, subtle elegant full body profile view",
        "looking away with a gentle quiet smile, leaning slightly",
        "sitting down, tying dark hair up in a ponytail, looking at local lens",
        "looking back over the shoulder while walking slow",
        "relaxing on the floor with legs crossed, casually smiling at the room",
        "bending slightly to stretch arms towards the ceiling, elongated pose",
        "leaning back on a chair cushions in a relaxed posture",
        "holding an elegant pose stretching on one leg, fit posture"
    ]

    # 30개 랜덤 조합 프롬프트 생성
    PROMPTS = []
    used_combinations = set()
    
    while len(PROMPTS) < 30:
        bg = random.choice(BACKGROUNDS)
        outfit = random.choice(OUTFITS)
        pose = random.choice(POSES)
        
        comb = (bg, outfit, pose)
        if comb not in used_combinations:
            used_combinations.add(comb)
            full_prompt = f"{BASE_SUBJECT}, {pose}, {outfit}, {bg}"
            PROMPTS.append(full_prompt)

    # 전체 생성 가동
    print(f"🎬 '6스텝 및 시드 랜덤' 30장 컨셉 생성을 시작합니다.")
    success_count = 0
    for i, p in enumerate(PROMPTS):
        # 복수 생성이라 시드를 랜덤화 시켜야 베레이션이 나옴
        seed_num = random.randint(1, 999999999) 
        if generate_scene(i+1, p, seed_num):
            success_count += 1
    
    print(f"\n✨ [제작 완료] {success_count}/{len(PROMPTS)}장 생성 성공!")
    print(f"📍 저장 위치: {DOWNLOADS_DIR}")
    os.system(f"open {DOWNLOADS_DIR}")

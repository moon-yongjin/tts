import json
import requests
import time
import os
import base64

# ─────────────────────────────────────────────
#  [설정]
# ─────────────────────────────────────────────
DRAW_THINGS_URL = "http://127.0.0.1:7860"
SCRIPT_PATH     = os.path.join(os.path.dirname(__file__), "대본.txt")
TIMESTAMP       = time.strftime('%m%d_%H%M')

# ─────────────────────────────────────────────
#  [사이즈 선택]
# ─────────────────────────────────────────────
def select_size():
    print("\n📐 이미지 사이즈를 선택하세요:")
    print("  1) 세로형  (720 x 1280)  ← 쇼츠 / 릴스 / 틱톡")
    print("  2) 가로형  (1280 x 720)  ← 유튜브 일반")
    print("  3) 정사각  (1024 x 1024) ← 1:1")
    while True:
        choice = input("\n번호를 입력하세요 (1/2/3): ").strip()
        if choice == "1":
            print("✅ 세로형 (720 x 1280) 선택됨")
            return 720, 1280, "portrait"
        elif choice == "2":
            print("✅ 가로형 (1280 x 720) 선택됨")
            return 1280, 720, "landscape"
        elif choice == "3":
            print("✅ 정사각 (1024 x 1024) 선택됨")
            return 1024, 1024, "square"
        else:
            print("❌ 1, 2, 3 중에서 선택해주세요.")

# ─────────────────────────────────────────────
#  [캐릭터 정의] - 며느리(지은) & 시어머니(김 여사)
# ─────────────────────────────────────────────
DAUGHTER_IN_LAW = "A beautiful Korean woman in her 30s, very large breasts, curvy glamorous body, short straight bob hairstyle, wearing glasses, natural face, wearing a baggy white cotton V-neck t-shirt and loose gray cotton pants"
MOTHER_IN_LAW = "A stern elderly Korean woman in her 60s, sharp eyes, perm hair, wearing a kitchen apron over house clothes, pointing finger or looking strict"
KITCHEN = "A modern but realistic Korean apartment kitchen"
LIVING_ROOM = "A cozy Korean living room with a laptop on a table"

# ─────────────────────────────────────────────
#  [프롬프트 매핑] - 02-2의 PROMPTS를 그대로 사용하되 대사만 표정으로 변경
# ─────────────────────────────────────────────
SCENE_PROMPTS = [
    f"Cinematic wide shot of a modern Korean apartment interior, morning light filtering through windows.", # 1 (제목)
    f"{MOTHER_IN_LAW} in small kitchen, shouting angrily with a pointing finger, aggressive expression.", # 2
    f"Extreme close up of {MOTHER_IN_LAW}'s angry face, sharp eyes, yelling, dramatic lighting.", # 3
    f"{DAUGHTER_IN_LAW} cooking at the stove with a frying pan, a gentle stoic smile on her face.", # 4
    f"{DAUGHTER_IN_LAW} looking at the camera, mouth slightly open as if speaking politely, kitchen background.", # 5
    f"Flashback: {DAUGHTER_IN_LAW} in a professional business suit (formal), but same face and glasses, blurred office background.", # 6
    f"A man in a business suit walking out of a front door, waving hand dismissively, blurred background.", # 7
    f"{MOTHER_IN_LAW} nagging, standing behind {DAUGHTER_IN_LAW} who is cleaning the floor.", # 8
    f"Close up of {DAUGHTER_IN_LAW}'s face looking down, subtle hidden smile, long eyelashes behind glasses.", # 9
    f"{MOTHER_IN_LAW} in a dark bedroom, looking at a glowing laptop screen with a shocked face.", # 10
    f"Close up of a laptop screen showing complex green and red stock market candlestick charts and a bank statement UI.", # 11
    f"Extreme close up of a digital bank statement showing '7,200,000,000 KRW' balance, focus on numbers.", # 12
    f"Close up of {MOTHER_IN_LAW}'s face, jaw dropping, eyes wide in total shock, hands on cheeks.", # 13
    f"{DAUGHTER_IN_LAW} walking towards {MOTHER_IN_LAW} holding a white coffee mug, calm and confident expression.", # 14
    f"{DAUGHTER_IN_LAW} explaining with a soft smile, gesturing with one hand, high-end cinematic lighting.", # 15
    f"Extreme close up of {MOTHER_IN_LAW} staring blankly, speechless, mouth slightly open.", # 16
    f"Cinematic portrait of {DAUGHTER_IN_LAW} with holographic stock data and charts floating in the background, professional vibe.", # 17
    f"{DAUGHTER_IN_LAW} smiling warmly, eyes sparkling through glasses, looking at {MOTHER_IN_LAW}.", # 18
    f"{DAUGHTER_IN_LAW} and {MOTHER_IN_LAW} sitting together on a sofa, looking at a tablet screen together, friendly atmosphere.", # 19
    f"{MOTHER_IN_LAW} looking at {DAUGHTER_IN_LAW} with respect, holding her hand, warm emotional scene.", # 20
    f"Blank screen or minimalist artistic shot of a warm home interior.", # 21 (공백 대응)
    f"Close up of {DAUGHTER_IN_LAW} winking at the camera, playful smile, subscribe and like concept.", # 22
    f"Cinematic sunset view from a high-rise Korean apartment window, peaceful ending." # 23
]

# ─────────────────────────────────────────────
#  [대본 파싱]
# ─────────────────────────────────────────────
def load_script_lines():
    if not os.path.exists(SCRIPT_PATH):
        return []
    with open(SCRIPT_PATH, "r", encoding="utf-8") as f:
        return [l.strip() for l in f.readlines() if l.strip()]

# ─────────────────────────────────────────────
#  [앱 확인]
# ─────────────────────────────────────────────
def check_and_start_draw_things():
    check_app = os.popen('pgrep -x "Draw Things"').read().strip()
    if not check_app:
        os.system('open -a "Draw Things"')
        time.sleep(10)
    for i in range(5):
        try:
            requests.get(f"{DRAW_THINGS_URL}/sdapi/v1/options", timeout=2)
            return True
        except:
            time.sleep(5)
    return False

# ─────────────────────────────────────────────
#  [이미지 생성]
# ─────────────────────────────────────────────
def generate_scene(scene_num, prompt_text, width, height, output_dir):
    filename = f"Scene_{scene_num:02d}.png"
    
    # 02-2와 완벽하게 동일한 프롬프트 스타일 (추가 키워드 제거)
    payload = {
        "prompt": f"{prompt_text}, masterpiece, high-end cinematic, ultra-detailed textures, realistic lighting, 8k professional photography, film grain",
        "negative_prompt": "text, watermark, banner, low quality, blurry, distorted, anime, cartoon, illustration, drawing, extra fingers, messy hands, distorted face, nsfw, naked, bad proportions, bad anatomy, subtitles, captions, letters, words",
        "steps": 6,
        "width": width,
        "height": height,
        "seed": 2024,
        "model": "z_image_turbo_1.0_q8p.ckpt",
        "guidance_scale": 1.0,
        "sampler": "Euler A AYS", # 사용자가 지정한 샘플러
        "shift": 3.0,
        "sharpness": 6,
        "seed_mode": "Scale Alike"
    }

    try:
        response = requests.post(f"{DRAW_THINGS_URL}/sdapi/v1/txt2img", json=payload, timeout=600)
        if response.status_code == 200:
            data = response.json()
            if "images" in data:
                filepath = os.path.join(output_dir, filename)
                with open(filepath, "wb") as f:
                    f.write(base64.b64decode(data["images"][0]))
                print(f"✅ Scene {scene_num:02d} 완료")
                return True
    except:
        pass
    return False

if __name__ == "__main__":
    width, height, size_label = select_size()
    output_dir = f"/Users/a12/Downloads/Script_Images_{size_label}_{TIMESTAMP}"
    os.makedirs(output_dir, exist_ok=True)

    if not check_and_start_draw_things():
        exit(1)

    script_lines = load_script_lines()
    for i, prompt in enumerate(SCENE_PROMPTS):
        if i < len(script_lines):
            print(f"[{i+1}/{len(SCENE_PROMPTS)}] {script_lines[i][:30]}...")
        generate_scene(i + 1, prompt, width, height, output_dir)

    print(f"\n✨ 완료: {output_dir}")
    os.system(f"open {output_dir}")

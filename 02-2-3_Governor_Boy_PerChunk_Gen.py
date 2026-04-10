import requests
import json
import base64
import os
import time
import re
from datetime import datetime

# 1. 설정 (기존 02-2-3 세팅 유지)
DRAWTHINGS_URL = "http://127.0.0.1:7860/sdapi/v1/txt2img"
OUTPUT_BASE_DIR = os.path.expanduser("~/Downloads")
TIMESTAMP = datetime.now().strftime("%m%d_%H%M")
SAVE_DIR = os.path.join(OUTPUT_BASE_DIR, f"GovernorBoy_PerChunk_{TIMESTAMP}")
os.makedirs(SAVE_DIR, exist_ok=True)

# 2. 공통 설정 (기존 02-2-3 세팅 유지: Steps 6, CFG 1.0)
COMMON_NEGATIVE = "easynegative, human_low_quality, bad_anatomy, distorted_face, blurry, lowres, text, watermark, signature, modern_clothing, western_features, 3d, render, illustration, simple background"
COMMON_PARAMS = {
    "sampler_name": "Euler A AYS",
    "steps": 6,
    "cfg_scale": 1.0,
    "width": 720,
    "height": 1280,
    "negative_prompt": COMMON_NEGATIVE,
    "seed": 2024,
    "model": "z_image_turbo_1.0_q8p.ckpt",
    "shift": 3.0,
    "sharpness": 6
}

# 3. 캐릭터 및 배경 정의 (원님과 소년 레퍼런스)
GOVERNOR = "A greedy and obese 50-year-old Korean governor (WON-NIM), wearing a bright red silk official robe (Gwanbok), traditional official hat (Samo), arrogant and haughty expression, sitting on a luxurious cushion."
BOY = "A smart 12-year-old Korean boy, clever eyes, simple off-white cotton hanbok, humble but witty vibe, honest facial features."
BG_HANOK_INSIDE = "Luxurious traditional Korean room (Sararangchae), polished wooden floor, sliding paper doors, silk folding screen in background."
BG_MADANG = "Traditional Korean courtyard (Madang), stone floor, sunny daylight, Hanok architecture in background."

def split_chunks(text):
    # 문단 단위(줄바꿈)로 우선 분할
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    return lines

def check_and_start_draw_things():
    """드로띵 앱 상태 확인 및 실행"""
    print("⏳ [자동화] 드로띵 앱 서버 상태 확인 중...")
    check_app = os.popen('pgrep -x "Draw Things"').read().strip()
    if not check_app:
        print("🚀 드로띵 앱 실행 중...")
        os.system('open -a "Draw Things"')
        time.sleep(10)

    for i in range(5):
        try:
            # options 엔드포인트로 체크
            requests.get("http://127.0.0.1:7860/sdapi/v1/options", timeout=2)
            print("✅ 드로띵 API 서버 활성화")
            return True
        except:
            time.sleep(5)
    return False

def get_scene_prompt(idx, chunk_text):
    """대본 순서에 따른 정밀 장면 매핑 (16개 청크 대응)"""
    
    # 01-05: 발단 (내기 제안)
    if idx == 0:
        return f"(Wide shot), {GOVERNOR} sitting on a purple cushion in {BG_HANOK_INSIDE}, {BOY} standing before him, historical drama setting."
    elif idx == 1:
        return f"(Medium shot), {GOVERNOR} speaking arrogantly with a wave of hand, {BOY} listening in {BG_HANOK_INSIDE}."
    elif idx == 2:
        return f"(Close-up), {GOVERNOR}'s eyes full of greed and challenge, arrogant expression, {BG_HANOK_INSIDE}."
    elif idx == 3:
        return f"(Close-up), {BOY} looking troubled, deep in thought, bowing his head lowly, humble but smart eyes."
    elif idx == 4:
        return f"(Action shot), {BOY} kneeling and bowing low on the floor, {GOVERNOR} looking down from his high chair/cushion."
    
    # 06-10: 전개 (소년의 역공)
    elif idx == 5:
        return f"(Medium shot), {BOY} looking up at {GOVERNOR}, historical room details, dramatic lighting."
    elif idx == 6:
        return f"(Close-up), {GOVERNOR} laughing loudly, chin up, winner's attitude, rich historical background."
    elif idx == 7:
        return f"(Medium shot), {BOY} speaking with a subtle smile, {GOVERNOR} becoming intrigued and leaning forward."
    elif idx == 8:
        return f"(Close-up), {BOY} making a witty gesture, explaining his clever idea, smart expression."
    elif idx == 9:
        return f"(Action shot), {GOVERNOR} starting to stand up from his seat, curiosity in his eyes, {BG_HANOK_INSIDE}."
    
    # 11-16: 결말 (승리 및 마무리)
    elif idx == 10:
        return f"(Wide shot), {GOVERNOR} walking out of the Hanok into {BG_MADANG} with confidence, {BOY} following behind."
    elif idx == 11:
        return f"(Medium shot), {GOVERNOR} crossing the high threshold (Mun-teok) to step into the sunny courtyard."
    elif idx == 12:
        return f"(Portrait), {GOVERNOR} standing in {BG_MADANG}, arms on waist, shouting 'Now bring me in!', looking proud."
    elif idx == 13:
        return f"(Reveal shot), {BOY} bowing with a bright witty smile, {GOVERNOR}'s face in the background looking shocked."
    elif idx == 14:
        return f"Ending concept: a traditional Korean scroll or ink wash background with subscribe button icon, calm mood."
    elif idx == 15:
        return f"Final shot: {BOY} and {GOVERNOR} in {BG_MADANG}, sunset, high quality historical setting, the text 'Thank you' vibe."
    
    return f"(Cinematic shot), {GOVERNOR} and {BOY} in a traditional setting."

def generate_image(prompt, name, index, total):
    print(f"🎨 [{index}/{total}] 생성 중: {name}")
    payload = COMMON_PARAMS.copy()
    payload["prompt"] = prompt + ", (masterpiece, high quality, 8k, realistic skin texture, historical setting, high contrast, cinematic lighting)"
    payload["seed"] = 2024 + index
    
    try:
        response = requests.post(DRAWTHINGS_URL, json=payload, timeout=300)
        if response.status_code == 200:
            result = response.json()
            image_data = base64.b64decode(result['images'][0])
            file_path = os.path.join(SAVE_DIR, f"{name}.png")
            with open(file_path, "wb") as f:
                f.write(image_data)
            return True
        else:
            print(f"  ❌ API 오류: {response.status_code}")
    except Exception as e:
        print(f"  ❌ 에러: {e}")
    return False

def main():
    if not check_and_start_draw_things():
        print("❌ 드로띵 API 연결 실패")
        return

    script_path = "/Users/a12/projects/tts/대본.txt"
    if not os.path.exists(script_path):
        print("❌ 대본 파일이 없습니다.")
        return
        
    with open(script_path, "r", encoding="utf-8") as f:
        text = f.read()
    
    chunks = split_chunks(text)
    total = len(chunks)
    print(f"🚀 총 {total}개의 청크 이미지 생성 시작 (저장: {SAVE_DIR})")
    
    for i, chunk in enumerate(chunks):
        prompt = get_scene_prompt(i, chunk)
        name = f"Governor_Boy_Chunk_{i+1:02d}"
        generate_image(prompt, name, i+1, total)

    print(f"\n✅ 완료! {SAVE_DIR} 폴더를 확인하세요.")
    os.system(f"open {SAVE_DIR}")

if __name__ == "__main__":
    main()

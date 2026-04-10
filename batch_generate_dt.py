import json
import requests
import time
import os
import base64
import concurrent.futures
import sys
import re
from glob import glob
from pathlib import Path
from google import genai
from google.genai import types

# Configuration
DRAW_THINGS_URL = "http://127.0.0.1:7860"
DOWNLOADS_DIR = "/Users/a12/Downloads/Script_Scenes_Dynamic"
SCRIPT_FILE = "/Users/a12/projects/tts/대본.txt"
CONFIG_PATH = "/Users/a12/projects/tts/config.json"
USER_DOWNLOADS = str(Path.home() / "Downloads")

def load_gemini_key():
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            config = json.load(f)
            return config.get("Gemini_API_KEY")
    except:
        return None

# Gemini API 설정
GOOGLE_API_KEY = load_gemini_key()
if not GOOGLE_API_KEY:
    print("❌ API Key를 찾을 수 없습니다.")
    exit(1)

client = genai.Client(api_key=GOOGLE_API_KEY)

if not os.path.exists(DOWNLOADS_DIR):
    os.makedirs(DOWNLOADS_DIR)

def check_and_start_draw_things():
    """드로띵 앱이 꺼져있으면 켜고, API 서버가 안 보이지 않으면 강제로 실행 시도 (완전 자동화)"""
    print("⏳ [자동화] 드로띵 앱 및 API 서버 상태 확인 중...")
    
    # 1. 앱 실행 확인 및 실행
    check_app = os.popen('pgrep -x "Draw Things"').read().strip()
    if not check_app:
        print("🚀 드로띵 앱이 꺼져 있어 자동으로 실행합니다...")
        os.system('open -a "Draw Things"')
        time.sleep(10) # 로딩 대기

    # 2. API 서버 응답 확인 (반복 시도 및 AppleScript 강제 활성화)
    for i in range(5):
        try:
            requests.get(f"{DRAW_THINGS_URL}/sdapi/v1/options", timeout=2)
            print("✅ 드로띵 API 서버가 활성화되어 있습니다.")
            return True
        except:
            print(f"⏳ API 서버 대기 중... ({i+1}/5) AppleScript 활성화 시도")
            script = '''
            tell application "System Events"
                tell process "Draw Things"
                    set frontmost to true
                    try
                        click menu item "Start" of menu 1 of menu item "HTTP API Server" of menu 1 of menu bar item "File" of menu bar 1
                    on error
                        -- 이미 켜져 있거나 메뉴 구조가 다를 경우 대비하여 조용히 넘어감
                    end try
                end tell
            end tell
            '''
            os.system(f"osascript -e '{script}'")
            time.sleep(5)
    return False

def get_granular_prompts(segments):
    """각 구간별 텍스트를 기반으로 상세한 이미지 프롬프트를 생성합니다."""
    count = len(segments)
    print(f"🤖 Gemini를 통해 {count}개의 캐릭터 에셋용 프롬프트 생성 중...")
    segments_json = json.dumps([{"scene": i+1, "text": t} for i, t in enumerate(segments)], ensure_ascii=False)
    
    prompt = f"""
    당신은 게임/영상 캐릭터 디자이너입니다. 조선 시대 주모 캐릭터의 '에셋(Asset)'을 제작 중입니다.
    배경 없이 캐릭터만 선명하게 보이는 '캐릭터 시트' 스타일로 작성해주세요.

    [시각적 고정 철칙 - CHARACTER ASSET]
    - 스타일: "Character sheet, concept art, full body standing, plain white background, studio lighting, sharp focus, hyper-realistic texture"
    - 인물 [주모]: "A stunning Korean woman with a trendy K-pop Idol style face, sharp facial features, noticeably small and dainty face, sharp jawline, large wide mouth with a generous smile, plump and generous full-figured body, wearing white or off-white rough cotton commoner working clothes, realistic skin texture, period accurate."
    - 배경: "Pure solid white background, no floor, no shadows, standalone asset."

    [프롬프트 작성 규칙]
    1. 반드시 'plain white background'를 포함하여 에셋으로 활용 가능하게 할 것.
    2. 주모의 동작은 서 있거나, 웃거나, 항아리를 들고 있는 등 '에셋'으로 쓰기 좋은 동작 위주로 묘사할 것.
    3. 모든 프롬프트는 영어로 작성하며, 반드시 아래 JSON 리스트 형식으로만 응답할 것.
    """

    try:
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=prompt,
            config=types.GenerateContentConfig(response_mime_type='application/json')
        )
        if response.parsed is not None: return response.parsed
        return json.loads(response.text)
    except Exception as e:
        print(f"⚠️ Gemini 생성 실패 ({e})"); return []

def generate_scene(scene_num, p_text):
    filename = f"Jumo_Asset_V6_{scene_num:02d}.png"
    prompt_text = p_text["prompt"] if isinstance(p_text, dict) else str(p_text)
    
    # [핵심] 캐릭터 에셋 최적화: 화이트 백그라운드 + 소두육덕 아이돌
    payload = {
        "prompt": f"{prompt_text}, character sheet, concept art, full body, plain white background, standalone asset, masterpiece, 8k, highly detailed skin pores, trendy Korean Idol face, small dainty face, large mouth, plump body, white rough cotton clothes, 35mm lens",
        "negative_prompt": "background, tavern, outdoor, landscape, furniture, shadow, house, large face, double chin, cartoon, digital, flat, anime, blurry, low resolution, bad anatomy, silk, colorful, noble, foreigners, text, watermark",
        "steps": 6,
        "width": 640,
        "height": 640,
        "seed": -1,
        "guidance_scale": 1.0,
        "sampler": "Euler a",
        "shift": 3.0,
        "sharpness": 5,
        "seed_mode": "Scale Alike"
    }
    
    print(f"🚀 [Asset Creation] Queueing Jumo Asset {scene_num}...")
    try:
        response = requests.post(f"{DRAW_THINGS_URL}/sdapi/v1/txt2img", json=payload, timeout=200)
        if response.status_code == 200:
            data = response.json()
            if "images" in data and len(data["images"]) > 0:
                filepath = os.path.join(DOWNLOADS_DIR, filename)
                with open(filepath, "wb") as f:
                    f.write(base64.b64decode(data["images"][0]))
                print(f"✅ [에셋 생성 완료] {filename}")
                return scene_num
        print(f"❌ 실패: {response.status_code}")
    except Exception as e:
        print(f"❌ 오류: {e}")
    return None

if __name__ == "__main__":
    if not check_and_start_draw_things():
        print("💡 API 서버 활성화 실패")

    count = 5 # 주모만 5장
    
    # 캐릭터 고정 생성을 위해 더미 세그먼트 생성
    dummy_segments = ["Jumo character asset standing pose", "Jumo character asset greeting pose", "Jumo character asset holding a jar", "Jumo character asset smiling pose", "Jumo character asset working pose"]
    
    prompts = get_granular_prompts(dummy_segments)
    if not prompts: sys.exit(1)

    print(f"\n� 총 {len(prompts)}장의 캐릭터 에셋을 생성합니다 (Sequential)...")
    for i, p in enumerate(prompts[:count]):
        generate_scene(i+1, p)
    print(f"\n✨ 에셋 제작 완료: {DOWNLOADS_DIR}")

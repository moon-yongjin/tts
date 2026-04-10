import os
import json
import time
import requests
import sys
import re
from google import genai
from google.genai import types
from google.oauth2 import service_account
from concurrent.futures import ThreadPoolExecutor, as_completed

# [설정]
BASE_PATH = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(BASE_PATH)
CREDENTIALS_PATH = os.path.join(BASE_PATH, "service_account.json")
CONFIG_PATH = os.path.join(ROOT_DIR, "config.json")
SAKSAKI_API_URL = "http://127.0.0.1:8001/generate"

# [결과 저장 폴더]
_timestamp = time.strftime("%m%d_%H%M")
DOWNLOAD_DIR = os.path.join(os.path.expanduser("~"), "Downloads", f"무협_세로_삭삭이_고정_{_timestamp}")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# 1. Gemini 클라이언트 설정 (02-1 스타일 - 다중 키 지원)
def get_gemini_keys():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                config = json.load(f)
                return [v for k, v in config.items() if "Gemini_API_KEY" in k and v]
        except: pass
    return []

KEYS = get_gemini_keys()
current_key_index = 0
client = genai.Client(api_key=KEYS[0]) if KEYS else None

def init_next_client():
    global client, current_key_index
    current_key_index += 1
    if current_key_index < len(KEYS):
        client = genai.Client(api_key=KEYS[current_key_index])
        print(f"🔄 API Key 스위칭: [{current_key_index+1}/{len(KEYS)}] 키 사용 중")
        return True
    return False

# 2. 고정 스타일 (02-1 기준)
FIXED_STYLE_PROMPT = """
Photorealistic, cinematic film photography, 8k resolution, natural daylight, 
crisp and clear atmosphere, natural white balance, cool color temperature, 
vibrant colors, extremely detailed facial features, consistent character design, 
depth of field, high contrast. 
NO yellowish tint, NO warm sepia filters, NO vintage yellow tones.
NO artistic painting style, NO animation style, NO text.
"""

def split_script(text, count=3):
    text = ' '.join(text.split())
    total_len = len(text)
    limit = max(10, total_len // count)
    chunks = []
    start = 0
    while start < total_len and len(chunks) < count:
        end = start + limit
        if end >= total_len or len(chunks) == count - 1:
            chunks.append(text[start:].strip())
            break
        chunk = text[start:end]
        last_space = chunk.rfind(' ')
        if last_space > limit * 0.7:
            end = start + last_space
        chunks.append(text[start:end].strip())
        start = end + 1
    return chunks

# 3. 프롬프트 생성 (02-1 로직 이식)
def get_consistent_prompts(script_chunk, bible, full_script, prev_summary="None"):
    prompt = f"""
    [Task] Create 1 Ultra-Realistic Vertical Image Prompt for a 3-second cinematic video shot.
    
    [Full Script Context]
    {full_script[:2000]} # 대본 앞부분 위주

    [Visual Bible]
    - CHARACTER: {bible.get('character_en')}
    - BACKGROUND: {bible.get('background_en')}
    - RATIO: 9:16 Vertical
    - STYLE: {FIXED_STYLE_PROMPT}

    [CURRENT SCRIPT PART]
    "{script_chunk}"

    [RULES]
    1. **GLOBAL CONTEXT**: The prompt must be deeply informed by the entire story while focusing on the [CURRENT SCRIPT PART]. 
    2. **CINEMATIC MOVEMENT (For 3s Video)**: Describe the scene as a "living moment" ready for a 3-second camera move. Mention subtle movements like swaying robes, flickering torchlight, falling petals, or a character's steady breathing to make the transition to video natural.
    3. **FACIAL DETAIL**: Specifically describe the character's eyes and gaze. Use terms like "clear pupils", "sharp focus on eyes", "detailed iris", and "realistic skin texture around eyes" to ensure high quality face rendering.
    4. **CINEMATIC DEPTH & CROWDS**: Always include surrounding characters (companions, enemies, or townspeople) in the background or mid-ground to create a sense of scale, depth, and 3D realism.
    5. **입체감 (Stereoscopic Depth)**: Use foreground elements (e.g., blurry out-of-focus objects) or atmospheric effects (mist, dust, floating particles) to enhance the sense of depth.
    6. Vertical Composition: High-angle, low-angle, or close-ups that utilize the full vertical space effectively.
    7. Ensure photorealistic lighting, skin textures, and period-accurate costume details.
    8. NO TEXT. NO CARTOON.
    
    [Output Format] JSON
    {{
      "visual_prompt": "Specific photographic description in English including camera movement hint",
      "summary_for_next": "Brief summary",
      "context_ko": "장면 요약 (한국어)"
    }}
    """
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash", 
            contents=prompt,
            config=types.GenerateContentConfig(response_mime_type="application/json")
        )
        response_text = response.text if isinstance(response.text, str) else response.text[0]
        parsed = json.loads(response_text)
        return parsed[0] if isinstance(parsed, list) else parsed
    except Exception as e:
        print(f"⚠️ 프롬프트 생성 실패: {e}")
        return None

# 4. 삭삭이 서버 요청
def generate_saksaki_image(prompt, idx, context_ko=""):
    filename = f"{idx:02d}_saksaki_refined.png"
    filepath = os.path.join(DOWNLOAD_DIR, filename)
    
    print(f"\n[{idx}/3] {context_ko}")
    print(f"🚀 [SakSaki] 요청: {filename}...")
    
    try:
        # 실사용 네거티브 프롬프트 준비 (애니메이션 요소 제거 및 눈까리 보정)
        negative_prompt = (
            "anime, cartoon, drawing, illustration, sketch, 2d, cg, digital art, manga, line art, monochrome, "
            "deformed face, extra limbs, bad anatomy, "
            "bad eyes, deformed eyes, crossed eyes, lazy eye, poorly drawn eyes, closed eyes, asymmetrical eyes, "
            "squinting, blurry eyes, missing pupils, unnatural eyes, weird eyes"
        )
        
        payload = {
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "style_override": True # 서버의 하드코딩된 애니메이션 스타일 무시
        }
        response = requests.post(SAKSAKI_API_URL, json=payload, timeout=300)
        
        if response.status_code == 200:
            res_data = response.json()
            temp_path = res_data.get("output_path")
            if temp_path and os.path.exists(temp_path):
                import shutil
                shutil.copy2(temp_path, filepath)
                print(f"✅ 완료: {filepath}")
                return True
        print(f"❌ 실패: {response.text}")
    except Exception as e:
        print(f"❌ 서버 에러: {e}")
    return False

def main():
    script_path = os.path.join(ROOT_DIR, "대본.txt")
    bible_path = os.path.join(BASE_PATH, "visual_settings_916_대본.json")

    if not os.path.exists(script_path):
        print("❌ 대본.txt가 없습니다.")
        return
    if not os.path.exists(bible_path):
        print("❌ 고정 JSON(visual_settings_916_대본.json)이 없습니다.")
        return

    with open(script_path, "r", encoding="utf-8") as f:
        full_text = f.read().strip()
    with open(bible_path, "r", encoding="utf-8") as f:
        bible = json.load(f)

    print("📖 고정된 JSON 설정을 로드했습니다.")
    print(f"👤 캐릭터: {bible.get('character_en')[:50]}...")
    print(f"🏙️ 배경: {bible.get('background_en')[:50]}...")

    chunks = split_script(full_text, count=3)
    summary = "Start"
    
    for i, chunk in enumerate(chunks):
        print(f"\n--- [파트 {i+1}/3] Gemini 분석 중 ---")
        data = get_consistent_prompts(chunk, bible, full_text, summary)
        if data:
            summary = data.get('summary_for_next', summary)
            generate_saksaki_image(data['visual_prompt'], i+1, data.get('context_ko', ''))
            time.sleep(1)
        else:
            print(f"⚠️ 파트 {i+1} 분석 실패")

if __name__ == "__main__":
    main()

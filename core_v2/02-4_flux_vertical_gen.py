import os
import json
import time
import subprocess
import sys
import re
from google import genai
from google.genai import types
from concurrent.futures import ThreadPoolExecutor, as_completed

# [설정]
BASE_PATH = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(BASE_PATH)
CONFIG_PATH = os.path.join(ROOT_DIR, "config.json")
# Flux 모델 설정 (사용자 요청: 4-bit or 8-bit MLX/GGUF)
FLUX_MODEL = "mzbac/flux1.schnell.8bit.mlx"
MFLUX_GENERATE_PATH = "/Users/a12/miniforge3/envs/qwen-tts/bin/mflux-generate"

# [결과 저장 폴더]
_timestamp = time.strftime("%m%d_%H%M")
DOWNLOAD_DIR = os.path.join(os.path.expanduser("~"), "Downloads", f"무협_세로_플럭스_{_timestamp}")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# 1. Gemini 클라이언트 설정 (다중 키 지원)
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
    if not KEYS: return False
    current_key_index = (current_key_index + 1) % len(KEYS)
    client = genai.Client(api_key=KEYS[current_key_index])
    print(f"🔄 API Key 스위칭: [{current_key_index+1}/{len(KEYS)}] 키 사용 중")
    return True

# 2. 고정 스타일 (Flux 최적화 - 복잡한 스타일 프롬프트 불필요)
FIXED_STYLE_PROMPT = """
Photorealistic, cinematic film photography, 8k, natural light, 
crisp details, sharp focus on eyes, realistic skin texture, 
professional photography.
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

# 3. 프롬프트 생성 (Gemini)
def get_consistent_prompts(script_chunk, bible, full_script, prev_summary="None"):
    prompt = f"""
    [Task] Create 1 Ultra-Realistic Vertical Image Prompt for Flux.1.
    
    [Full Script Context]
    {full_script[:2000]}

    [Visual Bible]
    - CHARACTER: {bible.get('character_en')}
    - BACKGROUND: {bible.get('background_en')}
    - RATIO: 9:16 Vertical
    - STYLE: {FIXED_STYLE_PROMPT}

    [CURRENT SCRIPT PART]
    "{script_chunk}"

    [RULES]
    1. **FLUX OPTIMIZATION**: Flux is extremely good at following descriptions. Be clear and descriptive.
    2. **EYE & FACE QUALITY**: Explicitly mention "highly detailed eyes, clear iris, sharp focus on eyelashes" to ensure the highest quality.
    3. **PHOTOREALISM**: Avoid generic "photorealistic" tags; instead, describe textures (pores, peach fuzz, fabric weave).
    4. NO TEXT. NO CARTOON.
    
    [Output Format] JSON
    {{
      "visual_prompt": "Specific photographic description in English",
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

# 4. Flux 이미지 생성 (mflux)
def generate_flux_image(prompt, idx, context_ko=""):
    filename = f"{idx:02d}_flux_schnell.png"
    filepath = os.path.join(DOWNLOAD_DIR, filename)
    
    print(f"\n[{idx}/3] {context_ko}")
    print(f"🚀 [Flux] 생성 시작: {filename}...")
    
    # mflux-generate 명령 실행
    # schnell 모델은 보통 4스텝이면 충분함
    cmd = [
        MFLUX_GENERATE_PATH,
        "--model", FLUX_MODEL,
        "--prompt", prompt,
        "--steps", "4",
        "--width", "768",
        "--height", "1344",
        "--output", filepath,
        "--seed", str(int(time.time()) % 10000)
    ]
    
    try:
        start_time = time.time()
        # capture_output=True를 사용하고 에러 시 상세 정보 출력
        # result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        # 위 방식은 verbose하게 보기 어려우므로 변경
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stdout, stderr = process.communicate()
        
        elapsed = time.time() - start_time
        if process.returncode == 0 and os.path.exists(filepath):
            print(f"✅ 완료: {filepath} ({elapsed:.1f}s)")
            return True
        else:
            print(f"❌ 생성 실패 (Code: {process.returncode})")
            if stdout: print(f"--- STDOUT ---\n{stdout}")
            if stderr: print(f"--- STDERR ---\n{stderr}")
    except Exception as e:
        print(f"❌ Flux 실행 에러: {e}")
    return False

def main():
    script_path = os.path.join(ROOT_DIR, "대본.txt")
    bible_path = os.path.join(BASE_PATH, "visual_settings_916_대본.json")

    if not os.path.exists(script_path):
        print("❌ 대본.txt가 없습니다.")
        return
    if not os.path.exists(bible_path):
        print("❌ 고정 JSON이 없습니다.")
        return

    with open(script_path, "r", encoding="utf-8") as f:
        full_text = f.read().strip()
    with open(bible_path, "r", encoding="utf-8") as f:
        bible = json.load(f)

    print("📖 Flux로 전환하여 생성을 시작합니다.")
    print(f"🏗️ 모델: {FLUX_MODEL}")

    chunks = split_script(full_text, count=3)
    summary = "Start"
    
    for i, chunk in enumerate(chunks):
        print(f"\n--- [파트 {i+1}/3] Gemini 분석 중 ---")
        data = get_consistent_prompts(chunk, bible, full_text, summary)
        if data:
            summary = data.get('summary_for_next', summary)
            generate_flux_image(data['visual_prompt'], i+1, data.get('context_ko', ''))
            time.sleep(1)
        else:
            print(f"⚠️ 파트 {i+1} 분석 실패")

if __name__ == "__main__":
    main()

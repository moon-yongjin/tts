import os
import json
import time
import sys
import re
import requests
import base64
import shutil
from concurrent.futures import ThreadPoolExecutor, as_completed
from google import genai
from google.genai import types
from google.oauth2 import service_account

# [설정]
BASE_PATH = os.path.dirname(os.path.abspath(__file__))
CREDENTIALS_PATH = os.path.join(BASE_PATH, "service_account.json")

# 1. Gemini 클라이언트 설정
try:
    credentials = service_account.Credentials.from_service_account_file(
        CREDENTIALS_PATH,
        scopes=['https://www.googleapis.com/auth/cloud-platform']
    )
    client = genai.Client(
        vertexai=True, 
        project="ttss-483505", 
        location="us-central1", 
        credentials=credentials
    )
    print("🧠 [Portrait Mode] Gemini가 세로형(Portrait) 연출을 담당합니다.")
except Exception as e:
    print(f"❌ Google Credential Error: {e}")
    client = None

# 2. Draw Things API 설정
SD_API_URL = "http://127.0.0.1:7860/sdapi/v1/txt2img"

# [저장 경로] 02-2 전용 폴더
def get_portrait_folder():
    base_downloads = os.path.join(os.path.expanduser("~"), "Downloads")
    _timestamp = time.strftime("%m%d_%H%M")
    folder_name = f"무협_세로연출_10컷_{_timestamp}"
    path = os.path.join(base_downloads, folder_name)
    if not os.path.exists(path):
        os.makedirs(path)
    return path

DOWNLOAD_DIR = get_portrait_folder()
print(f"📂 저장 위치: {DOWNLOAD_DIR}")

# [스타일] Flux Clean Realism (No Horror)
# "Clean" 키워드 위주 + 드라마틱 조명
STYLE_PROMPT = "Photorealistic, 8k RAW photo, Fujifilm XT4, Cinematic Lighting, Soft skin texture, Natural features, Detailed eyes, Depth of field, <lora:flux-RealismLora:0.6>"

# --- [Core Functions] ---

def split_script_fixed_count(text, count=10):
    """대본을 강제로 N등분 (장면 연출용)"""
    # 텍스트 전처리
    text = re.sub(r'\s+', ' ', text).strip()
    total_len = len(text)
    chunk_size = total_len // count
    
    chunks = []
    start = 0
    for i in range(count):
        if i == count - 1:
            end = total_len
        else:
            end = start + chunk_size
            # 문장 끝(.)이나 공백을 찾아 자연스럽게 끊기
            lookahead = text.find('.', end - 20, end + 20)
            if lookahead != -1:
                end = lookahead + 1
            else:
                space = text.rfind(' ', start, end + 10)
                if space != -1: end = space
                
        chunk = text[start:end].strip()
        if chunk: chunks.append(chunk)
        start = end
    
    print(f"✂️ [Scene Split] 대본을 {len(chunks)}개 장면으로 분할했습니다.")
    return chunks

# --- [AI Logic] ---

def get_character_profile(script_text):
    """주인공 외모 고정을 위한 프로필 분석"""
    print("🧠 [Gemini] 주인공 외모 분석 중 (한국인/Clean)...")
    prompt = f"""
    Analyze the script and define the Main Character visual profile.
    
    IMPORTANT constraints:
    - Ethnicity: **KOREAN** (Authentic, not caricature).
    - Vibe: Realistic slice-of-life drama (Not Horror/Gritty).
    - Clothing: Realistic daily wear.
    
    Script:
    {script_text[:2000]}
    
    Output JSON ONLY: {{ "visual_prompt": "Detailed English description of a KOREAN character, soft lighting context" }}
    """
    
    try:
        response = client.models.generate_content(
            model="publishers/google/models/gemini-2.0-flash-001", 
            contents=prompt,
            config=types.GenerateContentConfig(response_mime_type="application/json")
        )
        return json.loads(response.text).get("visual_prompt", "Korean woman, middle-aged, worn face")
    except:
        return "Korean woman, middle-aged, worn face, realistic"

def get_dramatic_scene(script_chunk, char_profile, prev_context="None"):
    """Gemini로 극적인 세로 연출 프롬프트 생성 (얼굴박치기 금지)"""
    prompt = f"""
    Create a CINEMATIC VERTICAL SCENE prompt based on the script.
    
    [Character]: {char_profile} (Must be KOREAN)
    [Style]: Raw Realism, Vertical Movie Shot (9:16)
    [Current Plot]: {script_chunk}
    [Context]: {prev_context}
    
    CRITICAL INSTRUCTIONS:
    1. **NO EXTREME CLOSE-UPS**: Do not generate just a face. Show the **UPPER BODY** or **FULL BODY** to reveal the action.
    2. **ACTION & BACKGROUND**: Describe WHAT the character is doing (e.g., eating, running, crying on the floor) and WHERE they are.
    3. **ATMOSPHERE**: Use lighting and set design to reflect the mood (sadness, poverty, urgency).
    4. **KOREAN VIBE**: Ensure the background and artifacts look like a realistic Korean setting if applicable.
    
    Output JSON ONLY:
    {{
      "visual_prompt": "English prompt describing the ACTION and ENVIRONMENT",
      "summary": "Short plot summary for next context"
    }}
    """
    
    try:
        response = client.models.generate_content(
            model="publishers/google/models/gemini-2.0-flash-001", 
            contents=prompt,
            config=types.GenerateContentConfig(response_mime_type="application/json")
        )
        data = json.loads(response.text)
        if isinstance(data, list): data = data[0] # 리스트로 올 경우 첫 번째 요소 사용
        
        return data.get("visual_prompt", ""), data.get("summary", "")
    except Exception as e:
        print(f"⚠️ 프롬프트 생성 실패: {e}")
        return "", prev_context

def generate_portrait(prompt, index):
    """Draw Things API 호출 (Portrait Settings)"""
    filename = f"{index:03d}_Portrait.png"
    filepath = os.path.join(DOWNLOAD_DIR, filename)
    
    print(f"📤 [Scene {index}] 생성 요청...")
    print(f"   📝 {prompt[:80]}...")
    
    # 프롬프트 조립 (Style + Gemini Prompt)
    full_prompt = f"{STYLE_PROMPT}, {prompt}"
    
    # [Flux Clean Realism Tuned]
    payload = {
        "prompt": full_prompt,
        "negative_prompt": "horror, zombie, ghost, scary, ugly, deformed, dirty face, grunge, dark gloom, cartoon, 3d, painting, drawing, sketch, blurry, plastic, smooth, doll",
        "steps": 15,         # [재변경] 8 -> 15 (Clean Quality)
        "width": 832,        # Portrait
        "height": 1216,      # Portrait
        "cfg_scale": 3.0,    # [재변경] 2.5 -> 3.0 (Better Structure)
        "sampler_name": "Euler a",
        "seed": -1
    }

    try:
        start_time = time.time()
        response = requests.post(SD_API_URL, json=payload, timeout=300)
        
        if response.status_code == 200:
            r = response.json()
            if "images" in r:
                img_data = base64.b64decode(r["images"][0])
                with open(filepath, "wb") as f:
                    f.write(img_data)
                print(f"   ✅ 저장 완료: {filepath} ({time.time()-start_time:.2f}s)")
                return True
    except Exception as e:
        print(f"   ❌ 실패: {e}")
    return False

def run_pipeline():
    # 대본 로드
    script_path = os.path.join(os.getcwd(), "대본.txt")
    if not os.path.exists(script_path):
        script_path = os.path.join(BASE_PATH, "대본.txt")
    
    if not os.path.exists(script_path):
        print("❌ 대본.txt를 찾을 수 없습니다.")
        return

    with open(script_path, "r", encoding="utf-8") as f:
        full_text = f.read()

    # 1. 캐릭터 분석
    char_profile = get_character_profile(full_text)
    print(f"👤 캐릭터 프로필 확보: {char_profile[:50]}...")

    # 2. 대본 10등분
    chunks = split_script_fixed_count(full_text, count=10)
    
    # 3. 순차 생성 (문맥 유지)
    prev_context = "Start of the story"
    
    for i, chunk in enumerate(chunks, 1):
        print(f"\n🎥 [Cut {i}/10] --------------------------")
        visual_prompt, summary = get_dramatic_scene(chunk, char_profile, prev_context)
        
        if visual_prompt:
            generate_portrait(visual_prompt, i)
            prev_context = summary
        else:
            print("⚠️ 장면 묘사 실패 SCENE SKIP")

if __name__ == "__main__":
    run_pipeline()

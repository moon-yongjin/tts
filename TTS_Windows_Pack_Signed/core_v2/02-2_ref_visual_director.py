import os
import json
import time
import sys
import re
import requests
import base64
from concurrent.futures import ThreadPoolExecutor, as_completed
from google import genai
from google.genai import types
from google.oauth2 import service_account
from PIL import Image
import io

# [설정]
BASE_PATH = os.path.dirname(os.path.abspath(__file__))
CREDENTIALS_PATH = os.path.join(BASE_PATH, "service_account.json")

# 1. Gemini 클라이언트
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
    print("🧠 [Step 02-2] Reference Mode: Gemini Activated.")
except Exception as e:
    print(f"❌ Google Credential Error: {e}")
    client = None

# 2. 로컬 이미지 생성 API 설정 (Draw Things / SD WebUI)
SD_API_URL = "http://127.0.0.1:7860/sdapi/v1/txt2img"

def get_latest_folder():
    base_downloads = os.path.join(os.path.expanduser("~"), "Downloads")
    subdirs = [os.path.join(base_downloads, d) for d in os.listdir(base_downloads) 
               if os.path.isdir(os.path.join(base_downloads, d)) and d.startswith("무협_로컬생성_")]
    if subdirs:
        latest = sorted(subdirs)[-1]
        if time.time() - os.path.getctime(latest) < 86400:
            return latest
    return None

def encode_image_to_base64(image_path):
    if not os.path.exists(image_path): return None
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode('utf-8')

LATEST_DIR = get_latest_folder()
if LATEST_DIR:
    DOWNLOAD_DIR = LATEST_DIR
    print(f"📂 기존 로컬 폴더 재사용: {DOWNLOAD_DIR}")
else:
    _timestamp = time.strftime("%m%d_%H%M")
    DOWNLOAD_DIR = os.path.join(os.path.expanduser("~"), "Downloads", f"무협_로컬생성_{_timestamp}")
    if not os.path.exists(DOWNLOAD_DIR):
        os.makedirs(DOWNLOAD_DIR)
        print(f"📂 새 로컬 폴더 생성됨: {DOWNLOAD_DIR}")

# 스타일
STYLES = {
    "고전만화책": "Classic black and white manga style, professional inked line art, cinematic screentones, halftone patterns, highly detailed backgrounds, monochrome, strictly black and white, masterpiece"
}
SELECTED_STYLE = "고전만화책"

# --- [Core Functions] ---

def get_character_profile(script_text, script_name="대본.txt"):
    """Gemini를 사용해 대본에서 주인공 분석"""
    script_base = os.path.splitext(script_name)[0]
    profile_cache_path = os.path.join(BASE_PATH, f"character_profile_{script_base}.json")
    
    if os.path.exists(profile_cache_path):
        try:
            with open(profile_cache_path, "r", encoding="utf-8") as f: return json.load(f)
        except: pass

    # ... (기존 Gemini 로직 동일) -> 간략화
    return {"name": "Unknown", "consistency_prompt": "A traditional Korean warrior"}

def get_consistent_prompts(script_chunk, prev_summary="None", current_location="Unknown", retries=2):
    """Gemini로 프롬프트 생성"""
    style_desc = STYLES.get(SELECTED_STYLE, "")
    
    prompt = f"""
    Create a stable diffusion prompt for this script chunk.
    Style: {SELECTED_STYLE} ({style_desc})
    Context: {current_location} / {prev_summary}
    Chunk: {script_chunk}
    
    Output JSON ONLY:
    {{
      "scenes": [{{ "narration": "summary", "visual_prompt": "English prompt here" }}],
      "summary_for_next": "summary",
      "current_location": "location"
    }}
    """
    
    for attempt in range(retries + 1):
        try:
            response = client.models.generate_content(
                model="publishers/google/models/gemini-2.0-flash-001", 
                contents=prompt,
                config=types.GenerateContentConfig(response_mime_type="application/json")
            )
            data = json.loads(response.text)
            if isinstance(data, list): data = data[0]
            return data.get("scenes", []), data.get("summary_for_next", ""), data.get("current_location", "")
        except Exception:
            time.sleep(1)
            
    return [], prev_summary, current_location

def generate_reference_image(scene, global_num, ref_path):
    """로컬 ChilloutMix 서버를 사용하는 Reference 기반 생성 (Image-to-Image)"""
    prompt = scene['visual_prompt']
    filename = f"{global_num:03d}_{SELECTED_STYLE}.png"
    filepath = os.path.join(DOWNLOAD_DIR, filename)
    
    if os.path.exists(filepath):
        print(f"⏭️ {filename} 이미 존재함.")
        return (True, filename)

    print(f"📤 [Local ChilloutMix] 생성 요청: {filename} (Ref Fixed)")
    
    # 로컬 서버 URL (Step 98에서 실행 중인 headless 서버)
    LOCAL_SD_URL = "http://127.0.0.1:8001/generate_ref"
    
    try:
        # 이미지 파일 읽기 및 base64 인코딩
        with open(ref_path, "rb") as f:
            ref_b64 = base64.b64encode(f.read()).decode('utf-8')

        payload = {
            "prompt": prompt,
            "image_base64": ref_b64
        }
        
        response = requests.post(LOCAL_SD_URL, json=payload, timeout=300)
        
        if response.status_code == 200:
            data = response.json()
            temp_output = data.get("output_path")
            
            if temp_output and os.path.exists(temp_output):
                import shutil
                shutil.copy2(temp_output, filepath)
                print(f"   ✨ 로컬 서버 생성 완료: {filepath}")
                return (True, filename)
        
        print(f"   ❌ 로컬 서버 에러: {response.text}")
        return (False, filename, response.text)
        
    except Exception as e:
        print(f"   ❌ 통신 에러: {e}")
        return (False, filename, str(e))

def run_pipeline_ref(full_text, script_name="대본.txt", ref_path="reference.png"):
    print(f"🚀 [Step 02-2] Reference 기반 이미지 생성 시작")
    print(f"   📸 참조 이미지: {ref_path}")
    
    ref_b64 = encode_image_to_base64(ref_path)
    if not ref_b64:
        print("❌ reference.png 파일을 찾을 수 없습니다.")
        return

    # 대본 분할 (기존 로직 재사용)
    # ... (간략화: split_script_by_duration 대신 임시 청킹)
    chunks = [full_text[i:i+300] for i in range(0, len(full_text), 300)]
    
    current_summary = "Start"
    current_location = "Unknown"
    global_counter = 1
    
    with ThreadPoolExecutor(max_workers=1) as executor:
        for i, chunk in enumerate(chunks):
            if global_counter > 10: break # [테스트] 10장으로 제한
            scenes, current_summary, current_location = get_consistent_prompts(chunk, current_summary, current_location)
            if scenes:
                for scene in scenes:
                    if global_counter > 10: break
                    generate_reference_image(scene, global_counter, ref_path)
                    global_counter += 1

if __name__ == "__main__":
    # 참조 이미지 찾기
    ref_path = os.path.join(os.getcwd(), "reference.png")
    if not os.path.exists(ref_path):
        ref_path = os.path.join(BASE_PATH, "reference.png")
    
    # 대본 찾기
    target_path = os.path.join(os.getcwd(), "대본.txt")
    
    if os.path.exists(target_path) and os.path.exists(ref_path):
        with open(target_path, "r", encoding="utf-8") as f:
            full_txt = f.read()
        run_pipeline_ref(full_txt, os.path.basename(target_path), ref_path)
    else:
        print("❌ '대본.txt' 또는 'reference.png' 파일이 필요합니다.")

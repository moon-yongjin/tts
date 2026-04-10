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

# [설정]
BASE_PATH = os.path.dirname(os.path.abspath(__file__))
CREDENTIALS_PATH = os.path.join(BASE_PATH, "service_account.json")

# 1. Gemini 클라이언트 설정 (프롬프트 및 번역용) - 로컬 LLM 대체
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
    print("🧠 [Hybrid Mode] 프롬프트 작성은 'Google Gemini'가 담당합니다. (번역/묘사 품질 보장)")
except Exception as e:
    print(f"❌ Google Credential Error: {e}")
    client = None

# 2. 로컬 이미지 생성 API 설정 (Draw Things App - SD WebUI API 호환)
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

# 스타일 및 설정
STYLES = {
    "수묵화": "Traditional Korean ink wash painting, masterpiece, black and white ink, soft brushwork, artistic oriental painting style, high contrast, NEVER realistic photograph",
    "고전민화": "Traditional Korean folk art (Minhwa), bold black outlines, flat colors, decorative symbolic art, vintage paper texture, NEVER realistic photograph",
    "애니메이션": "Cinematic 2D anime style, Makoto Shinkai inspired, vibrant colors, detailed backgrounds, high-quality cel shading",
    "고전만화책": "Classic black and white manga style, professional inked line art, cinematic screentones, halftone patterns, highly detailed backgrounds, monochrome, strictly black and white, Japanese/Korean manga manuscript style, masterpiece",
}
SELECTED_STYLE = "고전만화책" # [변경] 사용자의 요청에 따라 흑백 만화책 느낌으로 기본값 설정
VISUAL_BIBLE = {}
import shutil
import base64

# --- [Core Functions] ---

def get_exact_duration_from_srt(script_name):
    """SRP 통합 파일 시간 정밀 분석"""
    download_path = os.path.join(os.path.expanduser("~"), "Downloads")
    script_base = os.path.splitext(script_name)[0]
    script_pattern = re.sub(r'_part\d+.*', '', script_base) 
    
    candidates = [f for f in os.listdir(download_path) 
                 if f.startswith(script_pattern) and f.endswith("_Full_Merged.srt")]
    
    if candidates:
        srt_candidate = max([os.path.join(download_path, c) for c in candidates], key=os.path.getmtime)
        try:
            with open(srt_candidate, "r", encoding="utf-8-sig") as f:
                content = f.read().strip()
                times = re.findall(r'(\d{2}:\d{2}:\d{2},\d{3})', content)
                if times:
                    h, m, s_ms = times[-1].split(':')
                    s, ms = s_ms.split(',')
                    total_seconds = int(h)*3600 + int(m)*60 + int(s) + int(ms)/1000
                    print(f"🎯 자막 파일 감지 ({os.path.basename(srt_candidate)}): 정확한 시간 {total_seconds:.1f}초 적용")
                    return total_seconds
        except: pass
    return None

def split_script(text, limit=20):
    chunks = []
    text = ' '.join(text.split())
    start = 0
    while start < len(text):
        end = start + limit
        if end >= len(text):
            chunks.append(text[start:].strip())
            break
        chunk = text[start:end]
        last_space = chunk.rfind(' ')
        if last_space > limit * 0.7:
            end = start + last_space
        chunks.append(text[start:end].strip())
        start = end + 1
    return [c for c in chunks if c]

def split_script_by_duration(text, script_name="대본.txt", target_interval=12.0):
    duration = get_exact_duration_from_srt(script_name)
    if not duration:
        clean_text = re.sub(r'\s+', '', text)
        duration = len(clean_text) / 5.4
        print(f"⚠️ 시간 추정 (텍스트 기반): {duration:.1f}초")
        
    target_image_count = max(1, round(duration / target_interval))
    chars_per_image = max(5, round(len(text) / target_image_count))
    print(f"⏱️  시간 기반 생성 모드: {duration:.1f}초 -> {target_image_count}장 분할 (간격: {target_interval}초)")
    return split_script(text, limit=chars_per_image)

# --- [AI Logic: Gemini + Draw Things] ---

def get_character_profile(script_text, script_name="대본.txt"):
    """Gemini를 사용해 대본에서 주인공 분석"""
    script_base = os.path.splitext(script_name)[0]
    profile_cache_path = os.path.join(BASE_PATH, f"character_profile_{script_base}.json")
    
    if os.path.exists(profile_cache_path):
        try:
            with open(profile_cache_path, "r", encoding="utf-8") as f: return json.load(f)
        except: pass

    print("🧠 [Gemini] 대본 분석 및 주인공 프로필 생성 중...")
    prompt = f"""
    Analyze the script and define the Main Character.
    Output JSON ONLY: {{ "name": "Name", "gender": "Gender", "age": "Age", "visual_description": "Detailed English description", "consistency_prompt": "Concise English prompt" }}
    Script:
    {script_text[:3000]}
    """
    
    retries = 2
    for attempt in range(retries + 1):
        try:
            response = client.models.generate_content(
                model="publishers/google/models/gemini-2.0-flash-001", 
                contents=prompt,
                config=types.GenerateContentConfig(response_mime_type="application/json")
            )
            profile = json.loads(response.text)
            if isinstance(profile, list): profile = profile[0]
            
            with open(profile_cache_path, "w", encoding="utf-8") as f:
                json.dump(profile, f, ensure_ascii=False, indent=2)
            return profile
        except Exception as e:
            wait_time = (2 ** attempt)
            if attempt >= retries:
                print(f"⚠️ Gemini 프로필 생성 실패 (최종): {e}")
            else:
                print(f"⚠️ Gemini 연결 불안정 ({attempt+1}/{retries}). {wait_time}초 후 재시도...")
                time.sleep(wait_time)

    return {"name": "Unknown", "consistency_prompt": "A traditional Korean warrior character"}

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
        except Exception as e:
            wait_time = (2 ** attempt)  # 1, 2, 4초 대기 (Exponential Backoff)
            if attempt >= retries: 
                 print(f"⚠️ Gemini 프롬프트 생성 실패 (최종): {e}")
            else:
                 print(f"⚠️ Gemini 연결 불안정 ({attempt+1}/{retries}). {wait_time}초 후 재시도... (Error: {e})")
                 time.sleep(wait_time)
            
    return [], prev_summary, current_location

def generate_single_image(scene, global_num):
    """Draw Things App API 호출 (SD WebUI 호환)"""
    prompt = scene['visual_prompt']
    filename = f"{global_num:03d}_{SELECTED_STYLE}.png"
    filepath = os.path.join(DOWNLOAD_DIR, filename)
    
    if os.path.exists(filepath) and os.path.getsize(filepath) > 1000:
        print(f"⏭️ {filename} 이미 존재함.")
        return (True, filename)

    print(f"📤 [Draw Things] 생성 요청: {filename}")
    print(f"   📝 [프롬프트]: {prompt[:100]}...") # 로그 추가
    
    # 인물은 대본에 맞추되, 바탕은 무조건 '만화책 원고' 느낌으로 고정
    style_text = STYLES.get(SELECTED_STYLE, '')
    full_prompt = (
        f"((Classic black and white manhwa manuscript style)), {style_text}, "
        f"Artistic scene: {prompt}, "
        f"professional ink line art, detailed manga background, cinematic screen tones, "
        f"monochrome, charcoal, strictly black and white, high contrast, masterpiece"
    )
    
    payload = {
        "prompt": full_prompt,
        "negative_prompt": "color, photo, realistic, 3d, render, low quality, blurry, fuzzy, soft focus, distorted face, watermark, text, signature",
        "steps": 8, # 안정적인 출력을 위해 8단계로 약간 상향
        "width": 1024,
        "height": 576,
        "cfg_scale": 2.5, # 조금 더 선명한 선을 위해 약간 상향
        "sampler_name": "DPM++ SDE Karras" # Lightning 모델에서 화질이 더 좋은 샘플러로 변경
    }

    try:
        # [수정] Draw Things는 로컬 앱이므로 타임아웃 180초면 충분
        response = requests.post(SD_API_URL, json=payload, timeout=180)
        
        if response.status_code == 200:
            r = response.json()
            if "images" in r and len(r["images"]) > 0:
                img_data = base64.b64decode(r["images"][0])
                with open(filepath, "wb") as f:
                    f.write(img_data)
                print(f"   🎨 생성 및 저장 완료: {filepath}")
                return (True, filename)
            else:
                print(f"   ❌ 응답에 이미지가 없음: {r}")
                return (False, filename, "No image in response")
        else:
            print(f"   ❌ HTTP 에러: {response.status_code}")
            return (False, filename, f"Status {response.status_code}")
    except Exception as e:
        print(f"   ❌ 예외 발생: {e}")
        return (False, filename, str(e))

def run_pipeline(full_text, script_name="대본.txt"):
    print(f"🚀 [Local Engine] 이미지 생성 파이프라인 가동 (SD WebUI 필요)")
    
    # 1. 캐릭터 분석
    char_profile = get_character_profile(full_text, script_name)
    
    # 2. 대본 분할
    chunks = split_script_by_duration(full_text, script_name=script_name)
    
    # 3. 생성 루프
    current_summary = "Start"
    current_location = "Unknown"
    global_counter = 1
    
    with ThreadPoolExecutor(max_workers=1) as executor: # 로컬 GPU 부하 고려하여 직렬 처리 권장
        for i, chunk in enumerate(chunks):
            print(f"\n--- [Chunk {i+1}/{len(chunks)}] ---")
            scenes, current_summary, current_location = get_consistent_prompts(chunk, current_summary, current_location)
            
            if scenes:
                for scene in scenes:
                    res = generate_single_image(scene, global_counter)
                    if res[0]: print(f"✅ 생성 완료: {res[1]}")
                    else: print(f"❌ 생성 실패: {res[2]}")
                    global_counter += 1
            else:
                print("⚠️ 프롬프트 생성 실패")

if __name__ == "__main__":
    # 대본 로드 로직
    # ... (기존과 동일하게 대본 찾기)
    search_paths = [os.path.join(os.getcwd(), "대본.txt"), os.path.join(BASE_PATH, "대본.txt")]
    target_path = next((p for p in search_paths if os.path.exists(p)), None)
    
    if target_path:
        with open(target_path, "r", encoding="utf-8") as f:
            full_txt = f.read()
        run_pipeline(full_txt, os.path.basename(target_path))
    else:
        print("❌ 대본.txt가 없습니다.")

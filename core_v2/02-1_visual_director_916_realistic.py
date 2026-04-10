from google import genai
from google.genai import types
from google.oauth2 import service_account
import os
import json
import time
import sys
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

# [윈도우 호환성]
if sys.stdout.encoding.lower() != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 1. 설정 및 서비스 계정 인증
BASE_PATH = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(BASE_PATH)
CONFIG_PATH = os.path.join(ROOT_DIR, "config.json")

# [Config 로드]
GEMINI_KEYS = []
MASTER_CHARACTER_PATH = os.path.join(BASE_PATH, "character_master.json")

if os.path.exists(CONFIG_PATH):
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            config = json.load(f)
            # Gemini_API_KEY, Gemini_API_KEY_2, ... 모든 키 수집
            GEMINI_KEYS = [v for k, v in config.items() if "Gemini_API_KEY" in k and v]
            if GEMINI_KEYS:
                print(f"✅ Config 로드성공: {len(GEMINI_KEYS)}개의 Gemini API Key 확인됨")
    except: pass

current_key_index = 0
client = None

def init_client(index=0):
    global client, current_key_index
    if index >= len(GEMINI_KEYS):
        return False
    current_key_index = index
    client = genai.Client(api_key=GEMINI_KEYS[index])
    print(f"🔄 API Key 스위칭: [{current_key_index+1}/{len(GEMINI_KEYS)}] 키 사용 중")
    return True

# 초기 클라이언트 설정
if not GEMINI_KEYS:
    print("❌ API Key를 찾을 수 없습니다. config.json을 확인하세요.")
    sys.exit(1)

init_client(0)

import argparse
parser = argparse.ArgumentParser(description="AI Premium Realistic Image Director (9:16)")
parser.add_argument("--count", type=int, help="Fixed image count override")
parser.add_argument("--auto-approve", action="store_true", help="Skip manual verification of settings")
parser.add_argument("script_path", nargs="?", help="Path to script text file")
args, unknown = parser.parse_known_args()

# 2. 경로 설정
def get_latest_folder():
    base_downloads = os.path.join(os.path.expanduser("~"), "Downloads")
    subdirs = [os.path.join(base_downloads, d) for d in os.listdir(base_downloads) 
               if os.path.isdir(os.path.join(base_downloads, d)) and d.startswith("무협_세로_")]
    if subdirs:
        latest = sorted(subdirs)[-1]
        if time.time() - os.path.getctime(latest) < 86400: # 24시간 이내
            return latest
    return None

LATEST_DIR = get_latest_folder()
if LATEST_DIR:
    DOWNLOAD_DIR = LATEST_DIR
    print(f"📂 기존 세로 폴더 재사용: {DOWNLOAD_DIR}")
else:
    _timestamp = time.strftime("%m%d_%H%M")
    DOWNLOAD_DIR = os.path.join(os.path.expanduser("~"), "Downloads", f"무협_세로_{_timestamp}")
    if not os.path.exists(DOWNLOAD_DIR):
        os.makedirs(DOWNLOAD_DIR)
        print(f"📂 새 세로 폴더 생성됨: {DOWNLOAD_DIR}")

# [고정 스타일] 사장님 요청: 맑고 선명한 실사 느낌 (누런끼 제거)
FIXED_STYLE_PROMPT = """
Photorealistic, cinematic film photography, 8k resolution, natural daylight, 
crisp and clear atmosphere, natural white balance, cool color temperature, 
vibrant colors, extremely detailed facial features, consistent character design, 
depth of field, high contrast. 
NO yellowish tint, NO warm sepia filters, NO vintage yellow tones.
NO artistic painting style, NO animation style, NO text.
NO split screen, NO multi-panel, NO collage, NO duplicate images, NO grid.
"""

def split_script(text, limit=100):
    text = ' '.join(text.split())
    chunks = []
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

def get_exact_duration_from_srt(script_name):
    download_path = os.path.join(os.path.expanduser("~"), "Downloads")
    script_base = os.path.splitext(script_name)[0]
    candidates = [f for f in os.listdir(download_path) if (f.startswith(script_base) or "_Full_Merged" in f) and f.endswith(".srt")]
    if candidates:
        srt_candidate = max([os.path.join(download_path, c) for c in candidates], key=os.path.getmtime)
        try:
            with open(srt_candidate, "r", encoding="utf-8-sig") as f:
                times = re.findall(r'(\d{2}:\d{2}:\d{2},\d{3})', f.read())
                if times:
                    last_time = times[-1]
                    h, m, s_ms = last_time.split(':'); s, ms = s_ms.split(',')
                    return int(h)*3600 + int(m)*60 + int(s) + int(ms)/1000
        except: pass
    return None

def get_visual_bible_proposal(script_text, script_name):
    script_base = os.path.splitext(script_name)[0]
    settings_path = os.path.join(BASE_PATH, f"visual_settings_916_{script_base}.json")
    
    # [캐릭터 설정] 매회 대본을 분석하여 새로운 캐릭터 프로필 설계 (강제 덮어쓰기)
    print(f"📋 [Visual Bible] 이번 대본에 최적화된 새로운 캐릭터를 설계합니다...")
    master_profile_info = "" # 매번 새롭게 생성하므로 비워둠
    prompt = f"""
    [Task] Create a 9:16 Vertical Cinematic Visual Bible.
    {master_profile_info}
    [Script]
    {script_text[:3000]}
    
    [Requirements]
    1. Focus on PHOTOREALISM: Describe textures, hair, skin, and specific period clothing for the main character.
    2. Character Consistency: Define a specific 'Visual Signature' (e.g., a unique scar, a specific headband, facial structure) to keep the character consistent across AI generations.
    3. Vertical Composition: Framing must be suitable for a smartphone screen (9:16, close-ups and full body shots).
    4. **Aesthetic Tone**: Emphasize a bright and clear atmosphere with natural daylight or cool cinematic moonlight. Avoid yellowish, warm, or vintage sepia tones. 
    
    [Output Format] JSON
    {{
      "approved": false,
      "character_ko": "주인공의 상세한 실사적 특징",
      "character_en": "Deeply detailed physical description for character consistency (age, eyes, nose, hair, skin texture, specific traditional Korean clothes)",
      "background_ko": "영화적 배경 설명",
      "background_en": "Cinematic vertical background description (lighting, atmospheric dust, time of day)",
      "target_interval": 4.0
    }}
    """
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash", 
            contents=prompt,
            config=types.GenerateContentConfig(response_mime_type="application/json")
        )
        
        # 새 SDK는 response.text가 리스트일 수 있음
        if isinstance(response.text, str):
            response_text = response.text
        elif isinstance(response.text, list):
            response_text = response.text[0] if response.text else "{}"
        else:
            response_text = str(response.text) if response.text else "{}"
        
        # JSON 파싱 후 배열인 경우 첫 번째 요소 추출
        parsed = json.loads(response_text)
        if isinstance(parsed, list):
            bible = parsed[0] if parsed else {}
        else:
            bible = parsed
            
        # [마스터 갱신] 매회 생성된 캐릭터를 마스터 프로필에 강제로 저장 (이번 회차 고정용)
        if bible.get("character_en"):
            try:
                with open(MASTER_CHARACTER_PATH, "w", encoding="utf-8") as f:
                    json.dump({"character_en": bible["character_en"]}, f, ensure_ascii=False, indent=2)
                print(f"✨ [마스터 갱신] 새로운 캐릭터 프로필로 연동되었습니다. (이번 50장 고정)")
            except: pass

        bible["approved"] = True
        with open(settings_path, "w", encoding="utf-8") as f:
            json.dump(bible, f, ensure_ascii=False, indent=2)
        return bible, settings_path
    except Exception as e:
        print(f"❌ Bible 생성 실패: {e}")
        return None, None

def get_consistent_prompts(script_chunk, bible, full_script, prev_summary="None"):
    prompt = f"""
    [Task] Create 1 Ultra-Realistic Vertical Image Prompt for a 3-second cinematic video shot.
    
    [Full Script Context]
    {full_script}

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
    3. **CINEMATIC DEPTH & CROWDS**: Always include surrounding characters (companions, enemies, or townspeople) in the background or mid-ground to create a sense of scale, depth, and 3D realism.
    4. **입체감 (Stereoscopic Depth)**: Use foreground elements (e.g., blurry out-of-focus objects) or atmospheric effects (mist, dust, floating particles) to enhance the sense of depth.
    5. Vertical Composition: High-angle, low-angle, or close-ups that utilize the full vertical space effectively.
    6. Ensure photorealistic lighting, skin textures, and period-accurate costume details.
    7. NO TEXT. NO CARTOON.
    
    [Output Format] JSON
    {{
      "visual_prompt": "Specific photographic description in English including camera movement hint",
      "summary_for_next": "Brief summary"
    }}
    """
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash", 
            contents=prompt,
            config=types.GenerateContentConfig(response_mime_type="application/json")
        )
        response_text = response.text if isinstance(response.text, str) else response.text[0] if response.text else "{}"
        parsed = json.loads(response_text)
        # 배열인 경우 첫 번째 요소 반환
        return parsed[0] if isinstance(parsed, list) else parsed
    except: return None

def generate_image(prompt, global_num):
    filename = f"{global_num:03d}_Realistic_Vertical.png"
    filepath = os.path.join(DOWNLOAD_DIR, filename)
    if os.path.exists(filepath): return True, filename

    max_retries = len(GEMINI_KEYS)
    for attempt in range(max_retries):
        try:
            response = client.models.generate_images(
                model='imagen-4.0-generate-001',
                prompt=f"{prompt}. Vertical mobile screen, portrait mode.",
                config={'number_of_images': 1, 'aspect_ratio': '9:16'}
            )
            if not response.generated_images:
                print(f"⚠️ 생성 실패 ({filename}): No images generated (Safety filter or other issue).")
                return False, filename
            img_obj = response.generated_images[0]
            if hasattr(img_obj, 'image') and img_obj.image:
                if hasattr(img_obj.image, 'image_bytes') and img_obj.image.image_bytes:
                    with open(filepath, "wb") as f: f.write(img_obj.image.image_bytes)
                else:
                    img_obj.image.save(filepath)
            elif hasattr(img_obj, 'image_bytes') and img_obj.image_bytes:
                with open(filepath, "wb") as f: f.write(img_obj.image_bytes)
            else:
                print(f"⚠️ 생성 실패 ({filename}): Unexpected image object structure.")
                return False, filename
            return True, filename
        except Exception as e:
            error_msg = str(e).lower()
            if ("429" in error_msg or "quota" in error_msg or "exhausted" in error_msg) and (current_key_index + 1 < len(GEMINI_KEYS)):
                print(f"⚠️ 쿼터 초과 발생! 다음 키로 교체 시도합니다... ({current_key_index + 1}번 키 소진)")
                init_client(current_key_index + 1)
                continue
            else:
                print(f"⚠️ 생성 실패 ({filename}): {e}")
                return False, filename
    return False, filename

def run_pipeline(text, name):
    print("🏙️ [Step 02-1] 프리미엄 실사 세로모드 가동")
    bible, s_path = get_visual_bible_proposal(text, name)
    if not bible: 
        print("❌ Critical: Visual Bible generation failed.")
        sys.exit(1)

    duration = get_exact_duration_from_srt(name) or (len(text)/5.4)
    target_count = args.count if args.count else max(1, round(duration / bible.get('target_interval', 4.0)))
    chunks = split_script(text, limit=max(10, round(len(text)/target_count)))

    print(f"📸 총 {len(chunks)}장의 세로 실사 이미지 생성을 시작합니다.")
    
    summary = "Start"
    futures = []
    with ThreadPoolExecutor(max_workers=4) as executor:
        for i, chunk in enumerate(chunks):
            data = get_consistent_prompts(chunk, bible, text, summary)
            if data:
                summary = data.get('summary_for_next', summary)
                futures.append(executor.submit(generate_image, data['visual_prompt'], i))
                time.sleep(0.5)

        for f in as_completed(futures):
            res = f.result()
            if res[0]: print(f"✅ 완료: {res[1]}")
            else:
                print(f"❌ Critical: Image generation failed for {res[1]}")
                sys.exit(1)

if __name__ == "__main__":
    script_path = args.script_path or os.path.join(ROOT_DIR, "대본.txt")
    if os.path.exists(script_path):
        with open(script_path, "r", encoding="utf-8") as f:
            run_pipeline(f.read().strip(), os.path.basename(script_path))
    else: print("❌ 대본을 찾을 수 없습니다.")

from google import genai
from google.genai import types
from google.oauth2 import service_account
import os
import json
import time
import sys

# [윈도우 호환성]
sys.stdout.reconfigure(encoding='utf-8')
from concurrent.futures import ThreadPoolExecutor, as_completed
import re
import PIL.Image, PIL.ImageDraw


# 1. 설정 및 서비스 계정 인증
BASE_PATH = os.path.dirname(os.path.abspath(__file__))
CREDENTIALS_PATH = os.path.join(BASE_PATH, "service_account.json")

# Vertex AI 클라이언트 설정 (서비스 계정 JSON 파일 사용)
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

# 2. 경로 및 출력 설정 (동적 하위 폴더 생성 및 재사용 로직)
def get_latest_folder():
    base_downloads = os.path.join(os.path.expanduser("~"), "Downloads")
    subdirs = [os.path.join(base_downloads, d) for d in os.listdir(base_downloads) 
               if os.path.isdir(os.path.join(base_downloads, d)) and d.startswith("무협_생성_")]
    if subdirs:
        latest = sorted(subdirs)[-1]
        # 폴더 생성 시간이 24시간 이내인 경우 재사용
        if time.time() - os.path.getctime(latest) < 86400:
            return latest
    return None

LATEST_DIR = get_latest_folder()
if LATEST_DIR:
    DOWNLOAD_DIR = LATEST_DIR
    print(f"📂 기존 폴더 재사용 (누락분 보충): {DOWNLOAD_DIR}")
else:
    _timestamp = time.strftime("%m%d_%H%M")
    DOWNLOAD_DIR = os.path.join(os.path.expanduser("~"), "Downloads", f"무협_생성_{_timestamp}")
    if not os.path.exists(DOWNLOAD_DIR):
        os.makedirs(DOWNLOAD_DIR)
        print(f"📂 새 폴더 생성됨: {DOWNLOAD_DIR}")

# 스타일 정의 (더 강한 화풍 강제를 위해 설명 보강)
STYLES = {
    "수묵화": "Traditional Korean ink wash painting, black and white ink, soft brushwork, artistic oriental painting style, NEVER realistic photograph",
    "고전민화": "Traditional Korean folk art (Minhwa), bold black outlines, flat colors, decorative symbolic art, NEVER realistic photograph",
    "애니메이션": "2D cinematic animation style, high-quality anime cel-shaded look, vibrant hand-drawn aesthetic, NEVER realistic photograph",
    "김성모": "Gritty 90s Korean manhwa comic style, heavy black ink lines, dramatic comic book shading, NEVER realistic photograph",
    "스케치": "Rough artistic pencil sketch, hand-drawn charcoal lines on textured paper, expressive strokes, black and white, NEVER realistic photograph",
    "컬러스케치": "Artistic pencil sketch with light watercolor washes, soft pastel coloring, visible sketch lines, elegant and hand-drawn aesthetic, desaturated colors, NEVER realistic photograph"
}

# 기본 설정 (명령행 인자가 있으면 사용)
# 가급적이면 기존 폴더의 파일명을 보고 스타일을 추정
SELECTED_STYLE = "스케치" # 누락된 파일들이 '스케치'이므로 기본값 변경
if LATEST_DIR:
    existing_files = [f for f in os.listdir(LATEST_DIR) if f.endswith(".png")]
    if existing_files:
        # 파일명에서 스타일 추출 (예: 001_스케치.png -> 스케치)
        sample = existing_files[0]
        if "_" in sample:
            style_part = sample.split("_")[1].replace(".png", "")
            if style_part in STYLES:
                SELECTED_STYLE = style_part
                print(f"🎨 기존 파일 기반 스타일 감지: {SELECTED_STYLE}")

if len(sys.argv) > 1:
    arg_style = sys.argv[1]
    if arg_style in STYLES:
        SELECTED_STYLE = arg_style

# 시각적 연출 옵션
VISUAL_DIRECTIONS = {
    "1": {
        "ko": "[대립과 긴장] 캐릭터 간의 감정 선과 갈등을 강조하는 연출: 표정의 대비, 그림자 활용, 긴박한 구도 위주.",
        "en": "Conflict and Tension: Emphasize emotional tension between characters. Use dramatic lighting, sharp contrasts, and tight framing on facial expressions."
    },
    "2": {
        "ko": "[미장센] 사물과 배경을 통한 상징적 연출: 인물보다는 주변의 사물, 환경, 분위기를 통해 상황을 암시하는 예술적 연출.",
        "en": "Mise-en-scène: Use surrounding objects, environment, and atmosphere to symbolically represent the scene. Focus on artistic compositions and meaningful background details."
    },
    "3": {
        "ko": "[시점의 변화] 다이나믹한 앵글: 익스트림 롱샷, 버드아이 뷰, 낮은 앵글 등 다양한 시점을 통해 공간감과 웅장함 강조.",
        "en": "Dynamic Perspectives: Utilize various camera angles like extreme long shots, bird's-eye views, and low angles to create a sense of scale and space."
    }
}

# 시각적 일관성 베이스 (Visual Bible)
# [수정] 대본 파일명에 따라 동적으로 설정 (run_pipeline에서 초기화)
SETTINGS_PATH = "" 
VISUAL_BIBLE = {
    "character": "Maintain consistency for the main character.",
    "background": "Cinematic 16:9 background consistent with the story.",
    "art_style_override": ""
}

def split_script(text, limit=20):
    """대본을 정확히 20자 단위(사용자 요청 밀도)로 자름"""
    chunks = []
    # 공백과 줄바꿈을 하나의 공백으로 통일
    text = ' '.join(text.split())
    
    # 정확히 60자씩 자르되, 가능하면 단어 경계에서 자름
    start = 0
    while start < len(text):
        end = start + limit
        if end >= len(text):
            chunks.append(text[start:].strip())
            break
        
        # limit 근처에서 공백을 찾아 자연스럽게 자름
        chunk = text[start:end]
        last_space = chunk.rfind(' ')
        if last_space > limit * 0.7:  # limit의 70% 이상 위치에 공백이 있으면 거기서 자름
            end = start + last_space
        
        chunks.append(text[start:end].strip())
        start = end + 1
    
    return [c for c in chunks if c]  # 빈 청크 제거

def get_exact_duration_from_srt(script_name):
    """Downloads 폴더에서 해당 대본의 통합 SRT 파일을 찾아 마지막 자막 시간을 반환"""
    download_path = os.path.join(os.path.expanduser("~"), "Downloads")
    script_base = os.path.splitext(script_name)[0]
    
    # 1. 통합 SRT 파일 검색 (우선순위 높음)
    candidates = [f for f in os.listdir(download_path) 
                 if f.startswith(script_base) and f.endswith("_Full_Merged.srt")]
    
    srt_candidate = None
    if candidates:
        # 가장 최근 파일 선택
        srt_candidate = max([os.path.join(download_path, c) for c in candidates], key=os.path.getmtime)
    
    if srt_candidate and os.path.exists(srt_candidate):
        try:
            with open(srt_candidate, "r", encoding="utf-8-sig") as f:
                content = f.read().strip()
                # SRT 마지막 타임스탬프 추출 (00:06:12,345)
                times = re.findall(r'(\d{2}:\d{2}:\d{2},\d{3})', content)
                if times:
                    last_time = times[-1]
                    h, m, s_ms = last_time.split(':')
                    s, ms = s_ms.split(',')
                    total_seconds = int(h)*3600 + int(m)*60 + int(s) + int(ms)/1000
                    print(f"🎯 자막 파일 감지 ({os.path.basename(srt_candidate)}): 정확한 시간 {total_seconds:.1f}초 적용")
                    return total_seconds
        except Exception as e:
            print(f"⚠️ 자막 분석 에러: {e}")
            
    return None

def get_estimated_duration(text, script_name="대본.txt"):
    """대본 길이를 바탕으로 총 소요 시간(초)을 추정 (SRT 파일 우선)"""
    # 1. SRT 파일에서 정확한 시간 찾기 시도
    exact_time = get_exact_duration_from_srt(script_name)
    if exact_time:
        return exact_time
        
    # 2. 파일이 없으면 추정치 사용 (fallback)
    clean_text = re.sub(r'\s+', '', text)
    # 한글 일반 발화 속도 기준 (초당 5.4자)
    duration = len(clean_text) / 5.4
    print(f"⚠️ 자막 파일을 찾을 수 없어 텍스트 길이로 추정합니다: {duration:.1f}초 (글자수: {len(clean_text)})")
    return duration

def split_script_by_duration(text, script_name="대본.txt", target_interval=12.0, fixed_count=0):
    """
    사용자 요청에 따라 지정된 수량 또는 시간 간격에 맞춰 텍스트를 자름.
    """
    if fixed_count > 0:
        target_image_count = fixed_count
        print(f"🎯 수량 고정 모드: 총 {target_image_count}장 생성 예정")
    else:
        duration = get_estimated_duration(text, script_name)
        target_image_count = max(1, round(duration / target_interval))
        print(f"⏱️  시간 기반 생성 모드: {duration:.1f}초 -> {target_image_count}장 분할 (간격: {target_interval}초)")
    
    total_chars = len(text)
    # 한 장당 배분할 평균 글자 수
    chars_per_image = max(5, round(total_chars / target_image_count))
    
    if fixed_count <= 0:
        print(f"ℹ️  약 {chars_per_image}자당 1장 생성")
    
    return split_script(text, limit=chars_per_image)

def get_visual_bible_proposal(script_text):
    """Gemini를 사용해 배경과 주인공의 시점(Visual Bible) 제안 생성"""
    print("📋 [Visual Bible] 대본을 분석하여 일관된 배경 및 캐릭터 가이드를 생성합니다...")
    
    prompt = f"""
    [Task] Create a 'Visual Bible' for consistent image generation.
    [Script]
    {script_text[:4000]}
    
    [Requirements]
    1. Define the MAIN CHARACTER: Name, age, appearance, clothes, and key features.
    2. Define the GLOBAL BACKGROUND: Setting, lighting, and palette.
    3. Provide descriptions in both Korean (for user review) and English (for image generation).
    
    [Output Format] JSON
    {{
      "approved": false,
      "character_ko": "주인공에 대한 상세한 한국어 설명",
      "character_en": "Very detailed visual prompt for the character in English",
      "background_ko": "배경과 분위기에 대한 한국어 설명",
      "background_en": "Very detailed visual prompt for the background in English",
      "art_style_override_ko": "화풍 유지에 대한 한국어 가이드",
      "art_style_override_en": "Technical prompt instructions to lock in the style",
      "visual_variety_ko": "사물과 분위기를 통한 상징적 연출. 탕약의 김, 문틈의 그림자, 꽉 쥔 손, 서까래 등 클로즈업 샷을 섞어 누아르적인 분위기 강조",
      "visual_variety_en": "Focus on Mise-en-scène and symbolic close-ups: steam from a pot, shadows through doors, clenched hands, or architectural details to create a noir atmosphere without over-relying on character shots.",
      "target_interval": 6.0,
      "clip_duration": 6.0
    }}
    """
    
    try:
        response = client.models.generate_content(
            model="publishers/google/models/gemini-2.0-flash-001", 
            contents=prompt,
            config=types.GenerateContentConfig(response_mime_type="application/json")
        )
        bible_data = json.loads(response.text)
        
        # 리스트로 넘어올 경우 첫 번째 항목 추출
        if isinstance(bible_data, list) and len(bible_data) > 0:
            bible = bible_data[0]
        else:
            bible = bible_data
            
        bible["approved"] = False
        with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
            json.dump(bible, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"❌ Visual Bible 제안 생성 실패: {e}")
        return False

def get_character_profile(script_text, script_name="대본.txt"):
    """Gemini를 사용해 대본에서 주인공의 시각적 프로필을 자동 추출 (로컬 캐시 우선)"""
    script_base = os.path.splitext(script_name)[0]
    profile_cache_path = os.path.join(BASE_PATH, f"character_profile_{script_base}.json")
    
    # 1. 로컬 캐시 확인
    if os.path.exists(profile_cache_path):
        try:
            with open(profile_cache_path, "r", encoding="utf-8") as f:
                profile = json.load(f)
            return profile
        except:
            pass

    print("🧠 대본 분석 및 주인공 프로필 생성 중...")
    
    prompt = f"""
    [Task] Analyze the FULL script and identify the absolute MAIN CHARACTER (Protagonist).
    [Script]
    {script_text}
    
    [Requirements]
    1. Identify the protagonist who leads the story from beginning to end.
    2. Define their name, age, gender, and detailed appearance (clothes, facial features, hair).
    3. IMPORTANT: Distinguish the protagonist from minor characters. The protagonist is the one most mentioned.
    4. Create a "Consistency Prompt" for image generation.
    
    [Output Format] JSON
    {{
      "name": "Character Name",
      "age": "Estimated age",
      "gender": "Gender",
      "visual_description": "Detailed visual description in English",
      "consistency_prompt": "A concise visual prompt for image generation consistency"
    }}
    """
    
    try:
        response = client.models.generate_content(
            model="publishers/google/models/gemini-2.0-flash-001", 
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )
        profile = json.loads(response.text)
        print(f"👤 분석된 주인공: {profile.get('name')} ({profile.get('gender')}, {profile.get('age')})")
        
        # 분석된 프로필 저장 (사용자가 수정할 수 있게 BASE_PATH에 저장)
        try:
            with open(profile_cache_path, "w", encoding="utf-8") as f:
                json.dump(profile, f, ensure_ascii=False, indent=2)
            print(f"📝 새로운 캐릭터 프로필이 저장되었습니다. 필요시 수정하세요: {profile_cache_path}")
        except:
            pass
            
        return profile
    except Exception as e:
        print(f"⚠️ 캐릭터 프로필 생성 실패: {e}")
        return {
            "name": "Protagonist",
            "consistency_prompt": "Maintain consistency for the main character mentioned in the script."
        }

def get_consistent_prompts(script_chunk, prev_summary="None", current_location="Unknown", retries=2):
    """Gemini를 사용해 일관성 있는 이미지 프롬프트 추출 (배경 강화 버전)"""
    style_desc = STYLES.get(SELECTED_STYLE, STYLES["애니메이션"])
    
    monochrome_rule = ""
    if SELECTED_STYLE in ["스케치", "수묵화"]:
        monochrome_rule = "CRITICAL: This is a BLACK AND WHITE style. Do NOT use any color descriptors. NO COLOR allowed."
    
    prompt = f"""
    [Task] Analyze the script and create 1 highly descriptive visual prompt. 
    Focus on PRECISE BACKGROUND AND ATMOSPHERE.
    
    [Visual Style Preset] {SELECTED_STYLE}: {style_desc}
    {monochrome_rule}
    
    [STRICT VISUAL BIBLE]
    - CHARACTER: {VISUAL_BIBLE.get('character_en', '')}
    - GLOBAL STYLE: {VISUAL_BIBLE.get('art_style_override_en', '')}
    - VARIETY (Style Guideline): {VISUAL_BIBLE.get('visual_variety_en', '')}
    
    [URGENT: PREVENT REPETITION]
    - If the variety guideline mentions specific objects (e.g., 'steam', 'hands', 'shadows'), use them as CONCEPTUAL INSPIRATION only. 
    - DO NOT include the same objects in every frame. 
    - Adapt the composition and focus based on the [CURRENT SCRIPT PART]. 
    - If the scene is about travel, show the path. If it's about dialogue, show the atmosphere.
    
    [SCENE CONTEXT]
    - PREVIOUS LOCATION: {current_location}
    - PREVIOUS SUMMARY: {prev_summary}
    
    [CURRENT SCRIPT PART]
    {script_chunk}
    
    [CORE RULES for BACKGROUND & CONTINUITY]
    1. **LOCATION DETECTION**: 
       - If the script mentions a specific place (e.g., 'forest', 'cave', 'market'), update the location. 
       - Describe the NEW environment in extreme detail (architecture, lighting, weather).
       - If no location change is implied, MAINTAIN the previous location with consistent details.
       
    2. **ATMOSPHERIC DETAIL**: Describe light sources, mist, dust, rain, and objects that ground the scene.
    
    3. **CINEMATIC COMPOSITION**: Use "Rule of Thirds" and "Wide Angle" shots. Place character asymmetrically.
    
    4. **STRICT NO-TEXT RULE**: NEVER include text/letters in the prompt.
    
    5. **NO SOLO CHARACTERS**: The protagonist MUST NOT be alone. Always include at least one other character (companion, enemy, or crowd) in the scene to create interaction and scale.
    
    [Output Format] JSON
    {{
      "scenes": [
        {{
          "narration": "Summary of current script chunk",
          "visual_prompt": "Ultra-detailed, high-quality cinematic prompt in English"
        }}
      ],
      "summary_for_next": "Brief plot summary for consistency",
      "current_location": "The specific name and description of the environment in this scene"
    }}
    """
    
    for attempt in range(retries + 1):
        try:
            print(f"🤖 Gemini V2 분석 중... (시도 {attempt+1}/{retries+1})")
            response = client.models.generate_content(
                model="publishers/google/models/gemini-2.0-flash-001", 
                contents=prompt,
                config=types.GenerateContentConfig(response_mime_type="application/json")
            )
            data = json.loads(response.text)
            if isinstance(data, list): data = data[0]
            
            return data.get('scenes', []), data.get('summary_for_next', prev_summary), data.get('current_location', current_location)
        except Exception as e:
            print(f"⚠️ Gemini 에러: {e}")
            if attempt < retries: time.sleep(2)
            else: return [], prev_summary, current_location


def generate_single_image(scene, global_num, retries=3):
    """단일 이미지 생성 함수 (재시도 로직 포함)"""
    prompt = scene['visual_prompt']
    filename = f"{global_num:03d}_{SELECTED_STYLE}.png"
    filepath = os.path.join(DOWNLOAD_DIR, filename)
    
    # 이미 존재하는 파일인지 확인 (0바이트가 아닌 경우 스킵)
    if os.path.exists(filepath) and os.path.getsize(filepath) > 1000:
        print(f"⏭️ {filename} 이미 존재함. 스킵합니다.")
        return (True, filename)

    for attempt in range(retries + 1):
        try:
            # 보수적인 속도 조절
            if attempt > 0:
                time.sleep(3 * attempt) 
            
            style_prefix = STYLES.get(SELECTED_STYLE, STYLES["애니메이션"])
            
            response = client.models.generate_images(
                model='publishers/google/models/imagen-4.0-generate-001',
                prompt=f"Style: {style_prefix}. {prompt}",
                config={'number_of_images': 1, 'aspect_ratio': '16:9'}
            )
            
            img_obj = response.generated_images[0]
            if hasattr(img_obj, 'image'):
                img_obj.image.save(filepath)
            else:
                with open(filepath, "wb") as f:
                    f.write(img_obj.image_bytes)
            return (True, filename)
        except Exception as e:
            print(f"⚠️ Imagen 시도 {attempt+1} 실패 ({filename}): {e}")
            if attempt >= retries:
                return (False, filename, str(e))
    return (False, filename, "Unknown error")

def run_pipeline(full_text, script_name="대본.txt"):
    global VISUAL_BIBLE, SETTINGS_PATH
    start_time = time.time()
    
    # 1. Visual Bible 체크 (배경/주인공 설정 파일)
    script_base = os.path.splitext(script_name)[0]
    SETTINGS_PATH = os.path.join(BASE_PATH, f"visual_settings_{script_base}.json")
    
    if not os.path.exists(SETTINGS_PATH):
        print("\n" + "!"*50)
        print("⚠️  [일관성 보호] 시각적 설정(visual_settings.json)이 없습니다.")
        if get_visual_bible_proposal(full_text):
            print(f"✅ AI가 제안하는 배경 및 캐릭터 설정을 생성했습니다: {SETTINGS_PATH}")
            print("👉 'visual_settings.json' 파일을 열어 배경과 주인공의 모습을 확인/수정해주세요.")
            print("👉 설정이 마음에 들면 다시 실행해 주세요. (자동 실행 방지)")
        print("!"*50 + "\n")
        return

    # 설정 파일 로드 및 승인 여부 확인
    try:
        with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # 리스트로 래핑되어 있는 경우 처리
        if isinstance(data, list):
            VISUAL_BIBLE = data[0] if len(data) > 0 else {}
        else:
            VISUAL_BIBLE = data
            
        if not VISUAL_BIBLE.get("approved", False):
            print("\n" + "="*80)
            print("⌛ [시각적 연출 선택] 영상의 분위기를 결정해 주세요.")
            print("-" * 80)
            for k, v in VISUAL_DIRECTIONS.items():
                print(f"{k}. {v['ko']}")
            print("-" * 80)
            
            choice = input("👉 연출 번호를 선택하세요 (1/2/3) 또는 'n'으로 종료: ").strip()
            
            if choice in VISUAL_DIRECTIONS:
                dir_info = VISUAL_DIRECTIONS[choice]
                VISUAL_BIBLE["visual_variety_ko"] = dir_info["ko"]
                VISUAL_BIBLE["visual_variety_en"] = dir_info["en"]
                VISUAL_BIBLE["approved"] = True
                
                with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
                    json.dump(VISUAL_BIBLE, f, ensure_ascii=False, indent=2)
                print(f"✅ 연출 스타일 '{choice}번'이 적용되었습니다. 제작을 시작합니다.\n")
            else:
                print("\n💡 설정을 확인한 뒤에 다시 실행해 주세요.")
                print("="*80 + "\n")
                return
            
        print(f"📖 시각적 설정(Visual Bible) 승인됨: 생성 모드로 진입합니다.")
    except Exception as e:
        print(f"❌ 설정 파일 로드 에러: {e}")
        return

    print(f"🚀 AI 이미지 디렉터 가동 중... (스타일: {SELECTED_STYLE})")
    print(f"📍 저장 위치: {DOWNLOAD_DIR}")
    
    # 0. 주인공 프로필 설정 (기존 사용 또는 새로 파악 선택)
    script_base = os.path.splitext(script_name)[0]
    profile_cache_path = os.path.join(BASE_PATH, f"character_profile_{script_base}.json")
    char_profile = None

    if os.path.exists(profile_cache_path):
        print("\n" + "="*80)
        print("👤 [캐릭터 일관성 설정] 기존에 파악된 주인공 정보를 재사용하시겠습니까?")
        try:
            with open(profile_cache_path, "r", encoding="utf-8") as f:
                p = json.load(f)
            print(f"  - 현재 주인공: {p.get('name')} ({p.get('age')}, {p.get('gender')})")
            print(f"  - 묘사: {p.get('visual_description', '')[:100]}...")
        except:
            pass
        print("-" * 80)
        
        char_choice = input("👉 기존 정보 사용(r) / 새로 파악하기(n): ").strip().lower()
        if char_choice == 'r':
            print("♻️  기존 주인공 정보를 재사용합니다.")
            char_profile = get_character_profile(full_text, script_name=script_name)
        else:
            print("🧠 대본을 통해 주인공을 다시 파악합니다...")
            # 캐시 파일 삭제 후 재생성
            if os.path.exists(profile_cache_path): os.remove(profile_cache_path)
            char_profile = get_character_profile(full_text, script_name=script_name)
            # [Fix] Bible에 이미 있는 잘못된 주인공 정보도 덮어쓰기 위해 초기화
            VISUAL_BIBLE['character_en'] = char_profile.get('consistency_prompt', "")
            VISUAL_BIBLE['character_ko'] = char_profile.get('visual_description', "")
    else:
        char_profile = get_character_profile(full_text, script_name=script_name)
        VISUAL_BIBLE['character_en'] = char_profile.get('consistency_prompt', "")
        VISUAL_BIBLE['character_ko'] = char_profile.get('visual_description', "")

    # Bible 정보 통합 (Bible이 우선이지만, 새로 파악한 경우 위에서 이미 덮어씀)
    if not VISUAL_BIBLE.get('character_en'):
        VISUAL_BIBLE['character_en'] = char_profile.get('consistency_prompt', "")
    
    # 최종 프로필 저장 (참고용)
    profile_path = os.path.join(DOWNLOAD_DIR, "character_profile.json")
    with open(profile_path, "w", encoding="utf-8") as f:
        json.dump(char_profile, f, ensure_ascii=False, indent=2)
    print(f"📝 캐릭터 프로필 최종본 저장됨: {profile_path}")

    # 대본 쪼개기 (수량 설정 확인)
    user_interval = VISUAL_BIBLE.get('target_interval', 6.0)
    fixed_image_count = VISUAL_BIBLE.get('target_image_count', 0)
    
    # 명령행 인자에서 --count 가 있으면 덮어쓰기
    for i, arg in enumerate(sys.argv):
        if arg == "--count" and i+1 < len(sys.argv):
            try:
                fixed_image_count = int(sys.argv[i+1])
            except: pass

    chunks = split_script_by_duration(full_text, script_name=script_name, target_interval=user_interval, fixed_count=fixed_image_count)
    current_summary = "Starting the story"
    # 배경 일관성을 위한 초기 위치 설정
    current_location = VISUAL_BIBLE.get('background_en', VISUAL_BIBLE.get('background', "Unknown location"))
    
    total_images = len(chunks)
    print(f"📦 총 {total_images}개의 파트 분석 및 생성을 시작합니다. (배경 강화 버전)")
    print(f"🚀 [병렬 처리 활성화] Gemini 분석과 Imagen 생성을 동시에 진행합니다.")
    
    global_counter = 1
    futures = []
    
    # 이미지 생성을 위한 고정 풀 (안정적인 생성을 위해 worker 수 조절)
    with ThreadPoolExecutor(max_workers=4) as executor:
        for i, chunk in enumerate(chunks):
            print(f"\n--- [파트 {i+1}/{len(chunks)}] Gemini V2 분석 중 ---")
            
            # 1. 일관성 있는 프롬프트 추출 (Gemini)
            scenes, current_summary, current_location = get_consistent_prompts(chunk, current_summary, current_location)
            
            if scenes:
                print(f"💬 파트 대본: {scenes[0].get('narration', '내용 없음')}")
            
            # 1.5 SFX 태그 추출
            sfx_tags = re.findall(r'\[SFX:([^\]]+)\]', chunk)
            
            # 2. 이미지+비디오 생성 예약 (Imagen) - 비동기 방식으로 즉시 넘김
            if scenes:
                for scene in scenes:
                    filename = f"{global_counter:03d}_{SELECTED_STYLE}.png"
                    print(f"📤 생성 대기열 추가: {filename}")
                    
                    future = executor.submit(generate_single_image, scene, global_counter)
                    futures.append(future)
                    global_counter += 1
                    # 너무 빠른 요청 방지 (burst limit 방역)
                    time.sleep(0.5) 
            else:
                print(f"⚠️ 파트 {i+1}에서 프롬프트를 추출하지 못했습니다.")
        
        # 모든 작업 완료 대기
        print(f"\n⏳ 모든 이미지가 생성될 때까지 대기합니다... (남은 이미지: {len(futures)}장)")
        completed_count = 0
        for future in as_completed(futures):
            result = future.result()
            completed_count += 1
            if result[0]:
                print(f"✅ [{completed_count}/{len(futures)}] 완료: {result[1]}")
            else:
                print(f"❌ [{completed_count}/{len(futures)}] 최종 실패: {result[1]} - {result[2]}")
    
    end_time = time.time()
    duration = end_time - start_time
    mins = int(duration // 60)
    secs = int(duration % 60)
    
    print("\n" + "="*50)
    print(f"📊 작업 완료 리포트")
    print(f"📸 총 생성 이미지: {len(futures)}장")
    print(f"⏱️ 총 소요 시간: {mins}분 {secs}초")
    if len(futures) > 0:
        print(f"✨ 평균 속도: {duration/len(futures):.1f}초/장 (Gemini+Imagen 병렬 처리 적용)")
    print("="*50)
    
    # 다음 실행 시 다시 선택할 수 있도록 승인 상태 초기화 (사용자 요청)
    VISUAL_BIBLE["approved"] = False
    try:
        with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
            json.dump(VISUAL_BIBLE, f, ensure_ascii=False, indent=2)
    except:
        pass

if __name__ == "__main__":
    # 대본 파일 찾기 로직 강화 (CWD -> 부모 -> 현재 순)
    possible_paths = [
        os.path.join(os.getcwd(), "대본.txt"),
        os.path.join(os.path.dirname(BASE_PATH), "대본.txt"),
        os.path.join(BASE_PATH, "대본.txt")
    ]
    
    script_path = None
    for path in possible_paths:
        if os.path.exists(path):
            script_path = path
            break
            
    # 명령행 인자가 있다면 최우선 적용
    if len(sys.argv) > 1 and sys.argv[1].endswith(".txt"):
         if os.path.exists(sys.argv[1]):
             script_path = sys.argv[1]

    if script_path:
        print(f"📄 대본 파일 로드: {script_path}")
        with open(script_path, "r", encoding="utf-8") as f:
            script_text = f.read().strip()
        run_pipeline(script_text, script_name=os.path.basename(script_path))
    else:
        print(f"❌ 대본 파일을 찾을 수 없습니다. (확인 경로: {possible_paths})")

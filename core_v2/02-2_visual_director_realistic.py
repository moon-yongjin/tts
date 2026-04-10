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


# 1. 설정 및 API 풀 관리
BASE_PATH = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(BASE_PATH)
CONFIG_PATH = os.path.join(ROOT_DIR, "config.json")
API_KEYS_PATH = os.path.join(BASE_PATH, "api_keys.json")

class KeyPool:
    def __init__(self):
        self.keys = []
        self.blacklisted = set()
        # 1. config.json에서 기본 키 로드
        if os.path.exists(CONFIG_PATH):
            try:
                with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    k = config.get("Gemini_API_KEY")
                    if k: self.keys.append(k)
            except: pass
        
        # 2. api_keys.json에서 추가 키 로드
        if os.path.exists(API_KEYS_PATH):
            try:
                with open(API_KEYS_PATH, "r", encoding="utf-8") as f:
                    api_data = json.load(f)
                    for _, v in api_data.items():
                        if v not in self.keys: self.keys.append(v)
            except: pass
            
        if not self.keys:
            print("❌ 사용 가능한 API Key가 없습니다.")
            sys.exit(1)
            
        self.current_idx = 0
        self.client = None
        self.setup_client()
        print(f"🔑 [API Pool] 총 {len(self.keys)}개의 키가 로드되었습니다.")

    def setup_client(self):
        self.client = genai.Client(api_key=self.keys[self.current_idx])

    def rotate(self, blacklist_current=False):
        if blacklist_current:
            print(f"🚫 [API Blacklist] 키 {self.current_idx} 블랙리스트 추가.")
            self.blacklisted.add(self.current_idx)
            
        if len(self.keys) - len(self.blacklisted) <= 0:
            print("❌ 모든 키가 블랙리스트에 올랐거나 사용 불가능합니다.")
            return False
            
        start_idx = self.current_idx
        while True:
            self.current_idx = (self.current_idx + 1) % len(self.keys)
            if self.current_idx not in self.blacklisted:
                break
            if self.current_idx == start_idx:
                return False
                
        self.setup_client()
        print(f"🔄 [API Rotation] 키 교체됨 (Index: {self.current_idx})")
        return True

pool = KeyPool()
client = pool.client # 전역 참조용 (구조 유지)

import argparse

# Argument Parsing
parser = argparse.ArgumentParser(description="AI Image Director (Realistic Mode)")
parser.add_argument("--style", type=str, help="Art style override")
parser.add_argument("--count", type=int, help="Fixed image count override")
parser.add_argument("--output-dir", type=str, help="Custom output directory path")
parser.add_argument("--auto-approve", action="store_true", help="Skip manual verification of settings")
parser.add_argument("script_path", nargs="?", help="Path to script text file")
args, unknown = parser.parse_known_args()

# 2. 경로 및 출력 설정 (동적 하위 폴더 생성 및 재사용 로직)
def get_latest_folder():
    base_downloads = os.path.join(os.path.expanduser("~"), "Downloads")
    subdirs = [os.path.join(base_downloads, d) for d in os.listdir(base_downloads) 
               if os.path.isdir(os.path.join(base_downloads, d)) and d.startswith("무협_세로_")]
    if subdirs:
        latest = sorted(subdirs)[-1]
        # 폴더 생성 시간이 24시간 이내인 경우 재사용
        if time.time() - os.path.getctime(latest) < 86400:
            return latest
    return None

LATEST_DIR = get_latest_folder()
if args.output_dir:
    DOWNLOAD_DIR = args.output_dir
    if not os.path.exists(DOWNLOAD_DIR):
        os.makedirs(DOWNLOAD_DIR)
    print(f"📂 사용자 지정 경로 사용: {DOWNLOAD_DIR}")
elif LATEST_DIR:
    DOWNLOAD_DIR = LATEST_DIR
    print(f"📂 기존 폴더 재사용 (누락분 보충): {DOWNLOAD_DIR}")
else:
    _timestamp = time.strftime("%m%d_%H%M")
    DOWNLOAD_DIR = os.path.join(os.path.expanduser("~"), "Downloads", f"무협_세로_{_timestamp}")
    if not os.path.exists(DOWNLOAD_DIR):
        os.makedirs(DOWNLOAD_DIR)
        print(f"📂 새 세로 폴더 생성됨: {DOWNLOAD_DIR}")

# 스타일 정의 (실사진 중심 강화)
STYLES = {
    "실사진": "Hyper-realistic professional photography, masterpiece, 8k resolution, crisp detail, clean neutral white balance, sharp focus, cinematic studio lighting, highly detailed textures, NO yellow tint, NO warm filters, bright white clean aesthetic, pure colors",
    "수묵화": "Traditional Korean ink wash painting, black and white ink, soft brushwork, artistic oriental painting style, NEVER realistic photograph",
    "애니메이션": "2D cinematic animation style, high-quality anime cel-shaded look, vibrant hand-drawn aesthetic, NEVER realistic photograph",
    "스케치": "Rough artistic pencil sketch, hand-drawn charcoal lines on textured paper, expressive strokes, black and white, NEVER realistic photograph",
}

# 기본 설정: 실사진
SELECTED_STYLE = "실사진" 

# 스타일 우선순위: Argument > Default
if args.style and args.style in STYLES:
    SELECTED_STYLE = args.style

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
SETTINGS_PATH = "" 
VISUAL_BIBLE = {
    "character": "Maintain consistency for the main character.",
    "background": "Cinematic 16:9 background consistent with the story.",
    "art_style_override": ""
}

def split_script(text, limit=20):
    """대본을 정확히 20자 단위(사용자 요청 밀도)로 자름"""
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

def get_exact_duration_from_srt(script_name):
    download_path = os.path.join(os.path.expanduser("~"), "Downloads")
    script_base = os.path.splitext(script_name)[0]
    candidates = [f for f in os.listdir(download_path) if f.startswith(script_base) and f.endswith("_Full_Merged.srt")]
    srt_candidate = None
    if candidates:
        srt_candidate = max([os.path.join(download_path, c) for c in candidates], key=os.path.getmtime)
    if srt_candidate and os.path.exists(srt_candidate):
        try:
            with open(srt_candidate, "r", encoding="utf-8-sig") as f:
                content = f.read().strip()
                times = re.findall(r'(\d{2}:\d{2}:\d{2},\d{3})', content)
                if times:
                    last_time = times[-1]
                    h, m, s_ms = last_time.split(':')
                    s, ms = s_ms.split(',')
                    total_seconds = int(h)*3600 + int(m)*60 + int(s) + int(ms)/1000
                    return total_seconds
        except Exception as e:
            print(f"⚠️ 자막 분석 에러: {e}")
    return None

def get_estimated_duration(text, script_name="대본.txt"):
    exact_time = get_exact_duration_from_srt(script_name)
    if exact_time:
        return exact_time
    clean_text = re.sub(r'\s+', '', text)
    duration = len(clean_text) / 5.4
    return duration

def split_script_by_duration(text, script_name="대본.txt", target_interval=12.0, fixed_count=0):
    if fixed_count > 0:
        target_image_count = fixed_count
    else:
        duration = get_estimated_duration(text, script_name)
        target_image_count = max(1, round(duration / target_interval))
    total_chars = len(text)
    chars_per_image = max(5, round(total_chars / target_image_count))
    return split_script(text, limit=chars_per_image)

def get_visual_bible_proposal(script_text, retry_limit=3):
    print("📋 [Visual Bible] 실사진 화풍 기반의 설정을 생성합니다...")
    prompt = f"""
    [Task] Create a 'Visual Bible' for consistent REALISTIC image generation.
    [Script]
    {script_text[:4000]}
    
    [Requirements]
    1. Define the MAIN CHARACTER with photographic precision.
    2. Define the GLOBAL BACKGROUND with sharp, clean white lighting.
    3. ART STYLE: Must be hyper-realistic photography. NO yellow tints. Use 'Neutral White Balance' and 'Natural Studio Lighting'.
    
    [Output Format] JSON
    {{
      "approved": false,
      "character_ko": "실사 사진 같은 주인공 설명",
      "character_en": "Hyper-realistic portrait details, professional DSLR look, clean lighting",
      "background_ko": "깨끗하고 밝은 실사 배경",
      "background_en": "Modern clean background, high-end architecture/nature, bright neutral daylight, white balance calibrated",
      "art_style_override_ko": "실사 사진 (세로형 쇼츠 구성)",
      "art_style_override_en": "Professional 9:16 portrait photography, clean white balance, NO yellow tint, vivid natural colors",
      "visual_variety_ko": "세로형에 적합한 인물 중심 및 세로 구도 연출",
      "visual_variety_en": "Vertical composition optimized for Shorts (9:16). Focus on full-body shots or expressive vertical portraits.",
      "target_interval": 6.0,
      "clip_duration": 6.0
    }}
    """
    for attempt in range(retry_limit):
        try:
            response = pool.client.models.generate_content(
                model="gemini-2.0-flash", 
                contents=prompt,
                config=types.GenerateContentConfig(response_mime_type="application/json")
            )
            bible = json.loads(response.text)
            if isinstance(bible, list): bible = bible[0]
            bible["approved"] = False
            with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
                json.dump(bible, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"⚠️ Visual Bible 생성 실패 (시도 {attempt+1}): {e}")
            pool.rotate()
            time.sleep(2)
    return False

def get_character_profile(script_text, script_name="대본.txt", retry_limit=3):
    script_base = os.path.splitext(script_name)[0]
    profile_cache_path = os.path.join(BASE_PATH, f"character_master_{script_base}_realistic.json")
    if os.path.exists(profile_cache_path):
        try:
            with open(profile_cache_path, "r", encoding="utf-8") as f:
                profile = json.load(f)
                if profile.get("approved", False):
                    return profile
                else:
                    print(f"💡 캐릭터 마스터 설정 확인 대기 중: {profile_cache_path}")
                    return profile
        except: pass
    
    print("👤 주인공의 실사 프로필(한국인 특징 강화)을 분석 중입니다...")
    prompt = f"""
    [Task] Create a HIGH-PRECISION visual master profile for the protagonist based on the script.
    [Constraint] MUST be a KOREAN/ASIAN person with natural features. 
    [Style] Professional high-end photography focus.
    
    [Script] {script_text[:4000]}
    
    [Output Format] JSON
    {{
      "approved": false,
      "name": "주인공 이름",
      "age": "나이대",
      "visual_description_ko": "한국인 특유의 외모 특징 (쌍꺼풀 유무, 머리 모양, 피부톤 등) 상세 기술",
      "visual_description_en": "DETAILED portrait description: Typical Korean facial features, natural Asian eyes (monolid/hooded), straight dark hair, specific clothing texture, weathered skin if old, etc.",
      "fixed_anchor_prompt": "Forceful English string for Imagen: 'A real Korean [man/woman] in [age], [hair], [clothing], natural Korean features, pure ivory skin tone, professional portrait photography...'"
    }}
    """
    for attempt in range(retry_limit):
        try:
            response = pool.client.models.generate_content(
                model="gemini-2.0-flash", 
                contents=prompt,
                config=types.GenerateContentConfig(response_mime_type="application/json")
            )
            data = json.loads(response.text)
            if isinstance(data, list): profile = data[0]
            else: profile = data
            
            profile['approved'] = False
            # Ensure the anchor is strong
            if 'fixed_anchor_prompt' not in profile:
                profile['fixed_anchor_prompt'] = f"Hyper-realistic professional photo of a Korean {profile.get('gender', 'person')}, {profile.get('age', 'middle-aged')}, natural Korean facial features (monolid or hooded eyes, typical Asian nose), {profile.get('visual_description_en', 'Korean style')}."
            
            with open(profile_cache_path, "w", encoding="utf-8") as f:
                json.dump(profile, f, ensure_ascii=False, indent=2)
            return profile
        except Exception as e:
            print(f"⚠️ 캐릭터 프로필 생성 실패 (시도 {attempt+1}): {e}")
            pool.rotate()
            time.sleep(2)
    
    fallback = {"name": "Protagonist", "fixed_anchor_prompt": "Hyper-realistic Korean person with natural Asian facial features, professional portrait photography, clean white balance", "approved": False}
    with open(profile_cache_path, "w", encoding="utf-8") as f:
        json.dump(fallback, f, ensure_ascii=False, indent=2)
    return fallback

def get_consistent_prompts(script_chunk, prev_summary="None", current_location="Unknown", retries=3):
    style_desc = STYLES.get(SELECTED_STYLE)
    prompt = f"""
    [Task] Create 1 HIGHLY DRAMATIC photographic visual prompt that captures the SPECIFIC SITUATION in the script.
    [Style] {SELECTED_STYLE}: {style_desc}
    [Constraint] KOREAN ethnicity, CLEAN WHITE LIGHTING, NO YELLOW TINTS.
    
    [Visual Bible]
    - CHAR: {VISUAL_BIBLE.get('character_en', '')} (Must follow this identity)
    - STYLE: {VISUAL_BIBLE.get('art_style_override_en', '')}
    
    [SCRIPT CHUNK]
    {script_chunk}
    
    [Instructions for Situation]
    - Capture the ACTION: Is someone blocking someone? Is someone throwing an object? Is someone bowing?
    - Capture the EMOTION: Frowning face, sneering expression, warm smile, stern authority.
    - Capture the ENVIRONMENT: Modern art gallery details, luxury sedans, specific props mentioned.
    - Be descriptive with the visual composition (Close-up of a sneer, wide shot of a confrontation).
    
    [Output] JSON
    {{
      "scenes": [
        {{
          "narration": "Summary of the script part",
          "visual_prompt": "Cinematic photographic description of the SPECIFIC DRAMATIC SITUATION: [Action], [Reaction], [Setting details], [Composition]..."
        }}
      ],
      "summary_for_next": "..."
    }}
    """
    for attempt in range(retries):
        try:
            response = pool.client.models.generate_content(
                model="gemini-2.0-flash", 
                contents=prompt,
                config=types.GenerateContentConfig(response_mime_type="application/json")
            )
            data = json.loads(response.text)
            if isinstance(data, list): data = data[0]
            return data.get('scenes', []), data.get('summary_for_next', prev_summary), data.get('current_location', current_location)
        except Exception as e:
            print(f"⚠️ 프롬프트 생성 실패 (시도 {attempt+1}): {e}")
            pool.rotate()
            time.sleep(2)
    return [], prev_summary, current_location

def generate_single_image(scene, global_num, char_anchor, retries=5):
    prompt = scene['visual_prompt']
    filename = f"{global_num:03d}_{SELECTED_STYLE}.png"
    filepath = os.path.join(DOWNLOAD_DIR, filename)
    if os.path.exists(filepath) and os.path.getsize(filepath) > 1000:
        return (True, filename)

    for attempt in range(retries):
        try:
            style_prefix = STYLES.get(SELECTED_STYLE)
            # ANCHOR IS MANDATORY: Prepaid character description to every prompt
            final_prompt = f"Style: {style_prefix}. Subject: {char_anchor}. Action/Scene: {prompt}. Pure white lighting, clean atmosphere, realistic textures, cinematic photography, NO non-Asian features."
            response = pool.client.models.generate_images(
                model='imagen-4.0-generate-001',
                prompt=final_prompt,
                config={'number_of_images': 1, 'aspect_ratio': '9:16'}
            )
            img_obj = response.generated_images[0]
            if hasattr(img_obj, 'image'):
                img_obj.image.save(filepath)
            else:
                with open(filepath, "wb") as f:
                    f.write(img_obj.image_bytes)
            return (True, filename)
        except Exception as e:
            err_msg = str(e).lower()
            blacklist = False
            if "429" in err_msg or "resource_exhausted" in err_msg:
                print(f"⏳ [Rate Limit] {filename} 대기 중 (30초)...")
                time.sleep(30)
            elif "disconnected" in err_msg:
                print(f"🔌 [Network] {filename} 재시도 중...")
                time.sleep(5)
            elif "400" in err_msg and ("billed" in err_msg or "valid" in err_msg):
                print(f"🚫 [API Error] {filename} 키 문제 감지: {e}")
                blacklist = True
            else:
                print(f"⚠️ Imagen 생성 실패 (시도 {attempt+1}, {filename}): {e}")
            
            if not pool.rotate(blacklist_current=blacklist):
                print("❌ 더 이상 교체할 키가 없습니다. 생성을 중단합니다.")
                return (False, filename, "No valid keys left")
            time.sleep(3)
    return (False, filename, "Exhausted retries")

def run_pipeline(full_text, script_name="대본.txt"):
    global VISUAL_BIBLE, SETTINGS_PATH
    script_base = os.path.splitext(script_name)[0]
    SETTINGS_PATH = os.path.join(BASE_PATH, f"visual_settings_{script_base}_realistic.json")
    SCENES_PATH = os.path.join(BASE_PATH, f"scenes_{script_base}_realistic.json")
    
    if not os.path.exists(SETTINGS_PATH):
        if get_visual_bible_proposal(full_text):
            if args.auto_approve:
                with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
                    bible = json.load(f)
                bible["approved"] = True
                with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
                    json.dump(bible, f, ensure_ascii=False, indent=2)
            else:
                print(f"👉 설정 파일 생성됨: {SETTINGS_PATH}. 확인 후 다시 실행.")
                return

    with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
        VISUAL_BIBLE = json.load(f)
        if isinstance(VISUAL_BIBLE, list): VISUAL_BIBLE = VISUAL_BIBLE[0]

    if not VISUAL_BIBLE.get("approved", False):
        if args.auto_approve:
            VISUAL_BIBLE["approved"] = True
            with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
                json.dump(VISUAL_BIBLE, f, ensure_ascii=False, indent=2)
        else:
            print("💡 설정 승인 대기 중.")
            return

    char_profile = get_character_profile(full_text, script_name)
    # Automatic approval/usage of character anchor
    char_anchor = char_profile.get('fixed_anchor_prompt', "Hyper-realistic Korean protagonist, professional photography")
    VISUAL_BIBLE['character_en'] = char_anchor
    
    # 1. 씬 리스트 생성 (내부용, 별도 승인 없이 자동 진행)
    all_scenes = []
    if os.path.exists(SCENES_PATH):
        try:
            with open(SCENES_PATH, "r", encoding="utf-8") as f:
                all_scenes = json.load(f)
                print(f"📂 기존 씬 리스트 로드됨 ({len(all_scenes)}개)")
        except: pass

    if not all_scenes:
        print("📝 프롬프트를 생성 중입니다...")
        chunks = split_script_by_duration(full_text, script_name, target_interval=VISUAL_BIBLE.get('target_interval', 6.0), fixed_count=args.count or 0)
        current_summary = "Start"
        current_location = VISUAL_BIBLE.get('background_en', "Professional studio/natural setting")
        
        for i, chunk in enumerate(chunks):
            scenes, current_summary, current_location = get_consistent_prompts(chunk, current_summary, current_location)
            if scenes:
                all_scenes.extend(scenes)
        
        if all_scenes:
            with open(SCENES_PATH, "w", encoding="utf-8") as f:
                json.dump(all_scenes, f, ensure_ascii=False, indent=2)
            print(f"✅ 씬 리스트 생성 완료: {SCENES_PATH}")

    # 2. 이미지 생성 (자동 시작)
    print(f"🚀 이미지 생성을 시작합니다... (대상: {len(all_scenes)}개)")
    print(f"👤 고정 캐릭터 지침: {char_anchor[:100]}...")
    
    futures = []
    with ThreadPoolExecutor(max_workers=4) as executor:
        for i, scene in enumerate(all_scenes):
            # global_num은 1부터 시작
            future = executor.submit(generate_single_image, scene, i + 1, char_anchor)
            futures.append(future)
            time.sleep(0.5)
            
        for future in as_completed(futures):
            res = future.result()
            print(f"{'✅' if res[0] else '❌'} {res[1]}")

if __name__ == "__main__":
    script_path = args.script_path or os.path.join(ROOT_DIR, "대본.txt")
    if os.path.exists(script_path):
        with open(script_path, "r", encoding="utf-8") as f:
            script_text = f.read().strip()
        run_pipeline(script_text, script_name=os.path.basename(script_path))
    else:
        print("❌ 대본 없음.")

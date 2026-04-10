import os
import json
import requests
import google.generativeai as genai
import sys
import re
import time

# [경로 설정]
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# core_v2/engine -> core_v2 -> root
CORE_DIR = os.path.dirname(SCRIPT_DIR)
ROOT_DIR = os.path.dirname(CORE_DIR)

# [설정 로드] config.json 우선
CONFIG_PATH = os.path.join(ROOT_DIR, "config.json")
GOOGLE_API_KEY = None
ELEVENLABS_API_KEY = None

if os.path.exists(CONFIG_PATH):
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            config = json.load(f)
            GOOGLE_API_KEY = config.get("Gemini_API_KEY")
            ELEVENLABS_API_KEY = config.get("ElevenLabs_API_KEY")
            print(f"✅ 설정 파일 로드 성공: {CONFIG_PATH}")
    except Exception as e:
        print(f"⚠️ 설정 파일 로드 실패: {e}")

# Fallback (Hardcoded - Development only)
if not GOOGLE_API_KEY: GOOGLE_API_KEY = "AIzaSyDOtvWYJaFgSoOmDDQ77QO4i6RoFdWWuOA"
if not ELEVENLABS_API_KEY: ELEVENLABS_API_KEY = "4ac65146a95169cd5530e663dfd89d5b41b05a6d503007f7256861dfc41de97d"

# Gemini 설정
genai.configure(api_key=GOOGLE_API_KEY)
DEFAULT_MODEL = 'gemini-2.0-flash' # [변경] 최신 모델로 고정

# [설정] 
# 태그가 없을 경우 AI가 자동으로 삽입할지 여부
# 태그가 없을 경우 AI가 자동으로 삽입할지 여부 (풍성한 사운드를 위해 True로 변경)
AUTO_INSERT_TAGS = True 

def clean_sfx_name(name):
    """파일명으로 쓸 수 있게 특수문자 제거 (Tuple 처리 추가)"""
    if isinstance(name, tuple):
        name = name[0] # Regex group match일 경우 첫 번째 요소 사용
    if not isinstance(name, str):
        name = str(name)
        
    name = re.sub(r'[\\/*?:"<>|]', "", name)
    name = name.strip().replace(" ", "_").lower()
    return name


def generate_local_sfx(prompt, filename, output_dir="sfx"):
    """[Strict Reuse] 로컬 생성이 비활성화되었습니다."""
    print(f"⚠️ [Strict Mode] 효과음 생성이 비활성화되어 있습니다. 라이브러리 파일만 사용합니다. ({prompt})")
    return False

def generate_local_music(prompt, filename, output_dir="bgm", duration=15):
    """[Strict Reuse] BGM 생성이 비활성화되었습니다."""
    print(f"⚠️ [Strict Mode] BGM 작곡이 비활성화되어 있습니다. ({prompt})")
    return False

def generate_elevenlabs_sfx_real(prompt, filename, output_dir="sfx"):
    """[Strict Reuse] 외부 API 생성이 비활성화되었습니다."""
    return False

def save_elevenlabs_sfx(sfx_prompt, filename, output_dir="sfx"):
    """기존 함수 호환성을 위해 로컬 생성으로 리다이렉트"""
    return generate_local_sfx(sfx_prompt, filename, output_dir)

def auto_insert_sfx_tags(script_text):
    """Gemini를 사용하여 대본에 효과음 태그를 자동 삽입"""
    print("🤖 [AI SFX] 대본을 분석하여 효과음 태그를 삽입합니다...")
    model = genai.GenerativeModel(DEFAULT_MODEL)
    
    prompt = f"""
    You are an expert Sound Designer for audio dramas.
    Analyze the script below and insert [SFX:sound_name] tags where appropriate.
    
    [Rules]
    1. Insert tags for ambient sounds (rain, wind, crowd) and specific actions (footsteps, door_slam, glass_shatter).
    2. Use English for sound names inside tags (e.g., [SFX:footsteps_on_gravel]).
    3. Do NOT change the original text. Just insert tags between sentences.
    4. Density: Add roughly 1 sound effect every 3-4 sentences.
    5. Output the FULL script with tags inserted.
    
    [Script]
    {script_text}
    """
    
    try:
        response = model.generate_content(prompt)
        text_with_tags = response.text
        # 태그가 제대로 들어갔는지 검증
        if "[SFX:" in text_with_tags:
            return text_with_tags
        else:
            print("⚠️ AI가 태그 삽입에 실패했습니다.")
            return script_text
    except Exception as e:
        print(f"❌ AI 태그 생성 중 에러: {e}")
        return script_text

def process_script_sfx(script_text, output_dir="Library/sfx", auto_insert=None):
    """대본의 [SFX:...] 태그를 찾아 자동으로 로컬 생성. 태그가 없으면 AI로 자동 추가."""
    if auto_insert is None:
        auto_insert = AUTO_INSERT_TAGS
        
    # 1. 태그 존재 여부 확인
    matches = re.findall(r'\[(SFX|효과음):([^\]]+)\]', script_text)
    
    # 2. 태그가 없고 자동 모드가 켜져있으면 AI 태그 삽입 수행
    if not matches and auto_insert:
        script_text = auto_insert_sfx_tags(script_text)
        matches = re.findall(r'\[(SFX|효과음):([^\]]+)\]', script_text)
 
    if not matches: return script_text

    print(f"🔍 대본에서 {len(matches)}개의 효과음 태그 발견. 생성을 시작합니다.")
    
    # 3. 각 태그에 대해 오디오 생성 (로컬/API)
    # 기존 sfx_generator.py 엔 generate_local_sfx 만 있는데, 
    # 배포용에선 audio_result.json 브릿지가 없으므로 API 직접 호출로 Fallback 해야 함.
    # 하지만 여기선 generate_local_sfx가 브릿지를 쓰므로, 
    # 윈도우 패키지에선 standalone_generate 함수가 필요함.
    
    # [Smart Reuse] 기존 파일 목록 캐싱
    sfx_lib_dir = os.path.join(CORE_DIR, "Library", "sfx")
    existing_files = []
    if os.path.exists(sfx_lib_dir):
        existing_files = [f for f in os.listdir(sfx_lib_dir) if f.endswith(".mp3")]

    for prompt in matches:
        clean_name = clean_sfx_name(prompt)
        target_path = os.path.join(CORE_DIR, "Library", "sfx", f"{clean_name}.mp3")
        
        if not os.path.exists(target_path):
             # 1. 스마트 재사용 시도
             reused = False
             if existing_files:
                 best_match = find_best_match_sfx(prompt, existing_files)
                 if best_match:
                     src_path = os.path.join(sfx_lib_dir, best_match)
                     if os.path.exists(src_path):
                         import shutil
                         shutil.copy2(src_path, target_path)
                         print(f"♻️  기존 효과음 재사용: {best_match} -> {clean_name}.mp3")
                         reused = True
             
             # 2. 재사용 실패 시 새로 생성
             if not reused:
                 # ElevenLabs 제거 요청: 로컬 브릿지 바로 사용
                 # success = generate_elevenlabs_sfx_real(prompt, clean_name)
                 generate_local_sfx(prompt, clean_name)

    return script_text

def find_best_match_sfx(target_prompt, existing_files):
    """Gemini를 사용해 요청된 효과음과 가장 유사한 기존 파일을 찾음 (한글 키워드 우선 매칭)"""
    
    # 0. 빠른 키워드 매칭 (한국어 -> 영어 파일명)
    keyword_map = {
        "오토바이": "motorcycle", "바이크": "motorcycle", "엔진": "engine",
        "빗소리": "rain", "비": "rain", "천둥": "thunder", "뇌우": "thunder",
        "발자국": "footstep", "걷는": "footstep", "뛰는": "run",
        "문": "door", "여는": "open", "닫는": "close", "노크": "knock",
        "유리": "glass", "깨지는": "shatter", "파편": "debris",
        "총": "gun", "발사": "shot", "폭발": "explosion", "붐": "boom",
        "칼": "sword", "검": "sword", "휘두르는": "whoosh", "베는": "slash",
        "바람": "wind", "폭풍": "storm", "산들바람": "breeze",
        "물": "water", "강": "river", "파도": "wave", "첨벙": "splash",
        "비명": "scream", "소리치는": "shout", "숨소리": "breath",
        "심장": "heartbeat", "두근": "heartbeat",
        "종": "bell", "시계": "clock", "초침": "tick",
        "불": "fire", "타는": "burn", "장작": "wood",
        "호텔": "lobby", "로비": "lobby", "키보드": "keyboard", "엔터": "keyboard",
        "무릎": "kneel", "절": "bow", "명함": "card", "타이핑": "typing"
    }
    
    if isinstance(target_prompt, tuple):
        target_prompt = target_prompt[1] if len(target_prompt) > 1 else target_prompt[0]

    target_clean = re.sub(r'[^\w\s]', '', str(target_prompt)).strip()
    
    # 키워드가 포함되어 있으면 해당 영어 단어가 포함된 파일을 우선 검색
    for kor, eng in keyword_map.items():
        if kor in target_clean:
            # 영어 파일명에 해당 키워드가 포함된 것 찾기
            matches = [f for f in existing_files if eng in f.lower()]
            if matches:
                # 가장 짧은(가장 기본에 가까운) 파일명 선택
                best = min(matches, key=len)
                print(f"⚡️ [Fast Match] '{kor}' -> '{best}' (키워드 매칭)")
                return best

    try:
        model = genai.GenerativeModel(DEFAULT_MODEL)
        
        # 파일 목록이 너무 많으면 토큰 절약을 위해 일부만 보낼 수도 있지만, 
        # 일단 텍스트라 수백개 정도는 괜찮음.
        files_str = ", ".join(existing_files)
        
        prompt = f"""
        You are an expert Audio Engineer.
        Target Sound: "{target_prompt}"
        Existing Files: [{files_str}]
        
        Task:
        1. Determine if ANY of the 'Existing Files' is a semantically close match for the 'Target Sound'.
        2. "Close match" means the sound is interchangeable (e.g., 'footsteps_on_grass' can replace 'walking_softly').
        3. If a match exists, return ONLY the filename.
        4. If NO good match exists, return "None".
        
        Output format: Just the filename or None. No explanation.
        """
        
        response = model.generate_content(prompt)
        result = response.text.strip()
        
        if result and result.lower() != "none" and result in existing_files:
            return result
        else:
            return None
    except Exception as e:
        print(f"⚠️ 스마트 매칭 실패: {e}")
        return None



def suggest_bgm_mood(text_context):
    return "Cinematic piano"

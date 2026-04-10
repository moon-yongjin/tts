import os
import json
import requests
import google.generativeai as genai
import sys
import re

# [필수 설정] API 키 입력
GOOGLE_API_KEY = "AIzaSyDOtvWYJaFgSoOmDDQ77QO4i6RoFdWWuOA"
ELEVENLABS_API_KEY = "4ac65146a95169cd5530e663dfd89d5b41b05a6d503007f7256861dfc41de97d"

# Gemini 설정
genai.configure(api_key=GOOGLE_API_KEY)

# [경로 설정]
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CORE_DIR = os.path.dirname(SCRIPT_DIR)

def generate_local_sfx(prompt, filename, output_dir="sfx"):
    """로컬 AudioGen 서버 브릿지를 통해 효과음 생성"""
    BRIDGE_DIR = os.path.join(CORE_DIR, "..", "bridge")
    REQUEST_FILE = os.path.join(BRIDGE_DIR, "sfx_request.json")
    RESULT_FILE = os.path.join(BRIDGE_DIR, "sfx_result.json")
    
    if not os.path.exists(BRIDGE_DIR): os.makedirs(BRIDGE_DIR)
    if os.path.exists(RESULT_FILE): os.remove(RESULT_FILE)

    request_data = {
        "prompt": prompt,
        "output_name": f"{filename}.mp3"
    }

    print(f"📡 로컬 효과음 서버에 요청 중: {prompt}")
    with open(REQUEST_FILE, "w", encoding="utf-8") as f:
        json.dump(request_data, f, ensure_ascii=False, indent=2)
    
    # 결과 대기 (최대 60초)
    start_wait = time.time()
    while time.time() - start_wait < 60:
        if os.path.exists(RESULT_FILE):
            with open(RESULT_FILE, "r", encoding="utf-8") as f:
                result = json.load(f)
            if result.get("status") == "success":
                temp_audio = result.get("audio")
                if temp_audio and os.path.exists(temp_audio):
                    # 라이브러리 폴더로 이동
                    target_path = os.path.join(CORE_DIR, "Library", output_dir, f"{filename}.mp3")
                    if not os.path.exists(os.path.dirname(target_path)):
                        os.makedirs(os.path.dirname(target_path))
                    
                    import shutil
                    shutil.copy2(temp_audio, target_path)
                    print(f"✅ 효과음 생성 및 라이브러리 저장 완료: {filename}.mp3")
                    return True
        time.sleep(0.5)
    
    print("⏰ 효과음 생성 타임아웃 또는 서버 미응답")
    return False

def generate_local_music(prompt, filename, output_dir="bgm", duration=15):
    """통합 오디오 서버를 통해 배경음악(BGM) 생성"""
    BRIDGE_DIR = os.path.join(CORE_DIR, "..", "bridge")
    REQUEST_FILE = os.path.join(BRIDGE_DIR, "audio_request.json")
    RESULT_FILE = os.path.join(BRIDGE_DIR, "audio_result.json")
    
    if not os.path.exists(BRIDGE_DIR): os.makedirs(BRIDGE_DIR)
    if os.path.exists(RESULT_FILE): os.remove(RESULT_FILE)

    request_data = {
        "type": "music",
        "prompt": prompt,
        "output_name": f"{filename}.mp3",
        "duration": duration
    }

    print(f"📡 로컬 오디오 서버에 BGM 작곡 요청 중: {prompt}")
    with open(REQUEST_FILE, "w", encoding="utf-8") as f:
        json.dump(request_data, f, ensure_ascii=False, indent=2)
    
    # 음악 생성은 시간이 더 걸릴 수 있으므로 120초 대기
    start_wait = time.time()
    while time.time() - start_wait < 120:
        if os.path.exists(RESULT_FILE):
            with open(RESULT_FILE, "r", encoding="utf-8") as f:
                result = json.load(f)
            if result.get("status") == "success":
                temp_audio = result.get("audio")
                if temp_audio and os.path.exists(temp_audio):
                    target_path = os.path.join(CORE_DIR, "Library", output_dir, f"{filename}.mp3")
                    if not os.path.exists(os.path.dirname(target_path)):
                        os.makedirs(os.path.dirname(target_path))
                    import shutil
                    shutil.copy2(temp_audio, target_path)
                    print(f"✅ BGM 작곡 및 라이브러리 저장 완료: {filename}.mp3")
                    return True
        time.sleep(1.0)
    
    print("⏰ BGM 생성 타임아웃 또는 서버 미응답")
    return False

def save_elevenlabs_sfx(sfx_prompt, filename, output_dir="sfx"):
    """기존 함수 호환성을 위해 로컬 생성으로 리다이렉트"""
    return generate_local_sfx(sfx_prompt, filename, output_dir)

def process_script_sfx(script_text, output_dir="Library/sfx"):
    """대본의 [SFX:...] 태그를 찾아 자동으로 로컬 생성"""
    matches = re.findall(r'\[SFX:([^\]]+)\]', script_text)
    if not matches: return script_text

    print(f"🔍 대본에서 {len(matches)}개의 효과음 태그 발견. 생성을 시작합니다.")
    for prompt in matches:
        clean_name = clean_sfx_name(prompt)
        generate_local_sfx(prompt, clean_name)
    
    return script_text

def suggest_bgm_mood(text_context):
    return "Cinematic piano"

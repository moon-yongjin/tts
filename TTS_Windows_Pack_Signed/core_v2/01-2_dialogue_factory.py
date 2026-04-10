import os
import re
import requests
import json
import time
from datetime import datetime

# [설정]
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJ_ROOT = os.path.dirname(SCRIPT_DIR)
DOWNLOAD_DIR = os.path.join(os.path.expanduser("~"), "Downloads", "무협_대사_일레븐렙스")

# ⚠️ ElevenLabs는 토큰 소모가 크므로, 현재는 로컬 Qwen-TTS 서버만 사용하도록 강제함.
# API_KEY = "..." 
# VOICE_ID = "..."
# MODEL_ID = "eleven_multilingual_v2"

if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)
    print(f"📂 저장 폴더 생성: {DOWNLOAD_DIR}")

def extract_dialogue(text):
    """대본에서 따옴표 안에 있는 대사만 정확하게 추출"""
    print(f"DEBUG: 대본 길이 - {len(text)} 자")
    
    # 따옴표 기반 추출 (이중, 단일, 한국식 따옴표만 허용)
    # 닫는 따옴표가 나올 때까지 최단 매칭(non-greedy) - 탭/개행 문자 포함 허용
    pattern_quotes = r'["“”\'‘’](.*?)["“”\'‘’]'
    all_matches = re.findall(pattern_quotes, text, re.DOTALL)
    
    # 2자 미만이거나 너무 긴(나레이션급 300자 초과) 것 필터링
    all_matches = [m.strip() for m in all_matches if 2 <= len(m.strip()) <= 300]
    
    print(f"DEBUG: 추출 결과 - 따옴표 기반 ({len(all_matches)})")
    
    seen = set()
    dialogues = []
    for m in all_matches:
        m = m.strip()
        # 불필요한 태그 제거
        m = re.sub(r'\[.*?\]', '', m).strip()
        if len(m) >= 2 and m not in seen:
            dialogues.append(m)
            seen.add(m)
            print(f"DEBUG: 추출된 대사 -> {m[:30]}...")
            
    return dialogues

def generate_voice(text, filename):
    """로컬 Qwen-TTS Bridge 호출 (파일 기반 통신)"""
    output_path = os.path.join(DOWNLOAD_DIR, f"{filename}.mp3")
    
    if os.path.exists(output_path):
        print(f"⏭️ {filename} 이미 존재함.")
        return True

    # Qwen Bridge 경로 설정
    BRIDGE_DIR = os.path.join(PROJ_ROOT, "bridge")
    REQUEST_FILE = os.path.join(BRIDGE_DIR, "qwen_request.json")
    RESULT_FILE = os.path.join(BRIDGE_DIR, "qwen_result.json")
    
    if not os.path.exists(BRIDGE_DIR):
        os.makedirs(BRIDGE_DIR)

    # 요청 데이터 생성
    request_data = {
        "text": text,
        "output_name": f"Dialogue_{filename}.mp3"
    }

    try:
        # 기존 결과 파일 제거
        if os.path.exists(RESULT_FILE):
            os.remove(RESULT_FILE)

        # 요청 파일 쓰기
        with open(REQUEST_FILE, "w", encoding="utf-8") as f:
            json.dump(request_data, f, ensure_ascii=False, indent=2)
        
        print(f"⏳ Qwen 브릿지 대기 중... ({filename})")
        
        # 결과 파일 폴링 (최대 60초)
        start_wait = time.time()
        while time.time() - start_wait < 60:
            if os.path.exists(RESULT_FILE):
                with open(RESULT_FILE, "r", encoding="utf-8") as f:
                    result = json.load(f)
                
                if result.get("status") == "success":
                    temp_audio = result.get("audio")
                    if temp_audio and os.path.exists(temp_audio):
                        import shutil
                        shutil.copy2(temp_audio, output_path)
                        print(f"✅ 생성 및 복사 완료: {filename}.mp3")
                        return True
                else:
                    print(f"❌ Qwen 처리 실패: {result.get('message')}")
                    return False
            time.sleep(0.5)
            
        print(f"⏰ Qwen 브릿지 타임아웃 ({filename})")
        return False

    except Exception as e:
        print(f"⚠️ 브릿지 통신 오류: {e}")
        return False

def run_dialogue_generation(script_path):
    if not os.path.exists(script_path):
        print(f"❌ 대본 파일을 찾을 수 없습니다: {script_path}")
        return

    # 가끔 BOM(Byte Order Mark)이 있는 경우를 대비해 utf-8-sig 사용
    try:
        with open(script_path, "r", encoding="utf-8-sig") as f:
            content = f.read()
    except UnicodeDecodeError:
        with open(script_path, "r", encoding="cp949") as f:
            content = f.read()

    dialogues = extract_dialogue(content)
    print(f"🔍 총 {len(dialogues)}개의 대사 추출 완료.")

    for i, line in enumerate(dialogues):
        # 파일명을 대사 일부로 생성 (특수문자 제거)
        clean_name = re.sub(r'[^a-zA-Z가-힣0-9]', '', line)[:15]
        filename = f"{i+1:03d}_{clean_name}"
        
        print(f"🎙️ [{i+1}/{len(dialogues)}] 생성 중: {line[:20]}...")
        generate_voice(line, filename)
        # API 부하 방지
        time.sleep(0.5)

if __name__ == "__main__":
    target_script = os.path.join(PROJ_ROOT, "대본.txt")
    run_dialogue_generation(target_script)
    print(f"\n✨ 모든 대사 생성 작업이 완료되었습니다.")
    print(f"📍 폴더: {DOWNLOAD_DIR}")

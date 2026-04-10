import pyautogui
import pyperclip
import time
import os
import sys

# --- CONFIGuration ---
# 프롬프트 파일 (그록용)
PROMPT_FILE = "/Users/a12/projects/tts/대본_en.txt"
# 생성 대기 시간 (초) - 그록 영상 생성 속도에 맞춰 60~90초 추천
GEN_WAIT_SEC = 60 
# 시작 전 준비 시간 (초)
PREP_WAIT_SEC = 10

# pyautogui 안전 장치
pyautogui.FAILSAFE = True

def load_prompts(file_path):
    if not os.path.exists(file_path):
        # 대본.txt 폴백
        file_path = "/Users/a12/projects/tts/대본.txt"
        if not os.path.exists(file_path):
            print(f"❌ 파일을 찾을 수 없습니다: {file_path}")
            return []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    parsed = [line.strip() for line in lines if line.strip()]
    return parsed

def start_bot():
    print("==========================================")
    print("🚀 [Grok Turbo] 파이썬 타이핑 깡패 봇 가동!")
    print(f"📂 대상 파일: {PROMPT_FILE}")
    print("==========================================")
    
    prompts = load_prompts(PROMPT_FILE)
    if not prompts:
        print("🛑 처리할 프롬프트가 없습니다. 종료합니다.")
        return

    print(f"✅ 총 {len(prompts)}개의 파트를 로드했습니다.")
    print("-" * 40)
    print(f"⚠️ 중요: {PREP_WAIT_SEC}초 안에 그록(Grok) 입력창을 클릭하세요!")
    print("⚠️ 마우스를 구석으로 밀면 즉시 중단됩니다.")
    print("-" * 40)

    # 카운트다운
    for i in range(PREP_WAIT_SEC, 0, -1):
        print(f"⏳ 시작 {i}초 전...", end='\r')
        time.sleep(1)
    print("\n🔥 가동 시작!")

    for idx, prompt in enumerate(prompts):
        print(f"[{idx+1}/{len(prompts)}] 입력 중: {prompt[:30]}...")

        # 1. 클립보드 복사
        pyperclip.copy(prompt)
        
        # 2. 붙여넣기
        if sys.platform == 'darwin':
            pyautogui.hotkey('command', 'v')
        else:
            pyautogui.hotkey('ctrl', 'v')
            
        time.sleep(2) # 입력 안정화 대기

        # 3. 전송 (Enter)
        pyautogui.press('enter')
        print(f"✅ 전송 완료. {GEN_WAIT_SEC}초 대기 중...")

        # 4. 생성 대기
        time.sleep(GEN_WAIT_SEC)

    print("\n🎉 모든 작업이 완료되었습니다!")

if __name__ == "__main__":
    try:
        import pyautogui
        import pyperclip
    except ImportError:
        print("❌ 라이브러리 누락. 설치를 진행하세요.")
        sys.exit(1)
        
    start_bot()

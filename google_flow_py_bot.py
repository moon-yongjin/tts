import pyautogui
import pyperclip
import time
import os
import sys

# --- CONFIGURATION ---
# 프롬프트 파일 경로 (클린 버전)
PROMPT_FILE = "/Users/a12/projects/tts/google_flow_pro/dasibom_prompts_CLEAN.txt"
# 생성 대기 시간 (초) - 구글 생성 속도에 맞춰 넉넉히 35~40초 추천
GEN_WAIT_SEC = 35 
# 시작 전 준비 시간 (초)
PREP_WAIT_SEC = 10

# pyautogui 안전 장치 (마우스를 화면 모서리로 급하게 옮기면 중단됩니다)
pyautogui.FAILSAFE = True

def load_prompts(file_path):
    if not os.path.exists(file_path):
        print(f"❌ 파일을 찾을 수 없습니다: {file_path}")
        return []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    parsed = []
    for line in lines:
        if '|' in line:
            parts = line.split('|')
            if len(parts) >= 3:
                # 번호 | 메모 | 프롬프트 순서
                prompt_text = parts[2].strip()
                parsed.append(prompt_text)
    return parsed

def start_bot():
    print("🚀 [Google Flow] 파이썬 타이빙 깡패 모드 시작!")
    print(f"📂 대상 파일: {PROMPT_FILE}")
    
    prompts = load_prompts(PROMPT_FILE)
    if not prompts:
        print("🛑 처리할 프롬프트가 없습니다. 종료합니다.")
        return

    print(f"✅ 총 {len(prompts)}개의 프롬프트를 로드했습니다.")
    print("-" * 40)
    print(f"⚠️ 중요: {PREP_WAIT_SEC}초 안에 구글 플로우 입력창을 클릭하세요!")
    print("⚠️ 중단하려면 마우스를 화면 구석(끝)으로 확 밀어버리세요.")
    print("-" * 40)

    # 카운트다운
    for i in range(PREP_WAIT_SEC, 0, -1):
        print(f"⏳ 시작 {i}초 전...", end='\r')
        time.sleep(1)
    print("\n🔥 가동 시작!")

    for idx, prompt in enumerate(prompts):
        print(f"[{idx+1}/{len(prompts)}] 입력 중: {prompt[:30]}...")

        # 1. 클립보드에 복사
        pyperclip.copy(prompt)
        
        # 2. 붙여넣기 (맥 기준 Command+V)
        if sys.platform == 'darwin':
            pyautogui.hotkey('command', 'v')
        else:
            pyautogui.hotkey('ctrl', 'v')
            
        time.sleep(1.5) # 에셋 메뉴 팝업 대기

        # 3. 에셋 호출 확정 (Enter)
        # @[Asset]이 포함된 경우 구글 메뉴가 뜨면 Enter로 선택하게 됨
        pyautogui.press('enter')
        time.sleep(1)

        # 4. 최종 전송 (Enter)
        pyautogui.press('enter')
        print(f"✅ 전송 완료. {GEN_WAIT_SEC}초 대기 중...")

        # 5. 생성 대기
        time.sleep(GEN_WAIT_SEC)

    print("\n🎉 모든 작업이 완료되었습니다!")

if __name__ == "__main__":
    try:
        import pyautogui
        import pyperclip
    except ImportError:
        print("❌ 필요한 라이브러리가 없습니다.")
        print("설치 명령: /Users/a12/projects/tts/venv_dt/bin/pip install pyautogui pyperclip")
        sys.exit(1)
        
    start_bot()

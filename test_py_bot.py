import pyautogui
import pyperclip
import time
import sys

# 테스트용 단일 프롬프트 (다시, 봄 1장)
TEST_PROMPT = "001 | 하은_기본_고정 | Create a clean character reference sheet in cinematic realistic photography style on a plain light gray background. The character is a Korean female in her late 20s, slim build, natural beauty with a pale face. 8 views (Full body and Head)."

def run_test():
    print("🎯 [Google Flow] 1장 테스트 가동 시작!")
    print(f"📝 테스트 프롬프트: {TEST_PROMPT[:50]}...")
    print("-" * 40)
    print("⏳ 10초 뒤에 타이핑을 시작합니다. 구글 플로우 입력창을 클릭하세요!")
    
    for i in range(10, 0, -1):
        print(f"대기 중... {i}", end='\r')
        time.sleep(1)
    print("\n🚀 타이핑 신호 전송!")

    # 1. 클립보드 복사
    pyperclip.copy(TEST_PROMPT.split('|')[2].strip())
    
    # 2. 붙여넣기 (Mac: Command+V, Win: Ctrl+V)
    if sys.platform == 'darwin':
        pyautogui.hotkey('command', 'v')
    else:
        pyautogui.hotkey('ctrl', 'v')
        
    time.sleep(2)
    
    # 3. 엔터 (에셋 메뉴 확정)
    pyautogui.press('enter')
    time.sleep(1)
    
    # 4. 엔터 (생성 버튼 클릭 대신 엔터)
    pyautogui.press('enter')
    
    print("✅ 테스트 신호 전송 완료. 뚫렸는지 확인해보십시오!")

if __name__ == "__main__":
    try:
        import pyautogui
        import pyperclip
    except ImportError:
        print("라이브러리 로드 실패. venv_dt 환경에서 실행하시거나 설치가 필요합니다.")
        sys.exit(1)
    run_test()

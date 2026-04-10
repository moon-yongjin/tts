"""
02-4-5_grok_pyautogui.py
pyautogui를 사용한 Grok 이미지 업로드 자동화.
업로드 버튼 좌표 클릭 → 파일 경로 입력 → 엔터로 제출.
"""

import os
import time
import random
import subprocess
import pyautogui

INPUT_DIR = os.path.expanduser("~/Downloads/Grok_Video_Input")
GROK_URL  = "https://grok.com"

# ──────────────────────────────────────────────
# ⚠️ 아래 좌표를 직접 맞춰야 합니다
# 방법: 크롬에서 grok.com 열고, 파이썬에서 아래 실행:
#   import pyautogui; time.sleep(3); print(pyautogui.position())
# 이미지 업로드 버튼 위에 마우스를 올려두고 실행하면 좌표가 나옵니다.
# ──────────────────────────────────────────────
UPLOAD_BTN_X = 200  # ← 여기를 실제 업로드 버튼 X 좌표로 변경
UPLOAD_BTN_Y = 900  # ← 여기를 실제 업로드 버튼 Y 좌표로 변경

# 제출 버튼 or 그냥 Enter (현재는 Enter로 처리)
SUBMIT_BTN_X = None  # 엔터키로 처리
SUBMIT_BTN_Y = None


def open_grok_in_chrome():
    """크롬에서 Grok 새 탭 열기"""
    subprocess.Popen(["open", "-a", "Google Chrome", GROK_URL])
    time.sleep(4)


def upload_image(image_path: str) -> bool:
    filename = os.path.basename(image_path)
    print(f"\n📎 업로드 중: {filename}")

    try:
        # 1. 업로드 버튼 클릭 (pyautogui 좌표)
        pyautogui.click(UPLOAD_BTN_X, UPLOAD_BTN_Y)
        time.sleep(1.5)  # 파일 선택창 열릴 때까지 대기

        # 2. 파일 경로 입력 (macOS 파일 선택창에서 Cmd+Shift+G → 경로 붙여넣기)
        pyautogui.hotkey("command", "shift", "g")  # 경로 입력창 열기
        time.sleep(0.5)
        pyautogui.typewrite(image_path, interval=0.03)
        time.sleep(0.3)
        pyautogui.press("enter")   # 경로 이동
        time.sleep(0.5)
        pyautogui.press("enter")   # 파일 선택창에서 '열기' 확인
        time.sleep(2)

        print(f"  ✅ 업로드 완료")

        # 3. 업로드 인식 대기
        time.sleep(random.uniform(2, 3))

        # 4. 입력창 클릭 후 엔터 (제출)
        # 입력창은 업로드 버튼 오른쪽/위 쪽에 있으므로 대략적인 위치 클릭
        # 일반적으로 화면 중앙 근처
        screen_w, screen_h = pyautogui.size()
        pyautogui.click(screen_w // 2, screen_h - 130)  # 입력창 대략적인 위치
        time.sleep(0.5)
        pyautogui.press("enter")

        print(f"  🚀 엔터 전송 완료")
        return True

    except Exception as e:
        print(f"  ❌ 실패: {e}")
        return False


def refresh_grok():
    """Cmd+R로 새로고침"""
    pyautogui.hotkey("command", "r")
    time.sleep(random.uniform(3, 5))


def main():
    os.makedirs(INPUT_DIR, exist_ok=True)

    images = sorted([
        os.path.join(INPUT_DIR, f)
        for f in os.listdir(INPUT_DIR)
        if f.lower().endswith((".png", ".jpg", ".jpeg", ".webp"))
        and os.path.isfile(os.path.join(INPUT_DIR, f))
    ])

    if not images:
        print(f"📉 처리할 이미지 없음: {INPUT_DIR}")
        return

    print(f"📂 총 {len(images)}개 이미지 발견")
    print(f"⚠️  크롬에서 grok.com이 열려 있어야 합니다!")
    input("준비됐으면 엔터를 눌러 시작하세요...")

    success_count = 0
    for idx, img_path in enumerate(images):
        print(f"\n[{idx+1}/{len(images)}]")

        ok = upload_image(img_path)
        if ok:
            success_count += 1

        # 다음 이미지 전 대기 + 새로고침
        wait = random.uniform(12, 18)
        print(f"  💤 {wait:.0f}초 대기 후 새로고침...")
        time.sleep(wait)
        refresh_grok()

    print(f"\n🎉 완료! 성공: {success_count}/{len(images)}")


if __name__ == "__main__":
    main()

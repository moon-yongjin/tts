"""
grok_imagegen_bulk.py
이미지젠 버튼 클릭 → 이미지 업로드 → 엔터 → 5초 후 이미지젠 버튼 재클릭 반복
다운로드 없음. Fire & Forget 방식.
"""

import os
import asyncio
import random
from playwright.async_api import async_playwright

# ─── 설정 ───────────────────────────────────────────────
INPUT_DIR    = os.path.expanduser("~/Downloads/Grok_Video_Input")
CHROME_PORT  = 9222
GROK_URL     = "https://grok.com"
PROMPT_TEXT  = ""       # 공백이면 엔터만 침. 원하면 여기에 프롬프트 입력
FIRE_DELAY   = 5        # 실행 후 대기 초 (기본 5초)
BETWEEN_WAIT = (3, 6)   # 이미지 사이 랜덤 휴식 범위 (초)
# ────────────────────────────────────────────────────────

# 이미지젠 버튼 셀렉터 (좌상단 사이드바 또는 상단 탭)
IMAGEGEN_BTN_SELECTORS = [
    'a[href*="imagine"]',
    'button:has-text("Imagine")',
    'button:has-text("이미지")',
    'nav a:has-text("Imagine")',
    '[data-testid="imagegen-tab"]',
    'a[aria-label*="Imagine"]',
    'a[aria-label*="이미지"]',
]

# 파일 업로드 버튼 셀렉터
UPLOAD_BTN_SELECTORS = [
    'button[aria-label="Attach file"]',
    'button[aria-label="첨부하기"]',
    'button[aria-label="Upload image"]',
    'button[aria-label="이미지 업로드"]',
    'button[aria-label="Attach"]',
    'label[for*="file"]',
]

INPUT_SELECTORS = 'div.ProseMirror, div[contenteditable="true"], textarea'


async def click_imagegen_button(page) -> bool:
    """이미지젠 버튼 클릭 (여러 셀렉터 순차 시도)"""
    for sel in IMAGEGEN_BTN_SELECTORS:
        try:
            btn = page.locator(sel).first
            if await btn.count() > 0:
                await btn.click(timeout=5000)
                print("  ✅ 이미지젠 버튼 클릭 성공")
                await asyncio.sleep(2)
                return True
        except:
            continue
    print("  ⚠️  이미지젠 버튼을 찾지 못했습니다. URL 확인 중...")
    # fallback: URL 직접 이동
    try:
        await page.goto(GROK_URL + "/imagine", wait_until="domcontentloaded", timeout=10000)
        await asyncio.sleep(2)
        print("  🔄 /imagine 페이지로 직접 이동")
        return True
    except:
        return False


async def upload_and_fire(page, image_path: str) -> bool:
    filename = os.path.basename(image_path)
    print(f"\n  📎 이미지: {filename}")

    try:
        # 1. 업로드 버튼 클릭 (여러 셀렉터 시도)
        uploaded = False
        for sel in UPLOAD_BTN_SELECTORS:
            try:
                btn = page.locator(sel).first
                if await btn.count() == 0:
                    continue
                async with page.expect_file_chooser(timeout=8000) as fc_info:
                    await btn.click(force=True)
                fc = await fc_info.value
                await fc.set_files(image_path)
                uploaded = True
                break
            except:
                continue

        # fallback: input[type=file] 직접 찾기
        if not uploaded:
            try:
                file_input = page.locator('input[type="file"]').first
                await file_input.set_input_files(image_path)
                uploaded = True
            except:
                pass

        if not uploaded:
            print("  ❌ 업로드 실패")
            return False

        await asyncio.sleep(1.5)
        print("  ✅ 업로드 완료")

        # 2. 프롬프트 입력 (선택)
        if PROMPT_TEXT.strip():
            try:
                input_box = page.locator(INPUT_SELECTORS).first
                await input_box.focus()
                await input_box.fill(PROMPT_TEXT)
                await asyncio.sleep(0.5)
                print(f"  ✏️  프롬프트 입력 완료")
            except:
                pass

        # 3. 엔터로 전송
        input_box = page.locator(INPUT_SELECTORS).first
        await input_box.focus()
        await page.keyboard.press("Enter")
        print(f"  🚀 전송 완료! {FIRE_DELAY}초 후 다음으로...")

        # 4. Fire & Forget 대기
        await asyncio.sleep(FIRE_DELAY)
        return True

    except Exception as e:
        print(f"  ❌ 에러: {e}")
        return False


async def main():
    os.makedirs(INPUT_DIR, exist_ok=True)

    images = sorted([
        os.path.join(INPUT_DIR, f)
        for f in os.listdir(INPUT_DIR)
        if f.lower().endswith((".png", ".jpg", ".jpeg", ".webp"))
        and os.path.isfile(os.path.join(INPUT_DIR, f))
    ])

    if not images:
        print(f"❌ 처리할 이미지가 없습니다: {INPUT_DIR}")
        print("   위 폴더에 이미지를 넣고 다시 실행하세요.")
        return

    print("==========================================")
    print("🎨 [그록 이미지젠 벌크 Fire & Forget]")
    print(f"   총 {len(images)}장 처리 예정")
    print("==========================================")

    async with async_playwright() as pw:
        try:
            browser = await pw.chromium.connect_over_cdp(f"http://localhost:{CHROME_PORT}")
            context = browser.contexts[0]

            # 기존 Grok 탭 우선 사용
            page = None
            for p in context.pages:
                if "grok.com" in p.url:
                    page = p
                    print("✅ 기존 Grok 탭 연결")
                    break

            if not page:
                page = await context.new_page()
                await page.goto(GROK_URL)
                await asyncio.sleep(4)
                print("🆕 새 Grok 탭 열기")

            await page.bring_to_front()
            success = 0

            for idx, img_path in enumerate(images):
                print(f"\n[{idx+1}/{len(images)}] ─────────────────────")

                # 이미지젠 버튼 클릭 (매 사이클마다)
                ok = await click_imagegen_button(page)
                if not ok:
                    print("  ❌ 이미지젠 접근 실패. 건너뜁니다.")
                    continue

                # 업로드 & 전송
                ok = await upload_and_fire(page, img_path)
                if ok:
                    success += 1

                # 다음 이미지 전 랜덤 휴식
                if idx < len(images) - 1:
                    wait = random.uniform(*BETWEEN_WAIT)
                    print(f"  💤 {wait:.1f}초 대기 중...")
                    await asyncio.sleep(wait)

            print(f"\n==========================================")
            print(f"🎉 완료! 성공: {success}/{len(images)}")
            print(f"   그록 탭에서 결과를 직접 확인하세요.")
            print(f"==========================================")

        except Exception as e:
            print(f"❌ 연결 오류: {e}")
            print("   크롬이 디버그 모드로 실행 중인지 확인하세요:")
            print("   chrome --remote-debugging-port=9222")


if __name__ == "__main__":
    asyncio.run(main())

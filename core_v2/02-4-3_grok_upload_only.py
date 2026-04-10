"""
02-4-3_grok_upload_only.py  (v2 - 파일선택창 방식)
이미지를 하나씩 Grok에 업로드하고 새로고침만 반복합니다.
프롬프트 입력 / 전송 / 다운로드 로직 없음.

수정: input 직접 주입 → 업로드 버튼 클릭 + 파일선택창 방식으로 교체
"""

import os
import asyncio
import argparse
import random
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

INPUT_DIR = os.path.expanduser("~/Downloads/Grok_Video_Input")
GROK_URL  = "https://grok.com"

os.makedirs(INPUT_DIR, exist_ok=True)

# 업로드 버튼 셀렉터 목록 (Grok UI 변경 대비 다중 fallback)
UPLOAD_BTN_SELECTORS = ", ".join([
    'button[aria-label="첨부하기"]',
    'button[aria-label="이미지 업로드"]',
    'button[aria-label="Attach file"]',
    'button[aria-label="Upload image"]',
    'button[aria-label="첨부 파일"]',
    'button[aria-label="Attach"]',
])


async def upload_one(page, image_path: str) -> bool:
    filename = os.path.basename(image_path)
    print(f"\n📎 업로드 시도: {filename}")

    # ── 방법 1: 업로드 버튼 클릭 → 파일선택창 ──
    try:
        upload_btn = page.locator(UPLOAD_BTN_SELECTORS)
        await upload_btn.first.wait_for(state="visible", timeout=10000)

        async with page.expect_file_chooser(timeout=15000) as fc_info:
            await upload_btn.first.click(force=True)
        fc = await fc_info.value
        await fc.set_files(image_path)
        await asyncio.sleep(random.uniform(3, 5))
        print(f"  ✅ [방법1] 파일선택창으로 업로드 완료: {filename}")
        return True

    except Exception as e1:
        print(f"  ⚠️ [방법1] 실패 ({e1}), dispatch_event 시도...")

    # ── 방법 2: dispatch_event 로 클릭 유발 ──
    try:
        upload_btn = page.locator(UPLOAD_BTN_SELECTORS)
        async with page.expect_file_chooser(timeout=15000) as fc_info:
            await upload_btn.first.dispatch_event("click")
        fc = await fc_info.value
        await fc.set_files(image_path)
        await asyncio.sleep(random.uniform(3, 5))
        print(f"  ✅ [방법2] dispatch_event 업로드 완료: {filename}")
        return True

    except Exception as e2:
        print(f"  ⚠️ [방법2] 실패 ({e2}), hidden input 직접 주입 시도...")

    # ── 방법 3: 최후 수단 - hidden input 직접 주입 ──
    try:
        file_input = page.locator('input[type="file"]')
        if await file_input.count() > 0:
            await file_input.first.set_input_files(image_path)
            await asyncio.sleep(random.uniform(3, 5))
            print(f"  ✅ [방법3] hidden input 주입 완료: {filename}")
            return True
        else:
            print(f"  ❌ 업로드 input 요소를 찾을 수 없습니다.")
            return False

    except Exception as e3:
        print(f"  ❌ 모든 업로드 방법 실패: {e3}")
        return False


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=9222)
    args = parser.parse_args()

    # 입력 폴더 이미지 수집
    images = sorted([
        os.path.join(INPUT_DIR, f)
        for f in os.listdir(INPUT_DIR)
        if f.lower().endswith((".png", ".jpg", ".jpeg", ".webp"))
        and os.path.isfile(os.path.join(INPUT_DIR, f))
    ])

    if not images:
        print(f"📉 처리할 이미지가 없습니다: {INPUT_DIR}")
        return

    print(f"📂 총 {len(images)}개 이미지 발견 - 업로드 사이클 시작")

    async with async_playwright() as pw:
        try:
            print(f"🔌 크롬 연결 중 (포트: {args.port})...")
            browser = await pw.chromium.connect_over_cdp(f"http://localhost:{args.port}")
            context = browser.contexts[0]

            # 기존 Grok 탭 찾기
            page = None
            for p in context.pages:
                if "grok.com" in p.url:
                    page = p
                    print("✅ 기존 Grok 탭 발견")
                    break

            if not page:
                print("🆕 새 Grok 탭 열기")
                page = await context.new_page()
                await Stealth().apply_stealth_async(page)
                await page.goto(GROK_URL)
                await asyncio.sleep(5)

            await page.bring_to_front()

            success_count = 0
            for idx, img_path in enumerate(images):
                print(f"\n[{idx+1}/{len(images)}] 처리 시작")

                # 새로고침 후 업로드
                await page.goto(GROK_URL)
                await asyncio.sleep(random.uniform(3, 5))  # 페이지 로딩 대기

                ok = await upload_one(page, img_path)
                if ok:
                    success_count += 1

                # 다음 이미지 전 대기
                wait = random.uniform(5, 10)
                print(f"  💤 {wait:.1f}초 대기 후 다음 이미지...")
                await asyncio.sleep(wait)

            print(f"\n🎉 완료! 업로드 성공: {success_count}/{len(images)}")

        except Exception as e:
            print(f"❌ 연결 오류: {e}")


if __name__ == "__main__":
    asyncio.run(main())

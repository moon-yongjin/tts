"""
02-4-4_grok_upload_and_enter.py
이미지를 하나씩 Grok에 업로드하고 '엔터'를 눌러 전송한 뒤 새로고침을 반복합니다.
프롬프트 입력 없이 순수하게 제출 동작만 수행합니다.
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

# 업로드 버튼 셀렉터 목록
UPLOAD_BTN_SELECTORS = ", ".join([
    'button[aria-label="첨부하기"]',
    'button[aria-label="이미지 업로드"]',
    'button[aria-label="Attach file"]',
    'button[aria-label="Upload image"]',
    'button[aria-label="첨부 파일"]',
    'button[aria-label="Attach"]',
])

# 입력창 셀렉터
INPUT_SELECTORS = 'div.ProseMirror, div[contenteditable="true"], textarea'


async def upload_and_submit(page, image_path: str) -> bool:
    filename = os.path.basename(image_path)
    print(f"\n📎 처리 중: {filename}")

    try:
        # 1. 파일 업로드 (방법 1 시도)
        upload_btn = page.locator(UPLOAD_BTN_SELECTORS)
        await upload_btn.first.wait_for(state="visible", timeout=10000)

        async with page.expect_file_chooser(timeout=15000) as fc_info:
            await upload_btn.first.click(force=True)
        fc = await fc_info.value
        await fc.set_files(image_path)
        
        # 업로드 인식 대기
        await asyncio.sleep(2)
        print(f"  ✅ 업로드 완료")

        # 2. 엔터 입력으로 제출
        print(f"  ⌨️ 엔터 입력 중...")
        
        # 입력창 포커스
        input_box = page.locator(INPUT_SELECTORS).first
        await input_box.focus()
        await asyncio.sleep(0.5)
        
        # 엔터 키 전송
        await page.keyboard.press("Enter")
        await asyncio.sleep(random.uniform(2, 4))
        
        print(f"  🚀 제출 완료")
        return True

    except Exception as e:
        print(f"  ❌ 실패: {e}")
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

    print(f"📂 총 {len(images)}개 이미지 발견 - 업로드 & 제출 사이클 시작")

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
                print(f"\n[{idx+1}/{len(images)}] 처리 유닛")

                # 새로고침 후 시작 (깔끔하게)
                await page.goto(GROK_URL)
                await asyncio.sleep(random.uniform(3, 5))

                ok = await upload_and_submit(page, img_path)
                if ok:
                    success_count += 1

                # 다음 이미지 전 충분한 대기 (업로드가 완료되고 서버가 처리할 시간)
                wait = random.uniform(10, 15)
                print(f"  💤 {wait:.1f}초 대기 후 새로고침...")
                await asyncio.sleep(wait)

            print(f"\n🎉 완료! 성공: {success_count}/{len(images)}")

        except Exception as e:
            print(f"❌ 연결 오류: {e}")


if __name__ == "__main__":
    asyncio.run(main())

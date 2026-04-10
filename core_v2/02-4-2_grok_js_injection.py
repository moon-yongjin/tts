import os
import sys
import asyncio
import argparse
import time
import shutil
import random
from pathlib import Path
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

# 입력 및 출력 폴더 설정
INPUT_DIR = os.path.expanduser("~/Downloads/Grok_Video_Input")
OUTPUT_DIR = os.path.expanduser("~/Downloads/Grok_Generations")
COMPLETED_DIR = os.path.join(INPUT_DIR, "Completed")

os.makedirs(INPUT_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(COMPLETED_DIR, exist_ok=True)

async def human_type(page, selector, text):
    """사람이 타이핑하는 것처럼 한 글자씩 랜덤한 간격으로 입력"""
    element = page.locator(selector).first
    await element.focus()
    for char in text:
        await page.keyboard.type(char)
        await asyncio.sleep(random.uniform(0.05, 0.15))

async def process_image_to_video_v2(page, image_path):
    filename = os.path.basename(image_path)
    print(f"\n🎬 [AutoGrok v2] 파일 처리: {filename}")
    
    try:
        # 1. 파일 업로드 (가장 바닥 단의 input 요소를 찾아 직접 주입 - 가장 안정적)
        print("📎 이미지 주입 중...")
        file_input = page.locator('input[type="file"]')
        await file_input.first.set_input_files(image_path)
        await asyncio.sleep(random.uniform(2, 4))

        # 2. 프롬프트 입력 (JS Injection 방식)
        prompt = "Please animate this image into a high-quality, smooth cinematic 1080p video clip. Ensure natural motion. No strange morphing."
        print(f"✍️ 휴먼 라이크 타이핑 중...")
        
        # ProseMirror 또는 textarea 찾기
        input_selectors = 'div.ProseMirror, div[contenteditable="true"], textarea'
        await page.wait_for_selector(input_selectors, state="visible", timeout=10000)
        
        # JS를 통해 포커스 및 타이핑 시뮬레이션
        await human_type(page, input_selectors, prompt)
        await asyncio.sleep(1)

        # 3. 전송 버튼 클릭 (JS dispatchEvent 사용)
        print("🚀 생성 요청 전송...")
        
        # 키보드 Enter 전송 시도 (가장 자연스러운 방법)
        await page.keyboard.press("Enter")
        await asyncio.sleep(random.uniform(1, 2))

        submit_btn_selectors = 'button[aria-label="제출"], button[aria-label="Submit"], button[aria-label="Grok send"], button[aria-label="Send message"], button[aria-label="보내기"]'
        
        await page.evaluate(f"""(sel) => {{
            const btn = document.querySelector(sel);
            if(btn) {{
                btn.scrollIntoView({{behavior: 'smooth', block: 'center'}});
                btn.dispatchEvent(new MouseEvent('mousedown', {{bubbles: true}}));
                btn.dispatchEvent(new MouseEvent('mouseup', {{bubbles: true}}));
                btn.click();
                return true;
            }}
            return false;
        }}""", submit_btn_selectors)
        
        print("⏳ AI 생성 대기 중... (MutationObserver 가동)")
        
        # 4. 비디오 생성 완료 감지 및 다운로드
        # 비디오 요소가 나타날 때까지 대기
        try:
            await page.wait_for_selector('video', state="visible", timeout=300000)
        except Exception:
            print("❌ 비디오 생성 타임아웃 (5분 초과)")
            return False
            
        await asyncio.sleep(5) # 렌더링 안정화

        print("📥 결과물 다운로드 시도...")
        
        # 다운로드 버튼 클릭 (JS 강제 클릭)
        download_js = """() => {
            const btns = Array.from(document.querySelectorAll('button')).filter(b => 
                (b.getAttribute('aria-label') || '').includes('다운로드') || 
                (b.getAttribute('aria-label') || '').toLowerCase().includes('download')
            );
            if(btns.length > 0) {
                btns[btns.length - 1].click();
                return true;
            }
            return false;
        }"""
        
        async with page.expect_download(timeout=60000) as download_info:
            success = await page.evaluate(download_js)
            if not success:
                print("⚠️ 다운로드 버튼을 찾지 못했습니다.")
                return False
        
        download = await download_info.value
        save_name = f"AutoGrok_{int(time.time())}_{filename}.mp4"
        save_path = os.path.join(OUTPUT_DIR, save_name)
        await download.save_as(save_path)
        
        print(f"✅ 저장 완료: {save_name}")
        return True

    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        return False

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=9222)
    args = parser.parse_args()

    # 입력 디렉토리에서 이미지 검색
    images = sorted([os.path.join(INPUT_DIR, f) for f in os.listdir(INPUT_DIR) 
                   if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')) and os.path.isfile(os.path.join(INPUT_DIR, f))])

    if not images:
        print(f"📉 처리할 이미지가 없습니다. ({INPUT_DIR})")
        return

    print(f"📂 총 {len(images)}개의 이미지를 발견했습니다. 오토그록 모드로 시작합니다.")
    
    async with async_playwright() as p:
        try:
            print(f"🔌 크롬 연결 중... (포트: {args.port})")
            browser = await p.chromium.connect_over_cdp(f"http://localhost:{args.port}")
            context = browser.contexts[0]
            
            page = None
            for p_ctx in context.pages:
                if "grok.com" in p_ctx.url or "x.com/i/grok" in p_ctx.url:
                    page = p_ctx
                    print("✅ 기존 Grok 탭을 찾았습니다.")
                    break
                    
            if not page:
                print("🆕 새 Grok 탭을 엽니다.")
                page = await context.new_page()
                await Stealth().apply_stealth_async(page)
                await page.goto("https://grok.com")
                await asyncio.sleep(5)
            
            await page.bring_to_front()
            
            success_count = 0
            for img_path in images:
                print(f"\n🔄 새로운 이미지 처리를 위해 페이지 새로고침 중...")
                await page.goto("https://grok.com")
                await asyncio.sleep(5) # 로딩 대기
                
                success = await process_image_to_video_v2(page, img_path)
                if success:
                    success_count += 1
                    shutil.move(img_path, os.path.join(COMPLETED_DIR, os.path.basename(img_path)))
                
                delay = random.uniform(10, 20)
                print(f"💤 휴먼 라이크 대기 중 ({delay:.1f}초)...")
                await asyncio.sleep(delay) 

            print(f"\n🎉 작업 완료! (성공: {success_count}/{len(images)})")
            
        except Exception as e:
            print(f"❌ 연결 실패: {e}")

if __name__ == "__main__":
    asyncio.run(main())

import os
import sys
import asyncio
import time
import shutil
from pathlib import Path
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

# 설정
INPUT_DIR = os.path.expanduser("~/Downloads/Grok_Video_Input")
OUTPUT_DIR = os.path.expanduser("~/Downloads/Grok_Generations")
COMPLETED_DIR = os.path.join(INPUT_DIR, "Completed")
PROMPT = "."  # 국장님 요청: 최소 프롬프트로 속도 극대화

os.makedirs(INPUT_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(COMPLETED_DIR, exist_ok=True)

# --------------------------------------------------------------------------------
# Grok-v2 AI Injection Engine (God-Mode)
# --------------------------------------------------------------------------------
GOD_MODE_JS = """
async (args) => {
    const { promptText } = args;
    const findInput = () => document.querySelector('.ProseMirror') || document.querySelector('div[contenteditable="true"]');
    const input = findInput();
    if (!input) return { success: false, error: "Input not found" };

    input.focus();
    input.innerHTML = `<p>${promptText}</p>`;
    input.dispatchEvent(new InputEvent('input', { bubbles: true, inputType: 'insertText', data: promptText }));
    input.dispatchEvent(new Event('change', { bubbles: true }));
    return { success: true };
}
"""

async def process_image(context, image_path):
    filename = os.path.basename(image_path)
    print(f"🎬 [Background] Processing: {filename}")
    
    page = await context.new_page()
    await Stealth().apply_stealth_async(page)
    
    try:
        await page.goto("https://grok.com", wait_until="networkidle")
        
        # 1. AI Injection
        await page.evaluate(GOD_MODE_JS, {"promptText": PROMPT})
        
        # 2. Upload Image
        file_input = page.locator('input[type="file"]')
        await file_input.first.set_input_files(image_path)
        await asyncio.sleep(3)

        # 3. Submit
        submit_btn = page.locator('button[aria-label*="Grok"], button[aria-label*="Submit"], button[aria-label*="전송"]').first
        await submit_btn.click()
        print(f"⏳ [Background] Generation started for {filename}")

        # 4. Wait & Download
        await page.wait_for_selector('video', state="visible", timeout=360000)
        await asyncio.sleep(5)
        
        async with page.expect_download() as download_info:
            await page.locator('button[aria-label*="다운로드"], button[aria-label*="Download"]').last.click()
        download = await download_info.value
        save_path = os.path.join(OUTPUT_DIR, f"SilentGrok_{int(time.time())}_{filename}.mp4")
        await download.save_as(save_path)
        
        shutil.move(image_path, os.path.join(COMPLETED_DIR, filename))
        print(f"✅ [Background] Success: {os.path.basename(save_path)}")
        return True
    except Exception as e:
        print(f"❌ [Background] Error: {e}")
        return False
    finally:
        await page.close()

async def main():
    print("----------------------------------------------------")
    print("🛰️ SilentGrok (Background Mode) 가동 중...")
    print(f"📂 입력 대기: {INPUT_DIR}")
    print("----------------------------------------------------")

    async with async_playwright() as p:
        # Headless=True 로 화면 없이 백그라운드 작업 수행
        browser = await p.chromium.launch(headless=True)
        # 중요: 세션 유지를 위해 디렉토리를 지정하거나, 기존 크롬에 연결할 수 있으나 
        # 백그라운드 '독립' 실행을 위해 전용 컨텍스트 사용
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
        
        # 실제로는 로그인이 필요하므로, 최초 1회는 수동 로그인이 된 프로필을 사용하는 것이 좋음
        # 여기서는 기본 흐름만 구현
        
        while True:
            images = [os.path.join(INPUT_DIR, f) for f in os.listdir(INPUT_DIR) 
                      if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')) and os.path.isfile(os.path.join(INPUT_DIR, f))]
            
            for img in images:
                await process_image(context, img)
            
            await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(main())

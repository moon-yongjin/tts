import os
import sys
import asyncio
import argparse
import time
import shutil
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

# --------------------------------------------------------------------------------
# Constants & Selectors
# --------------------------------------------------------------------------------
PROMPT = "."  # 국장님 요청: 최소 프롬프트로 속도 극대화

UPLOAD_BTN_SELECTORS = [
    'button[aria-label*="첨부"]', 
    'button[aria-label*="Attach"]', 
    'button[aria-label*="이미지"]'
]

INPUT_SELECTORS = [
    'div.ProseMirror',
    'div[contenteditable="true"]',
    'textarea'
]

SUBMIT_BTN_SELECTORS = [
    'button[aria-label="제출"]',
    'button[aria-label="Submit"]',
    'button[aria-label="Grok send"]', 
    'button[aria-label="Send message"]', 
    'button:has-text("Grok")'
]

DOWNLOAD_BTN_SELECTORS = [
    'button[aria-label="다운로드"]',
    'button[aria-label="Download"]',
    'button[aria-label="Download video"]',
    'button[aria-label*="다운로드"]'
]

# --------------------------------------------------------------------------------
# Core Logic
# --------------------------------------------------------------------------------

# --------------------------------------------------------------------------------
# Grok-v2 AI Injection Engine (Designed by Llama-3-70B)
# --------------------------------------------------------------------------------
GOD_MODE_JS = """
async (args) => {
    const { promptText, imagePath } = args;
    const findInput = () => {
        return document.querySelector('.ProseMirror') || 
               document.querySelector('div[contenteditable="true"]') ||
               document.querySelector('div[role="textbox"]');
    };
    const injectText = (el, text) => {
        el.focus();
        el.innerHTML = '';
        const textNode = document.createTextNode(text);
        el.appendChild(textNode);
        el.dispatchEvent(new InputEvent('input', { bubbles: true, inputType: 'insertText', data: text }));
        el.dispatchEvent(new Event('change', { bubbles: true }));
    };
    const target = findInput();
    if (!target) return { success: false, error: "Input area not found" };
    injectText(target, promptText);
    return { success: true };
}
"""

async def process_image_to_video(context, image_path, worker_id):
    filename = os.path.basename(image_path)
    print(f"🚀 [Worker {worker_id}] Processing: {filename}")
    
    page = await context.new_page()
    await Stealth().apply_stealth_async(page)
    
    try:
        await page.goto("https://grok.com", wait_until="networkidle")
        await asyncio.sleep(2)

        # 1. AI-Powered Injection (Text)
        args = {"promptText": PROMPT, "imagePath": image_path}
        inj_result = await page.evaluate(GOD_MODE_JS, args)
        if not inj_result["success"]:
            raise Exception(f"AI Injection Failed: {inj_result.get('error')}")
        
        # 2. 파일 업로드 (Playwright Hijack)
        upload_btn = page.locator(", ".join(UPLOAD_BTN_SELECTORS))
        await upload_btn.first.wait_for(state="visible", timeout=20000)
        
        file_input = page.locator('input[type="file"]')
        await file_input.first.set_input_files(image_path)
        print(f"✅ [Worker {worker_id}] God-Mode Input Successful for {filename}")
        
        await asyncio.sleep(5) 

        # 3. 전송 버튼 클릭
        submit_btn = page.locator(", ".join(SUBMIT_BTN_SELECTORS))
        await submit_btn.first.click()

        print(f"⏳ [Worker {worker_id}] Generation in progress for {filename}...")
        
        # 4. 결과물 대기 및 다운로드
        # Wait up to 6 minutes for video
        await page.wait_for_selector('video', state="visible", timeout=360000)
        await asyncio.sleep(5)

        downloads_btns = page.locator(", ".join(DOWNLOAD_BTN_SELECTORS))
        if await downloads_btns.count() > 0:
             async with page.expect_download() as download_info:
                 await downloads_btns.last.click()
             download = await download_info.value
             save_name = f"FastGrok_{int(time.time())}_{filename}.mp4"
             save_path = os.path.join(OUTPUT_DIR, save_name)
             await download.save_as(save_path)
             
             # Success cleanup
             shutil.move(image_path, os.path.join(COMPLETED_DIR, filename))
             print(f"✅ [Worker {worker_id}] Success: {save_name}")
             return True
        else:
            print(f"⚠️ [Worker {worker_id}] Download button not found for {filename}")
            return False

    except Exception as e:
        print(f"❌ [Worker {worker_id}] Error processing {filename}: {e}")
        return False
    finally:
        await page.close()

async def worker(queue, context, worker_id, semaphore):
    while True:
        image_path = await queue.get()
        async with semaphore:
            await process_image_to_video(context, image_path, worker_id)
        queue.task_done()

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=9222)
    parser.add_argument("--workers", type=int, default=2, help="Number of parallel workers")
    args = parser.parse_args()

    # Find images
    images = [os.path.join(INPUT_DIR, f) for f in sorted(os.listdir(INPUT_DIR)) 
              if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')) and os.path.isfile(os.path.join(INPUT_DIR, f))]

    if not images:
        print(f"📉 No images found in {INPUT_DIR}")
        return

    print(f"📂 Found {len(images)} images. Running with {args.workers} parallel workers.")

    async with async_playwright() as p:
        try:
            print(f"🔌 Connecting to Chrome on port {args.port}...")
            browser = await p.chromium.connect_over_cdp(f"http://localhost:{args.port}")
            
            # 🖼️ FORCE 100% ZOOM & 1080P VIEWPORT (AI Logic)
            # This ensures Grok layout is consistent and doesn't condense to 80% or mobile view.
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                device_scale_factor=1.0,
                is_mobile=False
            )
            
            queue = asyncio.Queue()
            for img in images:
                await queue.put(img)

            semaphore = asyncio.Semaphore(args.workers)
            
            # Start workers
            tasks = []
            for i in range(args.workers):
                task = asyncio.create_task(worker(queue, context, i+1, semaphore))
                tasks.append(task)

            await queue.join()

            # Cancel workers
            for task in tasks:
                task.cancel()
            
            print(f"\n🎉 All tasks processed. Results in: {OUTPUT_DIR}")

        except Exception as e:
            print(f"❌ Connection Failed: {e}")
            print("Make sure Chrome is running with: --remote-debugging-port=9222")

if __name__ == "__main__":
    asyncio.run(main())

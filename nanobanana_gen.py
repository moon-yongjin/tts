import sys
import os
import asyncio
import argparse
from pathlib import Path
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

async def find_or_create_target_page(context):
    """Finds an existing Gemini or AI Studio tab or creates a new one."""
    print(f"DEBUG: Scanning {len(context.pages)} open pages...")
    for page in context.pages:
        url = page.url.lower()
        print(f"DEBUG: Checking page: {url}")
        if "gemini.google.com" in url or "aistudio.google.com" in url:
            print(f"🎯 Found existing tab: {page.url}")
            return page
    
    print("🚀 Opening Gemini...")
    page = await context.new_page()
    try:
        # Reduced timeout and less strict wait condition for the initial hit
        await page.goto("https://gemini.google.com", wait_until="domcontentloaded", timeout=20000)
    except Exception as e:
        print(f"⚠️ Navigation warning: {e}. Attempting to proceed anyway.")
    return page

async def generate_gemini_image(page, prompt, out_dir):
    try:
        url = page.url.lower()
        is_aistudio = "aistudio" in url
        
        print(f"✍️ Sending prompt to {'AI Studio' if is_aistudio else 'Gemini'}: {prompt}")
        
        # Selectors based on site
        if is_aistudio:
            # AI Studio Chat selectors
            textarea = page.locator("div[contenteditable='true'], textarea").first
            send_btn = page.locator("button:has-text('Run'), button[aria-label*='Run']").first
        else:
            # Gemini Chat selectors
            textarea = page.locator("div[contenteditable='true'][aria-label*='프롬프트'], div[contenteditable='true'][aria-label*='Prompt']").first
            send_btn = page.locator("button[aria-label*='프롬프트 보내기'], button[aria-label*='Send prompt']").first
        
        if not await textarea.is_visible(timeout=5000):
            # General fallback
            textarea = page.locator("div[contenteditable='true'], textarea").first

        await textarea.click()
        await textarea.fill(prompt)
        await asyncio.sleep(1)
        
        if not await send_btn.is_visible(timeout=2000):
            await textarea.press("Enter")
        else:
            await send_btn.click()

        print("🕒 Waiting for generation (NanoBanana 2)...")
        # Wait for images to appear in the chat response
        # Gemini usually shows images in a specific container
        image_selector = "img[src*='googleusercontent'], img[alt*='generated']"
        try:
            await page.wait_for_selector(image_selector, timeout=60000)
            await asyncio.sleep(5) # Stabilization
        except:
            print("⚠️ Timeout waiting for image. Checking current images...")

        # Find images in the last response
        images = await page.locator(image_selector).all()
        if not images:
            print("❌ No images found.")
            return 0

        count = 0
        for i, img in enumerate(images[-1:]): # Focus on the latest response
            try:
                # Hover to reveal download options if any
                await img.hover()
                await asyncio.sleep(1)
                
                # Gemini often has a download button or we can grab the src
                # Simplified: Save screenshot of the image element as fallback
                # but better to find the real download button.
                
                filename = f"gemini_{int(asyncio.get_event_loop().time())}.png"
                save_path = os.path.join(out_dir, filename)
                
                # Try to find download button near the image
                # In Gemini/AI Studio, download is often in a menu or a specific button
                download_btn = page.locator("button[aria-label*='다운로드'], button[aria-label*='Download']").last
                
                if await download_btn.is_visible(timeout=2000):
                    async with page.expect_download() as download_info:
                        await download_btn.click()
                    download = await download_info.value
                    await download.save_as(save_path)
                    print(f"✅ Downloaded: {filename}")
                    count += 1
                else:
                    # Generic capture
                    await img.screenshot(path=save_path)
                    print(f"📸 Image captured via screenshot: {filename}")
                    count += 1
            except Exception as e:
                print(f"⚠️ Error processing image {i}: {e}")
        
        return count
    except Exception as e:
        print(f"❌ Generation failed: {e}")
        return 0

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--prompt", required=True, help="Prompt text")
    parser.add_argument("--port", type=int, default=9222)
    parser.add_argument("--out-dir", default=str(Path.home() / "Downloads" / "NanoBanana_Generations"))
    args = parser.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)

    async with async_playwright() as p:
        try:
            print(f"🔗 Connecting to Chrome on port {args.port}...")
            browser = await p.chromium.connect_over_cdp(f"http://localhost:{args.port}")
            context = browser.contexts[0]
            
            page = await find_or_create_target_page(context)
            await Stealth().apply_stealth_async(page)
            
            if "login" in page.url.lower() or "signin" in page.url.lower():
                print("⚠️ Please log in to Gemini/AI Studio in your browser first.")
                return

            # Run generation
            count = await generate_gemini_image(page, args.prompt, args.out_dir)
            
            if count > 0:
                print(f"\n✨ Successfully generated/captured {count} NanoBanana images!")
            else:
                print("\n❌ Failed to generate or download images.")

        except Exception as e:
            print(f"❌ Browser connection error: {e}")

if __name__ == "__main__":
    asyncio.run(main())

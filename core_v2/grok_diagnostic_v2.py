import asyncio
import os
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

async def diagnostic():
    async with async_playwright() as p:
        print("🔌 Connecting to Chrome on port 9222...")
        try:
            browser = await p.chromium.connect_over_cdp("http://localhost:9222")
            context = browser.contexts[0]
            page = context.pages[0] if context.pages else await context.new_page()
            
            await page.bring_to_front()
            if "grok.com" not in page.url and "x.com/i/grok" not in page.url:
                print("🌐 Navigating to Grok...")
                await page.goto("https://grok.com")
            
            print("🔍 Analyzing UI Elements...")
            
            # 1. Check Input Field
            input_found = await page.locator('div[role="textbox"], .ProseMirror, textarea').first.is_visible()
            print(f" - Input Field Visible: {input_found}")
            
            # 2. Check Upload Button
            upload_found = await page.locator('button[aria-label*="첨부"], button[aria-label*="Attach"], button[aria-label*="이미지"]').first.is_visible()
            print(f" - Upload Button Visible: {upload_found}")
            
            # 3. Test Input (without sending)
            if input_found:
                test_text = "Verification Test: " + os.urandom(4).hex()
                target = page.locator('div[role="textbox"], .ProseMirror, textarea').first
                await target.fill(test_text)
                await asyncio.sleep(1)
                
                # Check if it actually filled
                val = await target.inner_text() or await target.input_value()
                if test_text in val:
                    print(f"✅ Input Verification SUCCESS: '{val}' detected.")
                else:
                    print(f"❌ Input Verification FAILED. Expected '{test_text}', got '{val}'")
            
            await browser.close()
        except Exception as e:
            print(f"❌ Diagnostic Failed: {e}")

if __name__ == "__main__":
    asyncio.run(diagnostic())

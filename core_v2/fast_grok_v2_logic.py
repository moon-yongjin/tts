import asyncio
import os
import time
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

# --------------------------------------------------------------------------------
# Grok-v2 AI Injection Engine (Designed by Llama-3-70B)
# --------------------------------------------------------------------------------
GOD_MODE_JS = """
async (args) => {
    const { promptText, imagePath } = args;
    // 1. Generic Input Area Locator (Role-Based)
    const findInput = () => {
        return document.querySelector('div[role="textbox"]') || 
               document.querySelector('.ProseMirror') || 
               document.querySelector('textarea[aria-label*="Grok"]');
    };

    // 2. Human-Like Injection
    const injectText = (el, text) => {
        el.focus();
        el.innerHTML = ''; // Clear
        const textNode = document.createTextNode(text);
        el.appendChild(textNode);
        
        // Trigger multi-stage events to fool React/Vue state observers
        el.dispatchEvent(new InputEvent('input', { bubbles: true, inputType: 'insertText', data: text }));
        el.dispatchEvent(new Event('change', { bubbles: true }));
        console.log("✅ Text Injected & Events Dispatched");
    };

    // 3. Robust File Upload (Hidden Input Hijack)
    const uploadFile = async (filePath) => {
        const fileInput = document.querySelector('input[type="file"]');
        if (!fileInput) return false;
        
        // Note: Playwright handles the actual file set, but we trigger the UI
        console.log("📎 File Input Found");
        return true;
    };

    const target = findInput();
    if (!target) return { success: false, error: "Input area not found" };

    injectText(target, promptText);
    const uploadStatus = await uploadFile(imagePath);

    return { success: true, uploadFound: uploadStatus };
}
"""

async def run_god_mode_test(image_path, text):
    async with async_playwright() as p:
        print("🔌 Connecting to Chrome...")
        try:
            browser = await p.chromium.connect_over_cdp("http://localhost:9222")
            context = browser.contexts[0]
            page = context.pages[0] if context.pages else await context.new_page()
            
            if "grok.com" not in page.url and "x.com/i/grok" not in page.url:
                print("🌐 Navigating to Grok...")
                await page.goto("https://grok.com", wait_until="networkidle")
            
            # Wait for any potential input area to appear
            print("⏳ Waiting for Grok input area...")
            try:
                await page.wait_for_selector('div[role="textbox"], .ProseMirror, textarea', timeout=30000)
            except:
                print("⚠️ Timeout waiting for input area. Checking current state...")

            print(f"🎬 Executing God-Mode Injection on {page.url}...")
            
            # AI-Powered Injection - Passing arguments as a dict
            args = {"promptText": text, "imagePath": image_path}
            result = await page.evaluate(GOD_MODE_JS, args)
            
            if result["success"]:
                print("✅ AI Injection reported SUCCESS.")
                
                # Handle File Upload separately via Playwright (since JS can't read local paths)
                if result["uploadFound"]:
                    file_input = page.locator('input[type="file"]')
                    await file_input.first.set_input_files(image_path)
                    print("📎 Image uploaded via Playwright hijack.")

                # Final Verification
                await asyncio.sleep(2)
                current_val = await page.locator('div[role="textbox"], .ProseMirror').first.inner_text()
                if text[:10] in current_val:
                    print(f"💎 VERIFIED: Text '{text[:10]}...' is physically in the box.")
                else:
                    print(f"❌ VERIFICATION FAILED: Found '{current_val}' instead.")
            else:
                print(f"❌ AI Injection ERROR: {result.get('error')}")

        except Exception as e:
            print(f"❌ System Failure: {e}")

if __name__ == "__main__":
    # Test with a dummy text
    asyncio.run(run_god_mode_test("/Users/a12/Downloads/reference.png", "Hello Grok! This is an AI-powered high-intelligence test."))

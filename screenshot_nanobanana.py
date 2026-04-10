import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        try:
            browser = await p.chromium.connect_over_cdp("http://localhost:9222")
            context = browser.contexts[0]
            page = None
            for p_ctx in context.pages:
                if "nanobanana.im" in p_ctx.url:
                    page = p_ctx
                    break
            
            if not page:
                page = await context.new_page()
                await page.goto("https://nanobanana.im", wait_until="networkidle")

            await page.screenshot(path="nanobanana_screenshot.png", full_page=True)
            print("✅ Screenshot saved to nanobanana_screenshot.png")

        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())

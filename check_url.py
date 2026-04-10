import asyncio
from playwright.async_api import async_playwright

async def check(page, url):
    print(f"--- Checking {url} ---")
    try:
        await page.goto(url, wait_until="networkidle", timeout=15000)
        print(f"Final URL: {page.url}")
        print(f"Title: {await page.title()}")
    except Exception as e:
        print(f"Error checking {url}: {e}")

async def main():
    async with async_playwright() as p:
        try:
            browser = await p.chromium.connect_over_cdp("http://localhost:9222")
            context = browser.contexts[0]
            page = await context.new_page()
            
            await check(page, "https://nanobanana.ai")
            await check(page, "https://nanobanana.im")
            
            await page.close()
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())

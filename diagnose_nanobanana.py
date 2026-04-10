import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        try:
            browser = await p.chromium.connect_over_cdp("http://localhost:9222")
            context = browser.contexts[0]
            page = None
            for p_ctx in context.pages:
                url = p_ctx.url.lower()
                print(f"DEBUG: Found page with URL: {url}")
                if "aistudio.google.com" in url or "gemini.google.com" in url:
                    page = p_ctx
                    break
            
            if not page:
                print("❌ NanoBanana page not found.")
                return

            # Extract basic structure
            content = await page.content()
            with open("nanobanana_structure.html", "w", encoding="utf-8") as f:
                f.write(content)
            
            # Deep scan interactive elements within all frames
            elements = await page.evaluate("""async () => {
                const results = [];
                const scanFrame = (frame) => {
                    const inputs = Array.from(frame.querySelectorAll('input, textarea, button, [role="button"], [contenteditable="true"]')).map(el => ({
                        tag: el.tagName,
                        id: el.id,
                        className: el.className,
                        placeholder: el.placeholder || '',
                        text: el.innerText || el.value || '',
                        ariaLabel: el.getAttribute('aria-label') || '',
                        frameUrl: window.location.href
                    }));
                    results.push(...inputs);
                };

                scanFrame(document);
                // Note: Security might block cross-domain iframe access via JS
                return results;
            }""")
            
            # Use Playwright's own frame iteration for cross-domain iframes
            all_elements = []
            for frame in page.frames:
                try:
                    print(f"🔍 Scanning frame: {frame.url}")
                    frame_elements = await frame.evaluate("""() => {
                        return Array.from(document.querySelectorAll('input, textarea, button, [role="button"], [contenteditable="true"]')).map(el => ({
                            tag: el.tagName,
                            id: el.id,
                            className: el.className,
                            placeholder: el.placeholder || '',
                            text: el.innerText || el.value || '',
                            ariaLabel: el.getAttribute('aria-label') || ''
                        }));
                    }""")
                    for e in frame_elements:
                        e['frameUrl'] = frame.url
                    all_elements.extend(frame_elements)
                except:
                    print(f"⚠️ Could not scan frame: {frame.url}")

            import json
            with open("nanobanana_elements.json", "w", encoding="utf-8") as f:
                json.dump(all_elements, f, indent=2, ensure_ascii=False)
            
            print("✅ Diagnostics complete. Saved to nanobanana_structure.html and nanobanana_elements.json")

        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())

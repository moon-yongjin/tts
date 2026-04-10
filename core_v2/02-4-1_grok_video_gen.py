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

async def process_image_to_video(page, image_path):
    filename = os.path.basename(image_path)
    print(f"\n🎬 [Grok 처리 시작] 파일: {filename}")
    
    try:
        # 1. 파일 업로드
        print("📎 이미지를 업로드 중입니다...")
        
        # 파일 첨부 버튼 클릭 방식 (다양한 언어 및 변경된 Selector 대응)
        upload_btn_selectors = [
            'button[aria-label="첨부하기"]', 
            'button[aria-label="이미지 업로드"]', 
            'button[aria-label="Attach file"]', 
            'button[aria-label="Upload image"]',
            'button[aria-label="첨부 파일"]'
        ]
        upload_btn = page.locator(", ".join(upload_btn_selectors))
        
        # 버튼이 보일 때까지 대기
        await upload_btn.first.wait_for(state="visible", timeout=15000)
        
        # 1-1. 표준 클릭 방식 + 이벤트 대기
        print("👆 업로드 버튼 클릭 시도 중...")
        try:
            async with page.expect_file_chooser(timeout=20000) as fc_info:
                await upload_btn.first.click(force=True)
            file_chooser = await fc_info.value
            await file_chooser.set_files(image_path)
            print("✅ 표준 클릭으로 파일 선택 완료")
        except Exception as e:
            print(f"⚠️ 표준 클릭 실패 ({e}), 대체 방식(dispatch_event) 시도...")
            # 1-2. 대체 방식: 자바스크립트 이벤트를 직접 발생시킴
            try:
                async with page.expect_file_chooser(timeout=20000) as fc_info:
                    await upload_btn.first.dispatch_event('click')
                file_chooser = await fc_info.value
                await file_chooser.set_files(image_path)
                print("✅ dispatch_event 방식으로 파일 선택 완료")
            except Exception as e2:
                # 1-3. 최종 수단: 숨겨진 input[type="file"]을 직접 찾아 파일 설정
                print(f"⚠️ 두 번째 방식도 실패 ({e2}), 직접 input 요소 탐색...")
                file_input = page.locator('input[type="file"]')
                if await file_input.count() > 0:
                    await file_input.first.set_input_files(image_path)
                    print("✅ hidden input 직접 주입 성공")
                else:
                    raise Exception("모든 업로드 방식이 실패했습니다. Grok UI가 크게 변경되었을 수 있습니다.")
            
        await asyncio.sleep(4) # 업로드 완료 및 썸네일 생성 대기

        # 2. 프롬프트 입력
        prompt = "Please animate this image into a high-quality, smooth cinematic 1080p video clip. Ensure natural motion. No strange morphing."
        print(f"✍️ 프롬프트 전송 중: {prompt}")
        
        # Grok은 ProseMirror(div) 또는 textarea를 사용함
        input_selectors = [
            'div.ProseMirror',
            'div[contenteditable="true"]',
            'textarea'
        ]
        text_input = page.locator(", ".join(input_selectors))
        await text_input.first.wait_for(state="visible", timeout=5000)
        await text_input.first.fill(prompt)
        await asyncio.sleep(1)
        
        # 3. 전송 버튼 클릭
        submit_btn_selectors = [
            'button[aria-label="제출"]',
            'button[aria-label="Submit"]',
            'button[aria-label="Grok send"]', 
            'button[aria-label="Send message"]', 
            'button:has-text("Grok")'
        ]
        submit_btn = page.locator(", ".join(submit_btn_selectors))
        await submit_btn.first.wait_for(state="visible", timeout=5000)
        await submit_btn.first.click()

        print("⏳ AI 생성 중... (Grok 서버 상황에 따라 1~3분 소요)")
        
        # 4. 결과물 대기 및 다운로드
        # 생성된 최근응답 영역에 비디오가 뜨기를 기다립니다.
        await page.wait_for_selector('video', state="visible", timeout=300000)
        await asyncio.sleep(5) # 완전히 렌더링될 때까지 여유

        print("📥 비디오 다운로드 처리 중...")
        
        download_btn_selectors = [
            'button[aria-label="다운로드"]',
            'button[aria-label="Download"]',
            'button[aria-label="Download video"]',
            'button[aria-label*="다운로드"]'
        ]
        downloads_btns = page.locator(", ".join(download_btn_selectors))
        if await downloads_btns.count() > 0:
             async with page.expect_download() as download_info:
                 await downloads_btns.last.click()
             download = await download_info.value
             save_name = f"Grok_{int(time.time())}_{filename}.mp4"
             save_path = os.path.join(OUTPUT_DIR, save_name)
             await download.save_as(save_path)
             print(f"✅ 비디오 저장 완료: {save_path}")
             return True
        else:
            print("⚠️ 다운로드 버튼을 찾지 못했습니다. 수동으로 다운로드해야 할 수 있습니다.")
            return False

    except Exception as e:
        print(f"❌ 처리 중 오류 발생: {e}")
        return False

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=9222)
    args = parser.parse_args()

    # 입력 디렉토리에서 이미지 검색 (알파벳 순 정렬)
    images = []
    for f in sorted(os.listdir(INPUT_DIR)):
        if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
            full_path = os.path.join(INPUT_DIR, f)
            if os.path.isfile(full_path):
                images.append(full_path)

    if not images:
        print(f"📉 처리할 이미지가 없습니다. ({INPUT_DIR} 폴더에 이미지를 넣어주세요.)")
        return

    print(f"📂 총 {len(images)}개의 이미지를 발견했습니다.")
    
    async with async_playwright() as p:
        try:
            print(f"🔌 크롬 브라우저 연결 중... (포트: {args.port})")
            browser = await p.chromium.connect_over_cdp(f"http://localhost:{args.port}")
            context = browser.contexts[0]
            
            page = None
            
            # grok 탭 찾기
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
                print("⚠️ 로그인이 필요할 수 있습니다. 브라우저를 확인하세요.")
                await asyncio.sleep(3)
            
            # 포커스 맞추기
            await page.bring_to_front()
            
            success_count = 0
            for img_path in images:
                success = await process_image_to_video(page, img_path)
                if success:
                    success_count += 1
                    # 완료된 파일 이동
                    filename = os.path.basename(img_path)
                    shutil.move(img_path, os.path.join(COMPLETED_DIR, filename))
                
                print("💤 5초 대기 후 다음 이미지 처리...")
                await asyncio.sleep(5) 

            print(f"\n🎉 모든 작업 완료! (성공: {success_count}/{len(images)})")
            
        except Exception as e:
            print(f"❌ 브라우저 연결 실패: {e}")
            print(f"크롬이 디버그 모드(포트 {args.port})로 실행 중인지 확인하세요.")
            print("명령어: /Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome --remote-debugging-port=9222")

if __name__ == "__main__":
    asyncio.run(main())

import os
import asyncio
import shutil
import glob
import json
from playwright.async_api import async_playwright

# 설정
INPUT_DIR = os.path.expanduser("~/Downloads/Grok_Video_Input")
COMPLETED_DIR = os.path.join(INPUT_DIR, "Completed")
PROMPT = "."

os.makedirs(INPUT_DIR, exist_ok=True)
os.makedirs(COMPLETED_DIR, exist_ok=True)

async def find_or_create_grok_page(context):
    """
    브라우저 컨텍스트 내에서 Grok 페이지를 찾거나 새로 생성합니다.
    """
    # 1. 기존 페이지들 뒤져보기
    for page in context.pages:
        if "grok.com" in page.url:
            print(f"🔗 [연결] 기존 Grok 탭을 발견했습니다: {page.url}")
            return page
    
    # 2. 없으면 새로 열기
    print("🆕 [신규] Grok Imagine 페이지를 새로 엽니다.")
    page = await context.new_page()
    await page.goto("https://grok.com/imagine", wait_until="networkidle")
    return page

async def process_one_image(context, image_path):
    filename = os.path.basename(image_path)
    print(f"🚀 [작업] {filename} 분석 및 업로드 시작...")
    
    try:
        page = await find_or_create_grok_page(context)
        
        # 1. 파일 업로드
        file_input = page.locator('input[type="file"]')
        await file_input.first.set_input_files(image_path)
        print(f"📎 [첨부] {filename} 업로드 완료")
        
        # UI 반응 대기 (이미지에 따라 로딩 시간 필요)
        await asyncio.sleep(4) 

        # 2. 영상 모드 선택 (이미지 업로드 후 노출됨)
        try:
            # 텍스트 '영상' 또는 'Video' 포함 요소 클릭
            video_btn = page.get_by_text("영상", exact=False).first
            if await video_btn.is_visible():
                await video_btn.click()
                print("🎬 [모드] 영상 생성 모드로 전환")
        except:
            pass

        # 3. 프롬프트 입력 및 전송
        input_area = page.locator('.ProseMirror')
        await input_area.fill(PROMPT)
        await page.keyboard.press("Enter")
        print(f"🔥 [완료] {filename} 전송 성공!")

        # 4. 파일 이동
        shutil.move(image_path, os.path.join(COMPLETED_DIR, filename))
        
    except Exception as e:
        print(f"❌ [오류] {filename} 처리 실패: {e}")

async def main():
    print("---------------------------------------------------------")
    print("🚀 Grok Simple Turbo v1.1 (God-Tier Sync Fix)")
    print("---------------------------------------------------------")

    # 1. 크롬 실제 프로필 경로 찾기
    chrome_base = os.path.expanduser("~/Library/Application Support/Google/Chrome")
    target_profile = "Default"
    
    # Default 외에 Profile 1 등이 사용 중일 수 있으므로 탐색
    profile_dirs = glob.glob(os.path.join(chrome_base, "Profile *"))
    if profile_dirs:
        # 가장 최근에 사용된(수정된) 프로필 폴더 선택
        profile_dirs.append(os.path.join(chrome_base, "Default"))
        target_profile_path = max(profile_dirs, key=os.path.getmtime)
        target_profile = os.path.basename(target_profile_path)
    else:
        target_profile_path = os.path.join(chrome_base, "Default")

    print(f"📂 [동기화] 사용 중인 프로필({target_profile})을 복제합니다...")

    temp_profile_path = os.path.join(os.path.expanduser("~"), "Grok_Turbo_Session")
    if os.path.exists(temp_profile_path):
        shutil.rmtree(temp_profile_path, ignore_errors=True)
    
    # 세션 복구에 필수적인 파일들만 최소한으로 복사
    os.makedirs(temp_profile_path, exist_ok=True)
    essential_items = [
        'Cookies', 'Cookies-journal', 'Local Storage', 
        'Session Storage', 'Network', 'Sync Data', 'Preferences'
    ]
    
    for item in essential_items:
        src = os.path.join(target_profile_path, item)
        dst = os.path.join(temp_profile_path, item)
        try:
            if os.path.isdir(src):
                shutil.copytree(src, dst, dirs_exist_ok=True)
            elif os.path.exists(src):
                shutil.copy2(src, dst)
        except Exception as e:
            # 파일 잠금 등은 무시하고 진행
            pass

    # 잠금 파일 제거 (동시 실행 가능하게 함)
    for lock in glob.glob(os.path.join(temp_profile_path, "*lock*")):
        try: os.remove(lock)
        except: pass

    async with async_playwright() as p:
        print("🔗 [연결] 브라우저를 실행합니다...")
        # 런처 옵션
        context = await p.chromium.launch_persistent_context(
            user_data_dir=temp_profile_path,
            headless=False,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-session-crashed-bubble",
                "--disable-infobars"
            ]
        )

        while True:
            # 처리할 파일 목록 가져오기
            files = [f for f in os.listdir(INPUT_DIR) 
                     if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))
                     and os.path.isfile(os.path.join(INPUT_DIR, f))]
            
            if files:
                for f in files:
                    await process_one_image(context, os.path.join(INPUT_DIR, f))
                    await asyncio.sleep(2) # 간격 조절
            
            await asyncio.sleep(5) # 폴더 감시 간격

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 프로그램을 종료합니다.")

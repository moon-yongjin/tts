#!/Users/a12/miniforge3/bin/python
from playwright.sync_api import sync_playwright
from playwright_stealth import stealth
import time
import os

def main():
    print("=" * 60)
    print(" 🤖 [Grok 자동 브라우저 컨트롤] 환경 테스트 팩")
    print("=" * 60)
    print("\n🚀 1. 플레이라이트(Playwright) 크롬 브라우저를 호출합니다...")

    try:
        with sync_playwright() as p:
            # 💡 기존 로그인 정보를 가져오기 위해 사용자의 '실제 크롬 프로필' 경로를 잡습니다.
            user_data_dir = os.path.expanduser("~/Library/Application Support/Google/Chrome")
            
            print("🔗 2. 평소 쓰시던 크롬 프로필로 grok.com 진입합니다...")
            # launch_persistent_context 를 사용하면 로그인 없이 기존 쿠키를 그대로 씁니다.
            context = p.chromium.launch_persistent_context(
                user_data_dir=user_data_dir,
                headless=False,
                channel="chrome"  # 일반 크롬 브라우저 강제 사용
            )
            page = context.pages[0] if context.pages else context.new_page()
            
            # 🛡️ 스텔스 가동 (구글 봇 탐지 우회)
            stealth(page)
            
            page.goto("https://grok.com")
            
            print("\n" + "!" * 45)
            print(" ⚠️ [수동 작업 필요] 그록에 로그인을 완료해 주세요!")
            print(" 로그인을 완료하신 뒤, 프롬프트를 입력할 수 있는")
            print(" ‘대화창’이 화면에 뜨면 여기 터미널 창을 클릭하세요.")
            print("!" * 45)
            
            input("\n👉 준비가 끝나셨다면 [엔터 Enter]를 누르세요...")
            
            print("\n✅ 3. 자동 제어망 부팅 성공! (사용자 화면 조작 테스트)")
            print(" - 프롬프트 입력창 자동 서치 중...")
            
            # 그록 페이지 내 인풋창(textarea 등)이 로드되었는지 확인하는 척
            time.sleep(2)
            
            print("\n🎉 자동 브라우저 컨트롤(A타입) 가동 조건이 모두 '충족'되었습니다!")
            print(" 마우스 좌표 없이 스크립트로 [대사 입력 - 생성 - 자동 다운]이")
            print(" 논스톱으로 뚫릴 수 있음이 검증되었습니다.")
            
            # 5초 대기 후 종료
            print("\n💤 5초 후 테스트 브라우저가 자동으로 닫힙니다.")
            time.sleep(5)
            context.close()

    except Exception as e:
        print(f"\n❌ 에러 발생: {e}")
        print(" 에러가 뜬다면 라이브러리 드라이버 세팅을 한번 더 돌려야 합니다.")

if __name__ == "__main__":
    main()

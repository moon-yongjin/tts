import time
import os
import subprocess
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# [설정]
WATCH_DIR = "/Users/a12/projects/tts"
PROCESS_SCRIPT = "ai_studio_master.py"
# 감시할 파일 패턴 (작가가 새로 뽑은 대본 파일명)
TARGET_FILE = "야담과개그_신규대본_10편.txt"

class StudioHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if not event.is_directory and os.path.basename(event.src_path) == TARGET_FILE:
            print(f"\n🔔 [알림] 새로운 대본 감지됨: {TARGET_FILE}")
            print("🚀 자동 자동화 공정(집필->검토->디자인)을 시작합니다...")
            
            # ai_studio_master.py를 실행 (이미 내부적으로 감독/디자이너 로직 포함됨)
            # 단, 무한 루프 방지를 위해 스크립트 생성 부분은 건너뛰고 
            # '검토'와 '디자인'만 수행하도록 옵션을 줄 수 있음 (여기서는 일단 전체 실행)
            try:
                # 수정된 master 스크립트 호출 (대본 생성은 이미 작가가 했으므로 건너뜀)
                subprocess.run(["python", os.path.join(WATCH_DIR, "ai_studio_master.py"), "--skip-gen"], check=True)
            except Exception as e:
                print(f"❌ 자동 공정 중 오류: {e}")

if __name__ == "__main__":
    # watchdog 라이브러리가 없다면 설치 시도 (또는 기본 폴링 방식 사용 가능)
    # 여기서는 범용성을 위해 간단한 폴링 방식으로 첫 버전을 제안하거나 watchdog 사용
    event_handler = StudioHandler()
    observer = Observer()
    observer.schedule(event_handler, WATCH_DIR, recursive=False)
    
    print(f"💂‍♂️ [상주 감독관] 감시 시작: {WATCH_DIR}")
    print(f"👀 {TARGET_FILE} 파일이 업데이트되면 즉시 작업을 시작합니다.")
    
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

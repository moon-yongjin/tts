import os
import json
import requests
import time
import sys

# [윈도우 호환성]
if sys.stdout.encoding.lower() != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BASE_PATH = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(BASE_PATH)
CONFIG_PATH = os.path.join(ROOT_DIR, "config.json")

# Config 로드
RUNPOD_API_KEY = ""
if os.path.exists(CONFIG_PATH):
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            config = json.load(f)
            RUNPOD_API_KEY = config.get("RunPod_API_KEY", "")
    except: pass

if not RUNPOD_API_KEY:
    print("❌ RunPod API Key를 찾을 수 없습니다. config.json을 확인하세요.")
    sys.exit(1)

def get_latest_folder():
    base_downloads = os.path.join(os.path.expanduser("~"), "Downloads")
    subdirs = [os.path.join(base_downloads, d) for d in os.listdir(base_downloads) 
               if os.path.isdir(os.path.join(base_downloads, d)) and d.startswith("무협_세로_")]
    if subdirs:
        latest = sorted(subdirs)[-1]
        if time.time() - os.path.getctime(latest) < 86400: # 24시간 이내
            return latest
    return None

DOWNLOAD_DIR = get_latest_folder()
if not DOWNLOAD_DIR:
    _timestamp = time.strftime("%m%d_%H%M")
    DOWNLOAD_DIR = os.path.join(os.path.expanduser("~"), "Downloads", f"무협_세로_{_timestamp}")
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def download_file(url, save_path):
    print(f"⬇️  다운로드 시작: {url}")
    try:
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            total_size = int(r.headers.get('content-length', 0))
            downloaded = 0
            
            with open(save_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            percent = int(downloaded * 100 / total_size)
                            sys.stdout.write(f"\r   진행률: {percent}% ({downloaded}/{total_size} bytes)")
                            sys.stdout.flush()
        print("\n✅ 다운로드 완료!")
        return True
    except Exception as e:
        print(f"\n❌ 다운로드 실패: {e}")
        return False

def check_status_and_download(job_id):
    headers = {
        "Authorization": f"Bearer {RUNPOD_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # 1. 상태 확인 (엔드포인트는 serverless ID에 따라 다를 수 있으나, status API는 공통)
    # 보통 https://api.runpod.ai/v2/{ENDPOINT_ID}/status/{JOB_ID} 형식이지만,
    # 여기서는 Job ID가 전체 Global Unique ID라고 가정하거나, 
    # 사용자가 Endpoint ID를 포함한 전체 URL을 모를 수 있으므로
    # 가장 일반적인 Status Check 방식을 시도합니다.
    
    # [중요] RunPod Serverless는 Endpoint ID가 필수입니다.
    # 사용자가 Job ID만 입력했을 때 Endpoint ID를 모르면 조회가 불가능할 수 있습니다.
    # 따라서 입력받을 때 "Endpoint ID"와 "Job ID"를 같이 받거나,
    # config.json에 ENDPOINT_ID를 저장해두어야 합니다.
    
    # 임시: config에서 ENDPOINT_ID 가져오기 시도
    ENDPOINT_ID = config.get("RunPod_Endpoint_ID", "")
    if not ENDPOINT_ID:
        # 사용자에게 입력 요청
        print("\n⚠️  RunPod Endpoint ID가 설정되지 않았습니다.")
        print("   (예: vllm-xyz123 또는 config.json에 'RunPod_Endpoint_ID' 추가)")
        ENDPOINT_ID = input("👉 Endpoint ID를 입력하세요: ").strip()
    
    if not ENDPOINT_ID:
        print("❌ Endpoint ID가 없어 진행할 수 없습니다.")
        return

    url = f"https://api.runpod.ai/v2/{ENDPOINT_ID}/status/{job_id}"
    
    print(f"\n🔍 Job Status 확인 중... (ID: {job_id})")
    
    while True:
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            status = data.get("status")
            print(f"   현재 상태: {status}")
            
            if status == "COMPLETED":
                output = data.get("output")
                # output이 딕셔너리고 'message'나 'file_url', 'video_url' 등이 있을 수 있음
                # 워크플로우에 따라 output 형식이 다름.
                # 여기서는 output이 문자열(URL)이거나, 
                # {'video': 'url'} 또는 {'file_url': 'url'} 형태라고 가정하고 파싱 시도
                
                download_url = None
                if isinstance(output, str) and output.startswith("http"):
                    download_url = output
                elif isinstance(output, dict):
                    # 일반적인 키들 검색
                    for key in ['video', 'video_url', 'file_url', 'url', 'download_link', 'output_url']:
                        if key in output and isinstance(output[key], str) and output[key].startswith("http"):
                            download_url = output[key]
                            break
                    
                    # 만약 못 찾으면 첫 번째 value가 url인지 확인
                    if not download_url:
                        for v in output.values():
                            if isinstance(v, str) and v.startswith("http"):
                                download_url = v
                                break
                
                if download_url:
                    print(f"🎉 작업 완료! 결과물 URL 발견: {download_url}")
                    save_path = os.path.join(DOWNLOAD_DIR, "Final_Output.mp4")
                    if download_file(download_url, save_path):
                        print(f"📂 저장 위치: {save_path}")
                    break
                else:
                    print(f"⚠️ 작업은 완료되었으나 다운로드 URL을 찾을 수 없습니다.")
                    print(f"   Output 데이터: {output}")
                    break
                    
            elif status == "FAILED":
                print("❌ 작업이 실패했습니다.")
                print(f"   에러: {data.get('error')}")
                break
                
            elif status in ["IN_PROGRESS", "IN_QUEUE"]:
                time.sleep(5) # 5초 대기 후 재시도
                
            else:
                print(f"❓ 알 수 없는 상태: {status}")
                if status == "CANCELLED": break
                time.sleep(5)
                
        except Exception as e:
            print(f"❌ API 요청 중 오류 발생: {e}")
            break

def watch_directory():
    print(f"\n👀 [감나빗 모드] 폴더 감시 중: {DOWNLOAD_DIR}")
    print("👉 런팟에서 'Final_Output.mp4' 파일이 이 폴더에 생기면 즉시 납치합니다.")
    print("   (취소하려면 Ctrl+C)")
    
    target_file = "Final_Output.mp4"
    target_path = os.path.join(DOWNLOAD_DIR, target_file)
    
    # 0.5초 간격으로 무한 루프
    while True:
        if os.path.exists(target_path):
            # 파일이 전송 중일 수 있으므로 사이즈가 안정될 때까지 대기
            initial_size = -1
            while True:
                current_size = os.path.getsize(target_path)
                if current_size == initial_size and current_size > 0:
                    break
                initial_size = current_size
                time.sleep(1) # 1초 대기 후 사이즈 재확인
                
            print(f"\n🎉 [포착] 파일이 감지되었습니다! ({initial_size} bytes)")
            print(f"✅ 다운로드 완료 처리: {target_path}")
            return
        time.sleep(0.5)

def main():
    # 사용자님이 주신 포드 ID
    POD_ID = "4j0uvlhn1s17wd"
    
    # 1. 커맨드라인 인자 확인
    job_id_arg = None
    if "--job" in sys.argv:
        idx = sys.argv.index("--job")
        if idx + 1 < len(sys.argv):
            job_id_arg = sys.argv[idx + 1]

    if job_id_arg:
        print(f"🎯 커맨드라인에서 Job ID 감지: {job_id_arg}")
        check_status_and_download(job_id_arg)
        return

    # 2. 포드 정보 출력 및 감시 모드
    print(f"\n📂 로컬 다운로드 폴더: {DOWNLOAD_DIR}")
    print(f"📡 런팟 포드 ID: {POD_ID}")
    print(f"🔗 파일 브라우저 (8080): https://{POD_ID}-8080.proxy.runpod.net")
    print(f"--------------------------------------------------")
    
    if len(sys.argv) > 1 and sys.argv[1] == "--manual":
        print("1. [추천] 감시 모드 (파일 생기면 자동 종료)")
        print("2. Job ID 입력 (API 자동 다운로드)")
        print("3. 수동 다운로드 (링크 입력)")
        print("--------------------------------------------------")
        
        choice = input("👉 번호를 선택하세요 (기본 1): ").strip()
        
        if choice == "2":
            job_id = input("👉 RunPod Job ID를 입력하세요: ").strip()
            if job_id: check_status_and_download(job_id)
        elif choice == "3":
            url = input("👉 다운로드 링크(URL)를 입력하세요: ").strip()
            if url:
                save_path = os.path.join(DOWNLOAD_DIR, "Final_Output.mp4")
                download_file(url, save_path)
        else:
            watch_directory()
    else:
        # [기본] 즉시 감시 모드 진입
        watch_directory()

if __name__ == "__main__":
    print("🚀 RunPod Final Video Downloader v2.4 (Pod Aware)")
    main()

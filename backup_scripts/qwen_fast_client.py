import os
import json
import time
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BRIDGE_DIR = os.path.join(BASE_DIR, "bridge")
REQ_FILE = os.path.join(BRIDGE_DIR, "qwen_request.json")
RES_FILE = os.path.join(BRIDGE_DIR, "qwen_result.json")

def request_generation(script_file):
    if not os.path.exists(script_file):
        print(f"❌ 파일을 찾을 수 없습니다: {script_file}")
        return

    with open(script_file, "r", encoding="utf-8") as f:
        text = f.read().strip()

    timestamp = time.strftime("%m%d_%H%M")
    output_name = f"{os.path.splitext(os.path.basename(script_file))[0]}_Fast_{timestamp}.mp3"

    data = {
        "text": text,
        "output_name": output_name
    }

    # 기존 결과 파일 삭제
    if os.path.exists(RES_FILE): os.remove(RES_FILE)

    # 요청 작성
    with open(REQ_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print("📡 서버에 생성을 요청했습니다. 잠시만 기다려 주세요...")
    
    # 결과 대기
    start_wait = time.time()
    while not os.path.exists(RES_FILE):
        if time.time() - start_wait > 600: # 10분 타임아웃
            print("❌ 서버 응답 시간 초과. qwen_instant_server.py가 실행 중인지 확인하세요.")
            return
        time.sleep(0.5)

    with open(RES_FILE, "r", encoding="utf-8") as f:
        res = json.load(f)

    if res.get("status") == "success":
        print(f"✅ 생성 완료! 소요시간: {res.get('elapsed', 0):.1f}초")
        print(f"📂 파일: {res.get('audio')}")
    else:
        print(f"❌ 오류 발생: {res.get('message')}")

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "대본.txt"
    request_generation(target)

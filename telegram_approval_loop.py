import os
import time
import requests
import subprocess
from pathlib import Path
from dotenv import load_dotenv

# 1. 경로 설정
PROJ_ROOT = Path("/Users/a12/projects/tts")
CORE_V2_DIR = PROJ_ROOT / "core_v2"
load_dotenv(os.path.join(CORE_V2_DIR, ".env"))

# 2. 텔레그램 설정
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

# 3. 작업 파일 설정
SCRIPT_GEN_CMD = ["/Users/a12/projects/tts/qwen3-tts-apple-silicon/.venv/bin/python3", "seq_script_gen.py"]
NEW_SCRIPT_FILE = PROJ_ROOT / "야담과개그_신규대본_1편.txt"
FINAL_SCRIPT_FILE = PROJ_ROOT / "대본.txt"
# 승인 시 실행할 TTS 커맨드
TTS_CMD = ["/Users/a12/projects/tts/qwen3-tts-apple-silicon/.venv/bin/python3", "1-3-55_ZeroShot_Angry_New_TTS.py"]

def send_telegram_with_buttons(text):
    """대본과 함께 [승인], [반려] 버튼 전송"""
    url = f"{API_URL}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": f"📜 **[신규 대본 도착]**\n\n{text}\n\n위 대본을 승인하시겠습니까?",
        "parse_mode": "Markdown",
        "reply_markup": {
            "inline_keyboard": [
                [
                    {"text": "✅ 승인 (음성 생성 시작)", "callback_data": "approve"},
                    {"text": "❌ 반려 (다시 작성)", "callback_data": "reject"}
                ]
            ]
        }
    }
    try:
        r = requests.post(url, json=payload)
        return r.json().get("result", {}).get("message_id")
    except Exception as e:
        print(f"❌ 텔레그램 전송 실패: {e}")
        return None

def wait_for_approval(message_id):
    """국장님의 응답이 올 때까지 폴링하며 무한 대기"""
    print("⏳ 국장님의 승인을 기다리는 중 (Telegram)...")
    offset = None
    while True:
        url = f"{API_URL}/getUpdates"
        params = {"timeout": 30, "offset": offset}
        try:
            r = requests.get(url, params=params, timeout=35)
            updates = r.json().get("result", [])
            for update in updates:
                offset = update["update_id"] + 1
                
                # Callback Query 처리 (버튼 클릭)
                if "callback_query" in update:
                    cb = update["callback_query"]
                    # 우리가 보낸 메시지에 대한 응답인지 확인
                    if cb.get("message", {}).get("message_id") == message_id:
                        data = cb.get("data")
                        # 응답 처리 알림 (시계 표시 제거)
                        requests.post(f"{API_URL}/answerCallbackQuery", json={"callback_query_id": cb["id"]})
                        return data
                
                # 텍스트 메시지로도 응답 가능하게 처리 ("승인", "반려")
                if "message" in update and "text" in update["message"]:
                    msg_text = update["message"]["text"]
                    if "승인" in msg_text or "ok" in msg_text.lower():
                        return "approve"
                    if "반려" in msg_text or "다시" in msg_text:
                        return "reject"
                        
            time.sleep(1)
        except Exception as e:
            print(f"⚠️ 폴링 오류 (재시도 중): {e}")
            time.sleep(5)

def run_process():
    print("🚀 [대본 승인 루프] 가동 시작")
    
    while True:
        # 1. 대본 생성
        print("✍️ 작가 에이전트 가동 (대본 생성 중)...")
        subprocess.run(SCRIPT_GEN_CMD, cwd=PROJ_ROOT)
        
        if not NEW_SCRIPT_FILE.exists():
            print("❌ 대본 생성 파일이 없습니다. 재시도합니다.")
            time.sleep(5)
            continue
            
        with open(NEW_SCRIPT_FILE, "r", encoding="utf-8") as f:
            script_content = f.read()
            
        # 2. 텔레그램 전송
        msg_id = send_telegram_with_buttons(script_content[:3500]) # 텔레그램 글자수 제한 고려
        if not msg_id:
            print("❌ 텔레그램 메시지 전송 실패. 10초 후 재시도.")
            time.sleep(10)
            continue
            
        # 3. 승인 대기
        choice = wait_for_approval(msg_id)
        
        if choice == "approve":
            print("✅ 국장님 승인 완료! 음성 합성 단계로 진입합니다.")
            requests.post(f"{API_URL}/sendMessage", json={"chat_id": CHAT_ID, "text": "✅ 승인되었습니다. 음성 생성을 시작합니다!"})
            
            # 대본 확정 (대본.txt 덮어쓰기)
            with open(FINAL_SCRIPT_FILE, "w", encoding="utf-8") as f:
                f.write(script_content)
                
            # 음성 생성 실행
            print("🎙️ 음성 합성 엔진 가동...")
            subprocess.run(TTS_CMD, cwd=PROJ_ROOT)
            
            requests.post(f"{API_URL}/sendMessage", json={"chat_id": CHAT_ID, "text": "🎉 음성 및 자막 생성이 완료되었습니다! Downloads 폴더를 확인하세요."})
            print("✨ 한 사이클 완료. 다음 대본을 위해 대기합니다.")
            
        else:
            print("❌ 국장님 반려. 대본을 다시 작성합니다.")
            requests.post(f"{API_URL}/sendMessage", json={"chat_id": CHAT_ID, "text": "♻️ 반려되었습니다. 새로운 대본을 다시 집필합니다."})
            # 루프가 처음으로 돌아가서 다시 생성함

if __name__ == "__main__":
    try:
        run_process()
    except KeyboardInterrupt:
        print("\n👋 프로세스를 종료합니다.")

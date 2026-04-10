import sys
import os
import json
import time
import requests
import html

TELEGRAM_TOKEN = "8515076340:AAHp4TH200xUzO5i9MeSbBSeX9K2hlJbg80"
TELEGRAM_CHAT_ID = "7793202015"
API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

def wait_for_approval(script_file):
    print("⏳ [Telegram Approval] 국장님의 결재를 기다리는 중입니다...")
    
    visual_report = ""
    # 구형 보고서와 신형 비주얼 아키텍트 보고서 모두 지원
    if os.path.exists("visual_concept_report.md"):
        with open("visual_concept_report.md", "r", encoding="utf-8") as f:
            visual_report = f.read()
    elif os.path.exists("visual_report.txt"):
        with open("visual_report.txt", "r", encoding="utf-8") as f:
            visual_report = f.read()

    director_report = ""
    if os.path.exists("director_report.txt"):
        with open("director_report.txt", "r", encoding="utf-8") as f:
            director_report = f.read()

    if not os.path.exists(script_file):
        print(f"❌ 대본 파일이 없습니다: {script_file}")
        return 1
        
    with open(script_file, "r", encoding="utf-8") as f:
        script_text = f.read()

    # HTML 이스케이프 처리 (특수 기호로 인한 발송 실패 방지)
    safe_script = html.escape(script_text)
    safe_director = html.escape(director_report)
    safe_visual = html.escape(visual_report)

    # [1] 대본 전문 및 결재 버튼 통합 발송
    # HTML 이스케이프 처리
    safe_script = html.escape(script_text)
    
    script_msg = (
        f"📜 <b>[대본 결재 요청]</b>\n\n"
        f"<i>{safe_script}</i>\n\n"
        "────────────────────\n"
        "💡 <b>수정 제안은 이 메시지에 '답장'으로 주세요.</b>\n"
        "마음에 드시면 아래 버튼을 눌러 승인하십시오."
    )

    reply_markup = {
        "inline_keyboard": [
            [
                {"text": "👍 승인 (제작 시작)", "callback_data": "approve_tts"},
                {"text": "❌ 반려 (대본 다시 쓰기)", "callback_data": "reject_tts"}
            ]
        ]
    }

    try:
        resp = requests.post(
            f"{API_URL}/sendMessage",
            json={
                "chat_id": TELEGRAM_CHAT_ID,
                "text": script_msg,
                "parse_mode": "HTML",
                "reply_markup": reply_markup
            }
        ).json()
        
        if not resp.get("ok"):
            print(f"❌ 텔레그램 발송 실패: {resp}")
            return 1
            
        message_id = resp["result"]["message_id"]
    except Exception as e:
        print(f"❌ 텔레그램 통신 오류: {e}")
        return 1

    offset = None
    timeout_minutes = 30
    start_time = time.time()
    
    while time.time() - start_time < timeout_minutes * 60:
        try:
            updates_resp = requests.get(
                f"{API_URL}/getUpdates",
                params={"offset": offset, "timeout": 30}
            ).json()
            
            if not updates_resp.get("ok"):
                time.sleep(2)
                continue
                
            updates = updates_resp.get("result", [])
            for update in updates:
                offset = update["update_id"] + 1
                
                # 1. 텍스트 답장 처리 (수정 지시 루프)
                if "message" in update and "reply_to_message" in update["message"]:
                    reply = update["message"]
                    if reply["reply_to_message"]["message_id"] == message_id:
                        feedback = reply.get("text", "")
                        if feedback:
                            print(f"📝 국장님의 수정 지시 접수: {feedback}")
                            # 피드백 저장 및 재생성 신호 (Exit Code 2)
                            with open("user_feedback.txt", "w", encoding="utf-8") as f:
                                f.write(feedback)
                            
                            requests.post(f"{API_URL}/sendMessage", json={
                                "chat_id": TELEGRAM_CHAT_ID,
                                "text": f"🫡 <b>수정 지시 접수!</b>\n\n'<i>{feedback}</i>'\n내용을 반영하여 대본과 장면을 다시 뽑아오겠습니다. 잠시만 기다려 주십시오!",
                                "parse_mode": "HTML"
                            })
                            return 2 # 특수 리턴 코드: 재생성 필요

                # 2. 버튼 클릭 처리
                if "callback_query" in update:
                    cq = update["callback_query"]
                    data = cq.get("data")
                    cq_id = cq["id"]
                    
                    if data == "approve_tts":
                        requests.post(f"{API_URL}/answerCallbackQuery", json={"callback_query_id": cq_id, "text": "승인되었습니다!"})
                        requests.post(f"{API_URL}/editMessageText", json={
                            "chat_id": TELEGRAM_CHAT_ID,
                            "message_id": message_id,
                            "text": "🎬 <b>국장님 승인 완료!</b>\n고퀄리티 렌더링 및 자동 푸쉬 공정을 시작합니다.",
                            "parse_mode": "HTML"
                        })
                        return 0
                        
                    elif data == "reject_tts":
                        requests.post(f"{API_URL}/answerCallbackQuery", json={"callback_query_id": cq_id, "text": "반려되었습니다. 다시 작성합니다."})
                        requests.post(f"{API_URL}/editMessageText", json={
                            "chat_id": TELEGRAM_CHAT_ID,
                            "message_id": message_id,
                            "text": "❌ <b>국장님 반려!</b>\n대본 소재를 새로 기획하여 다시 집필하겠습니다.",
                            "parse_mode": "HTML"
                        })
                        return 2
        except Exception as e:
            time.sleep(2)
            
    print("⏳ 결재 대기 시간이 초과되었습니다.")
    return 1

if __name__ == "__main__":
    script_path = sys.argv[1] if len(sys.argv) > 1 else "야담과개그_신규대본_1편.txt"
    sys.exit(wait_for_approval(script_path))

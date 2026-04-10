import feedparser
import time
from datetime import datetime
import requests

# [설정]
# 유튜브 채널 ID를 넣으세요. (예: UC... 형식)
# 채널 ID 찾는 법: 채널 정보 -> 사용자 ID 옆의 채널 ID 복사
CHANNEL_ID = "UC_x5XG1OV2P6uYZ5FHSzXdA" # 예시 ID
RSS_URL = f"https://www.youtube.com/feeds/videos.xml?channel_id={CHANNEL_ID}"

TELEGRAM_TOKEN = "8515076340:AAHp4TH200xUzO5i9MeSbBSeX9K2hlJbg80"
TELEGRAM_CHAT_ID = "7793202015"

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Telegram Error: {e}")

def check_new_video(last_video_id):
    print(f"[{datetime.now()}] 채널 체크 중... (RSS 방식)")
    feed = feedparser.parse(RSS_URL)
    
    if not feed.entries:
        print("영상을 찾을 수 없습니다. 채널ID를 확인하세요.")
        return last_video_id

    latest_video = feed.entries[0]
    current_video_id = latest_video.get('yt_videoid', latest_video.id)

    if current_video_id != last_video_id:
        title = latest_video.title
        link = latest_video.link
        msg = f"🔔 <b>새 영상 업로드 알림!</b>\n\n제목: {title}\n링크: {link}\n\n국장님, 새로운 영상이 올라왔습니다! 조만간 성과 보고를 시작하겠습니다. 🫡"
        send_telegram(msg)
        return current_video_id

    return last_video_id

def main():
    last_id = None
    # 최초 실행 시 가장 최근 영상 ID 저장 (알림 안 보냄)
    feed = feedparser.parse(RSS_URL)
    if feed.entries:
        last_id = feed.entries[0].get('yt_videoid', feed.entries[0].id)
        print(f"시작 영상 ID: {last_id}")

    while True:
        try:
            last_id = check_new_video(last_id)
        except Exception as e:
            print(f"Error checking video: {e}")
        
        # 30분마다 체크
        time.sleep(1800)

if __name__ == "__main__":
    main()

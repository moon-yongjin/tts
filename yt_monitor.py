import os
import requests
import json
import time
from datetime import datetime

# [설정]
YOUTUBE_API_KEY = "YOUR_API_KEY_HERE"  # 여기에 API 키를 입력하세요
CHANNEL_ID = "YOUR_CHANNEL_ID_HERE"    # 모니터링할 채널 ID
OLLAMA_API = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "qwen2.5-coder:7b"
TELEGRAM_TOKEN = "8515076340:AAHp4TH200xUzO5i9MeSbBSeX9K2hlJbg80"
TELEGRAM_CHAT_ID = "7793202015"

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Telegram Error: {e}")

def ask_ollama(prompt):
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False
    }
    try:
        response = requests.post(OLLAMA_API, json=payload)
        return response.json().get('response', '분석 실패')
    except:
        return "Ollama 연결 실패"

def get_channel_stats():
    # 실제 구현 시 google-api-python-client 사용 권장
    url = f"https://www.googleapis.com/youtube/v3/channels?part=statistics&id={CHANNEL_ID}&key={YOUTUBE_API_KEY}"
    try:
        r = requests.get(url)
        data = r.json()
        stats = data['items'][0]['statistics']
        return stats
    except Exception as e:
        return f"Error: {e}"

def monitor_main():
    print(f"[{datetime.now()}] 유튜브 모니터링 요원 가동 중...")
    
    # 1. 스탯 가져오기 (예시)
    # stats = get_channel_stats()
    
    # 2. AI 보고서 작성 요청
    # raw_data = f"현재 채널 조회수: {stats['viewCount']}, 구독자: {stats['subscriberCount']}"
    # report = ask_ollama(f"다음 유튜브 데이터를 보고 사장님께 올릴 짤막한 브리핑 보고서를 작성해줘: {raw_data}")
    
    # 3. 텔레그램 전송
    # send_telegram(f"📢 [채널 리포트]\n\n{report}")
    
    print("보고서 전송 완료. (API 키 입력 전이므로 시뮬레이션 종료)")

if __name__ == "__main__":
    monitor_main()

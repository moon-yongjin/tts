import json
import urllib.request
import sys

# 1. 설정
MLX_URL = "http://127.0.0.1:8080/v1/chat/completions"
# 검색된 토큰 및 챗 아이디 사용
TELEGRAM_TOKEN = "8515076340:AAHp4TH200xUzO5i9MeSbBSeX9K2hlJbg80"
TELEGRAM_CHAT_ID = "7793202015"

def query_mlx_local():
    """로컬 MLX 서버에 텍스트 생성 요청"""
    print("🤖 로컬 MLX 서버에서 텔레그램 발송할 메시지 생성 중...")
    prompt = "텔레그램 테스트 기능 확인을 위한 메시지입니다. 수신자는 국장님입니다. 센스있고 친근한 어조로 짧게(50자 이내) 한 문장 작성해줘."
    payload = {
        "model": "mlx-community/Qwen2.5-1.5B-Instruct-4bit",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7
    }
    
    req = urllib.request.Request(
        MLX_URL, 
        data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    
    try:
        with urllib.request.urlopen(req) as res:
            response = json.loads(res.read().decode('utf-8'))
            return response['choices'][0]['message']['content'].strip()
    except Exception as e:
        return f"로컬 서버 호출 에러: {e}"

def send_telegram(message):
    """텔레그램 봇 API로 메시지 발송"""
    print(f"📤 텔레그램 발송 중... (수신 ID: {TELEGRAM_CHAT_ID})")
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID, 
        "text": f"🔔 **[Local MLX 알림]**\n\n{message}", 
        "parse_mode": "Markdown"
    }
    
    req = urllib.request.Request(
        url, 
        data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    
    try:
        with urllib.request.urlopen(req) as res:
            res_data = json.loads(res.read().decode('utf-8'))
            if res_data.get("ok"):
                print("✅ 텔레그램 메시지 발송 성공!")
                return True
            else:
                print(f"❌ 발송 실패 응답: {res_data}")
    except Exception as e:
        print(f"❌ 텔레그램 연동 시 에러: {e}")
    return False

if __name__ == "__main__":
    msg = query_mlx_local()
    print(f"📝 생성된 메시지: {msg}")
    send_telegram(msg)

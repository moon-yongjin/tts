import requests
import json
import time
import sys
import datetime

# [설정]
API_KEY = "rpa_FHG3CVKINI8UZ0II8UU0V4O482A57CBUCMZDLU261yr9lz"
POD_ID = "4j0uvlhn1s17wd"

url = "https://api.runpod.io/graphql"
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}"
}

resume_mutation = f"""
mutation {{
  podResume(input: {{ podId: "{POD_ID}", gpuCount: 1 }}) {{
    id
    desiredStatus
  }}
}}
"""

def try_start_pod():
    print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 🚀 런팟(RunPod) 시동 시도 중... (ID: {POD_ID})")
    try:
        response = requests.post(url, json={'query': resume_mutation}, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            # 에러 체크
            if 'errors' in data:
                error_msg = data['errors'][0]['message']
                if "not enough free GPUs" in error_msg:
                    print("   ⚠️ [대기] 현재 사용 가능한 GPU가 없습니다. (빈자리 기다리는 중...)")
                    return False
                else:
                    print(f"   ❌ 오류 발생: {error_msg}")
                    return "ERROR"
            
            # 성공
            print("\n🎉 [성공] 런팟이 켜졌습니다! 부팅까지 약 1~2분 소요됩니다.")
            return True
            
        else:
            print(f"   ❌ HTTP 에러: {response.status_code}")
            return "ERROR"
            
    except Exception as e:
        print(f"   ❌ 연결 실패: {e}")
        return False

def main():
    print("==================================================")
    print("🔋 RunPod Auto-Starter (빈자리 자동 사냥꾼)")
    print("==================================================")
    
    attempt = 1
    while True:
        result = try_start_pod()
        
        if result == True:
            break
        elif result == "ERROR":
            break
            
        print(f"   ⏳ 30초 후 다시 시도합니다... (시도 {attempt}회)")
        time.sleep(30)
        attempt += 1

if __name__ == "__main__":
    main()

import requests
import time
import json
import os
from pathlib import Path

# 설정
TELEGRAM_TOKEN = "8515076340:AAHp4TH200xUzO5i9MeSbBSeX9K2hlJbg80"
CHAT_ID = "7793202015"
BASE_URL = "http://localhost:7860"

PROMPTS = [
    "비장한 최후의 결전, 웅장한 오케스트라와 북소리, epic martial arts battle, orchestral",
    "새벽녘 산사의 고요함, 대금과 가야금 연주, zen mountain temple, flute and gayageum",
    "빠르고 화려한 검술 액션, 박진감 넘치는 하이네너지 무협, fast sword fight, high energy",
    "떠나간 연인을 그리워하는 슬픈 비가, 정적이고 애절한 해금 선율, sad martial arts ballad, haegeum",
    "강호의 평화를 노래하는 경쾌한 민요풍, upbeat oriental folk dance",
    "어둠 속 비밀 살수의 추격전, 긴장감 넘치는 다크 무협 BGM, dark assassin pursuit, suspense",
    "사부님의 가르침을 받는 정적인 수련 시간, 평화롭고 신비로운 분위기, meditative training, mystical",
    "축제가 열린 객잔의 흥겨운 분위기, 소란스럽고 활기찬 동양풍 음악, lively tavern festival, energetic",
    "광활한 중원을 달리는 기마대, 속도감 있고 장엄한 분위기, vast plains cavalry, majestic",
    "신선이 사는 무릉도원의 몽환적인 배경음악, ethereal peach blossom spring, dreamlike"
]

def send_telegram_audio(audio_path, caption):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendAudio"
    try:
        with open(audio_path, 'rb') as audio:
            files = {'audio': audio}
            data = {'chat_id': CHAT_ID, 'caption': caption}
            res = requests.post(url, files=files, data=data)
            res.raise_for_status()
            print(f"✅ 텔레그램 전송 완료: {caption}")
    except Exception as e:
        print(f"❌ 텔레그램 전송 실패: {e}")

def generate_and_send():
    print(f"🎬 총 10개의 샘플 생성을 시작합니다.")
    
    for i, prompt in enumerate(PROMPTS):
        print(f"\n🎵 [{i+1}/10] 생성 시작: {prompt}")
        
        payload = {
            "prompt": prompt,
            "thinking": True,
            "audio_duration": 30,
            "vocal_language": "ko",
            "audio_format": "mp3"
        }
        
        try:
            # 1. 태스크 등록
            response = requests.post(f"{BASE_URL}/release_task", json=payload)
            response.raise_for_status()
            task_id = response.json()['data']['task_id']
            print(f"  - 태스크 등록 성공: {task_id}")
            
            # 2. 결과 대기 (폴링)
            while True:
                query_payload = {"task_id_list": [task_id]}
                res = requests.post(f"{BASE_URL}/query_result", json=query_payload)
                res.raise_for_status()
                task_info = res.json()['data'][0]
                
                if task_info['status'] == 1: # 성공
                    result_json = json.loads(task_info['result'])[0]
                    audio_path_raw = result_json['file']
                    audio_url = f"{BASE_URL}/v1/audio?path={audio_path_raw}"
                    
                    print(f"  - [{i+1}] 생성 성공! 다운로드 중: {audio_url}")
                    
                    temp_dir = Path("/Users/a12/projects/tts/tmp_samples")
                    temp_dir.mkdir(exist_ok=True)
                    temp_path = temp_dir / f"sample_{i+1}.mp3"
                    
                    audio_res = requests.get(audio_url)
                    audio_res.raise_for_status()
                    
                    content = audio_res.content
                    if len(content) < 1000: # 1KB 미만이면 에러일 가능성 높음
                        print(f"  - ⚠️ 경고: 다운로드된 파일이 너무 작습니다 ({len(content)} bytes). 내용: {content[:50]}")
                    
                    temp_path.write_bytes(content)
                    print(f"  - [{i+1}] 파일 저장 완료: {temp_path} ({len(content)} bytes)")
                    
                    # 텔레그램 전송
                    send_telegram_audio(temp_path, f"🎵 무협 샘플 {i+1}/10\n컨셉: {prompt}")
                    break
                elif task_info['status'] == 2: # 실패
                    print(f"  - [{i+1}] 서버에서 태스크 실패 보고")
                    break
                else:
                    # 진행 중
                    print(".", end="", flush=True)
                    time.sleep(10)
                    
        except Exception as e:
            print(f"  - [{i+1}] 오류 발생: {e}")

if __name__ == "__main__":
    generate_and_send()
    print("\n✅ 모든 샘플 생성 및 텔레그램 전송이 완료되었습니다.")

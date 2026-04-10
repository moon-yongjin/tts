import requests
import json
import time
from pathlib import Path

# 설정
BASE_URL = "http://localhost:7860"
TELEGRAM_TOKEN = "8515076340:AAHp4TH200xUzO5i9MeSbBSeX9K2hlJbg80"
CHAT_ID = "7793202015"
COUNT = 20

# 저장 폴더
SAVE_DIR = Path("/Users/a12/projects/tts/tmp_samples_dark")
SAVE_DIR.mkdir(exist_ok=True, parents=True)

# 프롬프트 구성 (첼로/거문고, 어둡고 무거운 분위기)
PROMPTS = [
    f"Deep, dark, and heavy atmosphere, melancholic cello and geomungo solocore, cinematic sorrow, martial arts mourning #{i+1}"
    for i in range(COUNT)
]

def send_telegram_audio(file_path, caption):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendAudio"
    try:
        with open(file_path, "rb") as audio:
            files = {"audio": audio}
            data = {"chat_id": CHAT_ID, "caption": caption}
            res = requests.post(url, files=files, data=data, timeout=60)
            if res.status_code == 200:
                print(f"✅ 텔레그램 전송 완료: {caption}")
            else:
                print(f"❌ 전송 실패: {res.text}")
    except Exception as e:
        print(f"❌ 오류 발생: {e}")

def run_batch():
    print(f"🎬 [Dark Series] 총 {COUNT}개의 샘플 생성을 시작합니다.")
    
    for i, prompt in enumerate(PROMPTS):
        local_file = SAVE_DIR / f"dark_sample_{i+1}.mp3"
        
        # 이미 생성된 파일이 있다면 건너뛰기
        if local_file.exists() and local_file.stat().st_size > 1000:
            print(f"✅ [{i+1}/{COUNT}] 이미 로컬에 파일이 존재합니다. 건너뜁니다.")
            continue

        # 5개마다 아주 짧은 휴식 (서버 과열 방지)
        if i > 0 and i % 5 == 0:
            print(f"\n☕ [Cooling] 5개 생성 완료. 10초간 대기합니다...")
            time.sleep(10)

        print(f"\n🎵 [{i+1}/{COUNT}] 로컬 생성 및 저장 시작: {prompt}")
        
        payload = {
            "prompt": prompt,
            "thinking": True,
            "audio_duration": 30,
            "vocal_language": "ko",
            "audio_format": "mp3"
        }
        
        # 태스크 등록 (연결될 때까지 재시도)
        task_id = None
        while True:
            try:
                # 무거운 모델 로딩을 고려하여 타임아웃
                response = requests.post(f"{BASE_URL}/release_task", json=payload, timeout=60)
                if response.status_code == 200:
                    task_id = response.json()['data']['task_id']
                    print(f"  - 태스크 등록 성공: {task_id}")
                    break
                else:
                    time.sleep(5)
            except Exception as e:
                time.sleep(5)
        
        if not task_id: continue

        try:
            # 2. 결과 대기 (폴링)
            start_polling = time.time()
            while time.time() - start_polling < 900: # 15분 제한
                try:
                    query_payload = {"task_id_list": [task_id]}
                    res = requests.post(f"{BASE_URL}/query_result", json=query_payload, timeout=30)
                    res.raise_for_status()
                    task_info = res.json()['data'][0]
                    
                    if task_info['status'] == 1: # 성공
                        result_json = json.loads(task_info['result'])[0]
                        audio_path_raw = result_json['file']
                        audio_url = f"{BASE_URL}/v1/audio?path={audio_path_raw}"
                        
                        audio_res = requests.get(audio_url, timeout=120)
                        audio_res.raise_for_status()
                        
                        if len(audio_res.content) < 1000:
                            time.sleep(5)
                            continue
                            
                        local_file.write_bytes(audio_res.content)
                        print(f"  - [{i+1}] 파일 로컬 저장 완료 ({len(audio_res.content)} bytes)")
                        break
                    elif task_info['status'] == 2:
                        print(f"  - [{i+1}] 생성 실패 (서버 에러)")
                        break
                    else:
                        print(".", end="", flush=True)
                        time.sleep(10)
                except Exception as poll_e:
                    time.sleep(5)
            else:
                print(f"  - [{i+1}] 시간 초과로 건너뜁니다.")
        except Exception as e:
            print(f"  - [{i+1}] 오류 발생: {e}")
            time.sleep(5)
                    
        except Exception as e:
            print(f"  - [{i+1}] 오류 발생: {e}")
            time.sleep(5)

if __name__ == "__main__":
    run_batch()

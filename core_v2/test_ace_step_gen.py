import requests
import time
import json
import os

def test_gen():
    base_url = "http://localhost:7860"
    
    # 1. Release Task
    payload = {
        "prompt": "웅장하고 비장한 느낌의 동양풍 무협 대서사시 배경음악, cinematic martial arts orchestral",
        "thinking": True,
        "audio_duration": 30,
        "vocal_language": "ko"
    }
    
    print(f"🚀 생성 요청 중: {payload['prompt']}")
    try:
        response = requests.post(f"{base_url}/release_task", json=payload)
        response.raise_for_status()
        data = response.json()
        task_id = data['data']['task_id']
        print(f"✅ 태스크 생성 완료: {task_id}")
    except Exception as e:
        print(f"❌ 요청 실패: {e}")
        return

    # 2. Poll Result
    while True:
        try:
            query_payload = {"task_id_list": [task_id]}
            res = requests.post(f"{base_url}/query_result", json=query_payload)
            res.raise_for_status()
            res_data = res.json()
            task_info = res_data['data'][0]
            status = task_info['status']
            
            if status == 1: # Success
                result_json = json.loads(task_info['result'])[0]
                audio_path = result_json['file']
                print(f"\n🎉 생성 성공!")
                print(f"🎵 오디오 경로 (API): {audio_path}")
                # Download for verification
                full_audio_url = f"{base_url}{audio_path}"
                print(f"🔗 다운로드 URL: {full_audio_url}")
                break
            elif status == 2: # Failed
                print("\n❌ 생성 실패")
                break
            else:
                print(".", end="", flush=True)
                time.sleep(2)
        except Exception as e:
            print(f"\n⚠️ 폴링 중 오류: {e}")
            time.sleep(5)

if __name__ == "__main__":
    test_gen()

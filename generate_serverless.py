import runpod
import json
import time
import requests
import os

# [설정]
RUNPOD_API_KEY = "YOUR_RUNPOD_API_KEY"  # RunPod Settings -> API Keys에서 발급
ENDPOINT_ID = "YOUR_ENDPOINT_ID"        # 생성한 Endpoint의 ID
DOWNLOADS_DIR = "/Users/a12/Downloads/RunPod_Serverless_Results"

os.makedirs(DOWNLOADS_DIR, exist_ok=True)

# RunPod SDK 설정
runpod.api_key = RUNPOD_API_KEY
endpoint = runpod.Endpoint(ENDPOINT_ID)

def generate_image_serverless(workflow_json, filename_prefix="Serverless_Output"):
    print(f"🚀 [RunPod Serverless] 요청 전송 중...")
    
    # 서버리스 요청 (ComfyUI 전용 포맷)
    payload = {
        "input": {
            "workflow": workflow_json
        }
    }
    
    try:
        # 작업 요청 (비동기)
        job = endpoint.run(payload)
        job_id = job.id
        print(f"📤 작업 예약 완료 (Job ID: {job_id})")
        
        # 상태 확인 (Polling)
        while True:
            status = job.status()
            if status == "COMPLETED":
                print(f"✨ 생성 완료!")
                result = job.output()
                # 생성된 이미지 URL 수거 (보통 S3나 결과물 링크로 옴)
                if 'images' in result:
                    for i, img_data in enumerate(result['images']):
                        url = img_data['url']
                        dst = os.path.join(DOWNLOADS_DIR, f"{filename_prefix}_{int(time.time())}_{i}.png")
                        
                        # 이미지 다운로드
                        img_res = requests.get(url)
                        with open(dst, 'wb') as f:
                            f.write(img_res.content)
                        print(f"🚚 [다운로드 완료] {dst}")
                break
            elif status == "FAILED":
                print(f"❌ 작업 실패: {job.error()}")
                break
            
            print("⏳ 렌더링 중...")
            time.sleep(5)
            
    except Exception as e:
        print(f"❌ 에러 발생: {e}")

if __name__ == "__main__":
    # 예시: 여기 부분에 ComfyUI 워크플로우 대입
    # test_workflow = { ... }
    # generate_image_serverless(test_workflow)
    print("💡 이 스크립트를 사용하려면 RUNPOD_API_KEY와 ENDPOINT_ID가 필요합니다.")

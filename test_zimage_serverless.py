import requests
import json
import time

API_KEY = "rpa_FHG3CVKINI8UZ0II8UU0V4O482A57CBUCMZDLU261yr9lz"
ENDPOINT_ID = "wvz92hpw73rmdw"

# Z-Image Turbo (SDXL) API Workflow load
with open('/Users/a12/projects/tts/zimage_api_workflow.json', 'r') as f:
    target_workflow = json.load(f)

# Update seed for randomness
target_workflow["18"]["inputs"]["seed"] = int(time.time() * 1000) % 10**14

payload = {
    "input": {
        "workflow": target_workflow
    }
}

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

url = f"https://api.runpod.ai/v2/{ENDPOINT_ID}/runsync"

print("🚀 Z-Image Turbo 워크플로우를 서버리스(RunPod)로 전송합니다...")
print("이 작업은 모델이 이미 메모리에 있다면 3-5초 내에 끝나야 합니다.")

start_time = time.time()
try:
    response = requests.post(url, headers=headers, json=payload, timeout=300)
    end_time = time.time()
    
    print(f"\n✅ Status Code: {response.status_code}")
    print(f"⏱️ 걸린 시간: {end_time - start_time:.2f}초")
    
    if response.status_code == 200:
        data = response.json()
        if "output" in data and "images" in data["output"]:
            print(f"✨ 성공! {len(data['output']['images'])} 장의 이미지가 Base64 형태로 수신되었습니다.")
            # For demonstration, save the first image to disk to prove it worked
            import base64
            img_data = data['output']['images'][0]
            # Strip the data prepender if it exists (data:image/png;base64,...)
            if img_data.startswith('data:'):
                img_data = img_data.split(',', 1)[1]
                
            img_bytes = base64.b64decode(img_data)
            with open('/Users/a12/Downloads/runpod_zimage_test.png', 'wb') as img_file:
                img_file.write(img_bytes)
            print("💾 결과 이미지를 다운로드 폴더에 저장했습니다: /Users/a12/Downloads/runpod_zimage_test.png")
        else:
             print("응답 JSON:")
             print(json.dumps(data, indent=2, ensure_ascii=False))
             
except Exception as e:
    print(f"❌ 에러 발생: {e}")

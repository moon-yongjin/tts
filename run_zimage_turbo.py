import json
import urllib.request
import urllib.parse
import os
import sys
import time
from datetime import datetime

# [설정]
# SSH 터널을 통해 로컬 18188 포트로 연결합니다.
COMFY_URL = "http://127.0.0.1:18188"
API_WORKFLOW_FILE = "/Users/a12/projects/tts/zimage_api_workflow.json"
OUTPUT_DIR = os.path.expanduser("~/Downloads/ZImage_Output")

def queue_prompt(prompt):
    p = {"prompt": prompt}
    data = json.dumps(p).encode('utf-8')
    req = urllib.request.Request(f"{COMFY_URL}/prompt", data=data)
    req.add_header('Content-Type', 'application/json')
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read())
    except Exception as e:
        print(f"❌ API 요청 실패: {e}")
        return None

def get_history(prompt_id):
    try:
        with urllib.request.urlopen(f"{COMFY_URL}/history/{prompt_id}") as response:
            return json.loads(response.read())
    except:
        return {}

def download_image(filename, subfolder, target_path):
    # ComfyUI /view API를 통해 이미지 다운로드
    query = urllib.parse.urlencode({"filename": filename, "subfolder": subfolder, "type": "output"})
    url = f"{COMFY_URL}/view?{query}"
    
    print(f"📥 이미지 다운로드 중: {url}")
    try:
        urllib.request.urlretrieve(url, target_path)
        return True
    except Exception as e:
        print(f"❌ 다운로드 실패: {e}")
        return False

def generate_zimage(user_prompt):
    print(f"\n🚀 Z-Image Turbo 생성 시작!")
    print(f"📄 프롬프트: {user_prompt}")
    
    # 1. 워크플로우 로드
    if not os.path.exists(API_WORKFLOW_FILE):
        print(f"❌ 워크플로우 파일을 찾을 수 없습니다: {API_WORKFLOW_FILE}")
        return
        
    with open(API_WORKFLOW_FILE, 'r') as f:
        prompt_data = json.load(f)
    
    # 2. 프롬프트 및 시드 업데이트
    # StylePromptEncoder (ID: 42)
    if "42" in prompt_data:
        prompt_data["42"]["inputs"]["text"] = user_prompt
    
    # ZSamplerTurbo (ID: 18) - 시드 랜덤화
    if "18" in prompt_data:
        prompt_data["18"]["inputs"]["seed"] = int(time.time() * 1000) % 10**14

    # 3. 큐 등록
    res = queue_prompt(prompt_data)
    if not res: return
    
    prompt_id = res['prompt_id']
    print(f"⏳ 대기 중 (ID: {prompt_id})...")
    
    # 4. 완료 대기
    start_time = time.time()
    while True:
        history = get_history(prompt_id)
        if prompt_id in history:
            print("✨ 생성 완료!")
            # 5. 결과 파일 정보 추출
            outputs = history[prompt_id]['outputs']
            for node_id in outputs:
                if 'images' in outputs[node_id]:
                    for img in outputs[node_id]['images']:
                        filename = img['filename']
                        subfolder = img['subfolder']
                        
                        # 로컬 저장 경로 설정
                        if not os.path.exists(OUTPUT_DIR): os.makedirs(OUTPUT_DIR)
                        timestamp = datetime.now().strftime("%H%M%S")
                        local_path = os.path.join(OUTPUT_DIR, f"ZI_{timestamp}_{filename}")
                        
                        if download_image(filename, subfolder, local_path):
                            print(f"✅ 저장 성공: {local_path}")
            break
        
        if time.time() - start_time > 180:
            print("⏳ 타임아웃: 생성이 너무 오래 걸립니다.")
            break
        
        time.sleep(2)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        user_input = " ".join(sys.argv[1:])
    else:
        user_input = "A hyper-realistic cinematic photo of a futuristic neon city interior, 8k, highly detailed"
    
    generate_zimage(user_input)

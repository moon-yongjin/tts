import os
import sys
import subprocess
import time
import json
import urllib.request
import urllib.parse
from datetime import datetime
from PIL import Image

# [설정]
REMOTE_IP = "203.57.40.175"
REMOTE_PORT = "14029"
SSH_KEY = os.path.expanduser("~/.ssh/id_ed25519_runpod")
LOCAL_PORT = "18188"

# 로컬 API 엔드포인트 (터널링 후)
COMFY_URL = f"http://127.0.0.1:{LOCAL_PORT}"
WORKFLOW_FILE = "/Users/a12/projects/tts/zimage_batch_workflow.json"
OUTPUT_DIR = os.path.expanduser("~/Downloads/ZImage_Output/Korean_Batch")

# [프롬프트] 한국인 캐릭터 고정
FIXED_PROMPT = "A portrait of a beautiful young Korean woman, natural beauty, black hair, soft lighting, detailed skin texture, 8k, photorealistic, cinematic masterpiece"

def open_tunnel():
    print("Bridge: Opening secure SSH tunnel...")
    cmd = [
        "ssh", "-f", "-N", 
        "-L", f"{LOCAL_PORT}:127.0.0.1:8188",
        "-i", SSH_KEY,
        "-p", REMOTE_PORT,
        f"root@{REMOTE_IP}"
    ]
    subprocess.Popen(cmd)
    time.sleep(5)

def close_tunnel():
    print("Bridge: Closing SSH tunnel...")
    subprocess.run(["pkill", "-f", f"L {LOCAL_PORT}:127.0.0.1:8188"])

def queue_prompt(prompt_data):
    data = json.dumps({"prompt": prompt_data}).encode('utf-8')
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
    query = urllib.parse.urlencode({"filename": filename, "subfolder": subfolder, "type": "output"})
    url = f"{COMFY_URL}/view?{query}"
    try:
        urllib.request.urlretrieve(url, target_path)
        
        # [자동 최적화] PNG -> JPG 변환 (용량 80% 절감)
        if target_path.lower().endswith(".png"):
            img = Image.open(target_path)
            rgb_img = img.convert('RGB')
            jpg_path = target_path.rsplit('.', 1)[0] + ".jpg"
            rgb_img.save(jpg_path, quality=85) # 품질 85% 설정
            os.remove(target_path) # 원본 PNG 삭제
            return jpg_path
            
        return target_path
    except Exception as e:
        print(f"❌ 다운로드/변환 실패: {e}")
        return None

def run_batch_generation():
    start_all = time.time()
    print(f"🎬 한국인 캐릭터 20장 배치 생성 시작 (4장씩 x 5회)")
    print(f"⚡️ 최적화: FP8 Quantization + JPG Compression (Quality 85%)")
    print(f"📂 저장 위치: {OUTPUT_DIR}")
    print("==================================================")
    
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    with open(WORKFLOW_FILE, 'r') as f:
        workflow = json.load(f)

    if "42" in workflow:
        workflow["42"]["inputs"]["text"] = FIXED_PROMPT

    # 1. 터널 열기
    close_tunnel()
    open_tunnel()
    
    total_images = 0
    
    try:
        for i in range(5):
            print(f"\n📸 [Batch {i+1}/5] 생성 요청 중...")
            
            if "18" in workflow:
                workflow["18"]["inputs"]["seed"] = int(time.time() * 1000) % 10**14
            
            res = queue_prompt(workflow)
            if not res: continue
            
            prompt_id = res['prompt_id']
            print(f"⏳ 대기 중 (ID: {prompt_id})...")
            
            start_batch = time.time()
            while True:
                history = get_history(prompt_id)
                if prompt_id in history:
                    outputs = history[prompt_id]['outputs']
                    for node_id in outputs:
                        if 'images' in outputs[node_id]:
                            images = outputs[node_id]['images']
                            print(f"✨ 생성 완료! {len(images)}장 다운로드/압축 중...")
                            
                            for img in images:
                                filename = img['filename']
                                subfolder = img['subfolder']
                                timestamp = datetime.now().strftime("%H%M%S")
                                local_path = os.path.join(OUTPUT_DIR, f"Korean_Batch_{i+1}_{timestamp}_{filename}")
                                
                                result_path = download_image(filename, subfolder, local_path)
                                if result_path:
                                    print(f"   ✅ 저장: {os.path.basename(result_path)}")
                                    total_images += 1
                    break
                
                if time.time() - start_batch > 180:
                    print("❌ 타임아웃")
                    break
                time.sleep(2)
                
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n🛑 중단됨")
    finally:
        close_tunnel()

    end_all = time.time()
    total_time = end_all - start_all
    
    print("\n==================================================")
    print(f"🎉 총 {total_images}장 생성 완료!")
    print(f"⏱️ 총 소요 시간: {total_time:.2f}초 (평균 {total_time/total_images:.2f}초/장)")
    print("==================================================")

if __name__ == "__main__":
    run_batch_generation()

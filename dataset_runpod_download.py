import json
import urllib.request
import time
import os

# [설정] RunPod 연결용 (보안 터널 8181 사용)
COMFYUI_URL = "http://127.0.0.1:8181"
BASE_DOWNLOAD_DIR = "/Users/a12/Downloads/LoRA_Datasets"

def get_history():
    try:
        with urllib.request.urlopen(f"{COMFYUI_URL}/history") as response:
            return json.loads(response.read())
    except Exception as e:
        return {}

def download_image(filename, subfolder, folder_type, char_folder):
    target_dir = os.path.join(BASE_DOWNLOAD_DIR, char_folder)
    os.makedirs(target_dir, exist_ok=True)
    
    url = f"{COMFYUI_URL}/view?filename={filename}&subfolder={subfolder}&type={folder_type}"
    target_path = os.path.join(target_dir, filename)
    
    if os.path.exists(target_path):
        return False
        
    try:
        urllib.request.urlretrieve(url, target_path)
        return True
    except:
        return False

def monitor_and_download():
    print(f"🚀 [RunPod] 통합 데이터셋 자동 수거 기동 (경로: {BASE_DOWNLOAD_DIR})")
    downloaded_files = set()
    
    while True:
        history = get_history()
        found_new = False
        
        for prompt_id in history:
            outputs = history[prompt_id].get('outputs', {})
            for node_id in outputs:
                if 'images' in outputs[node_id]:
                    for img in outputs[node_id]['images']:
                        filename = img['filename']
                        
                        # 캐릭터 판별
                        char_folder = ""
                        if filename.startswith("Dataset_MIL"): char_folder = "MIL"
                        elif filename.startswith("Dataset_DIL1"): char_folder = "DIL1"
                        elif filename.startswith("Dataset_DIL2"): char_folder = "DIL2"
                        
                        if char_folder and filename not in downloaded_files:
                            if download_image(filename, img['subfolder'], img['type'], char_folder):
                                downloaded_files.add(filename)
                                found_new = True
                                print(f"🚚 수거 완료: {char_folder} -> {filename}")
        
        if not found_new:
            time.sleep(10)
        else:
            print(f"✅ 현재까지 총 {len(downloaded_files)}장 수거됨.")
            # MIL(20) + DIL1(20) + DIL2(20) = 60
            if len(downloaded_files) >= 60:
                print(f"🎉 목표한 60장(캐릭터당 20장) 수거가 모두 끝났습니다!")
                break

if __name__ == "__main__":
    monitor_and_download()

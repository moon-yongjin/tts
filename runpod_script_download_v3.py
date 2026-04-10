import json
import urllib.request
import time
import os

# [설정] RunPod 연결용 (보안 터널 8181 사용)
COMFYUI_URL = "http://127.0.0.1:8181"
DOWNLOAD_DIR = "/Users/a12/Downloads/RunPod_Script_V3"

os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def get_history():
    try:
        with urllib.request.urlopen(f"{COMFYUI_URL}/history") as response:
            return json.loads(response.read())
    except Exception as e:
        print(f"⚠️ History 가져오기 실패: {e}")
        return {}

def download_image(filename, subfolder, folder_type):
    url = f"{COMFYUI_URL}/view?filename={filename}&subfolder={subfolder}&type={folder_type}"
    target_path = os.path.join(DOWNLOAD_DIR, filename)
    
    if os.path.exists(target_path):
        return False
        
    try:
        print(f"🚚 다운로드 중: {filename} ...")
        urllib.request.urlretrieve(url, target_path)
        return True
    except Exception as e:
        print(f"❌ 다운로드 실패 ({filename}): {e}")
        return False

def monitor_and_download(target_count=8):
    print(f"🚀 [RunPod] V3 자동 다운로드 시스템 기동 (대상: {DOWNLOAD_DIR})")
    print(f"🔎 'Script_V3_Scene_' 접두사가 붙은 파일을 수거합니다...")
    
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
                        if filename.startswith("Script_V3_Scene_") and filename not in downloaded_files:
                            if download_image(filename, img['subfolder'], img['type']):
                                downloaded_files.add(filename)
                                found_new = True
        
        if not found_new:
            time.sleep(5)
        else:
            print(f"✅ 현재까지 {len(downloaded_files)}장 수거 완료.")
            if len(downloaded_files) >= target_count:
                print(f"🎉 모든 {target_count}개 V3 장면 수거가 끝났습니다!")
                break

if __name__ == "__main__":
    monitor_and_download(8)

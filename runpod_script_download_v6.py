import json
import urllib.request
import time
import os

# [설정] RunPod 연결용 (보안 터널 8181 사용)
COMFYUI_URL = "http://127.0.0.1:8181"
DOWNLOAD_DIR = "/Users/a12/Downloads/RunPod_Script_V6"

os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def get_history():
    try:
        with urllib.request.urlopen(f"{COMFYUI_URL}/history") as response:
            return json.loads(response.read())
    except: return {}

def download_image(filename, subfolder, folder_type):
    url = f"{COMFYUI_URL}/view?filename={filename}&subfolder={subfolder}&type={folder_type}"
    target_path = os.path.join(DOWNLOAD_DIR, filename)
    if os.path.exists(target_path): return False
    try:
        urllib.request.urlretrieve(url, target_path)
        return True
    except: return False

def monitor_and_download(target_count=4):
    print(f"🚀 [RunPod] V6 자동 다운로드 기동 (경로: {DOWNLOAD_DIR})")
    downloaded_files = set()
    while True:
        history = get_history()
        found_new = False
        for p_id in history:
            outputs = history[p_id].get('outputs', {})
            for n_id in outputs:
                if 'images' in outputs[n_id]:
                    for img in outputs[n_id]['images']:
                        fname = img['filename']
                        if fname.startswith("Script_V6_Scene_") and fname not in downloaded_files:
                            if download_image(fname, img['subfolder'], img['type']):
                                downloaded_files.add(fname)
                                found_new = True
                                print(f"🚚 전송 완료: {fname}")
        if not found_new: time.sleep(5)
        else:
            if len(downloaded_files) >= target_count:
                print(f"🎉 V6 며느리 전용 장면 {target_count}장 수거 완료!")
                break

if __name__ == "__main__":
    monitor_and_download(4)

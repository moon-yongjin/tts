import os
import sys
import subprocess
import time
import json
import urllib.request
import urllib.parse
from datetime import datetime
from PIL import Image
import concurrent.futures

# [설정]
REMOTE_IP = "203.57.40.175"
REMOTE_PORT = "14029"
SSH_KEY = os.path.expanduser("~/.ssh/id_ed25519_runpod")
LOCAL_PORT = "18188"
COMFY_URL = f"http://127.0.0.1:{LOCAL_PORT}"
WORKFLOW_FILE = "/Users/a12/projects/tts/zimage_batch_workflow.json"
OUTPUT_DIR = os.path.expanduser("~/Downloads/ZImage_Output/Drama_Parallel")

# [배우 설정 - 이미지 고정용]
ACTOR_OKSUN = "A wealthy elegant Korean woman in her 60s, short permed hair, fierce and sharp eyes"
ACTOR_HYERIM = "A beautiful manipulative Korean woman in her 30s, long black hair, evil smirk"

DRAMA_PROMPTS = [
    f"Luxury penthouse exterior in Apgujeong, Korea, massive orange flames and black smoke at night, cinematic lighting, 8k",
    f"Wide shot of an expensive living room on fire, luxury furniture burning, intense heat and debris, hellish atmosphere",
    f"{ACTOR_OKSUN}, hand-cuffed, being roughly dragged by police officers through a burning apartment, soot on her face, cinematic",
    f"Ok-sun ({ACTOR_OKSUN}) being pushed like a sack of luggage into a police car, cold street at night, heavy drama",
    f"Hye-rim ({ACTOR_HYERIM}) on a stretcher, pretending to be injured, light facial burns, wearing a hospital gown, dark rainy night",
    f"Extreme close-up of Hye-rim's ({ACTOR_HYERIM}) eyes, a wicked and victorious smile glinting as she looks at the camera secretively",
    f"POV shot of Hye-rim seeing her mother-in-law being arrested, the reflection of the fire in the stretcher glass",
    f"Ok-sun ({ACTOR_OKSUN}) sitting alone in the cold dark backseat of a police car, looking out the window with a vengeful gaze",
    f"Metaphorical shot: A sharp silver knife piercing a glowing red heart made of glass, dark background, dramatic splash of light",
    f"Close-up of Ok-sun’s ({ACTOR_OKSUN}) eyes reflecting the roaring house fire, frozen calm expression, cinematic 8k",
    f"A crowd of angry neighbors and onlookers holding up smartphones, filming the arrest with hateful expressions, night street",
    f"A smartphone screen showing a TikTok live stream of the penthouse fire, Korean comments like 'She tried to kill her daughter-in-law' visible",
    f"Hye-rim ({ACTOR_HYERIM}) weeping fake tears in front of the reporters, but her hands are relaxed and still, psychological thriller vibe",
    f"A tiny hidden micro-camera lens disguised inside a burnt wall outlet, glowing red 'REC' light, reveal shot",
    f"A computer monitor in a dark room showing data progress bars: 'Cloud Backup Complete (Criminal Evidence)', high-tech thriller",
    f"Close-up of police car sirens flashing red and blue on a wet asphalt street, rain falling, dramatic cinematic blur",
    f"The burnt-out server room of the penthouse, smoke everywhere but green server lights still blinking in the dark",
    f"A fax machine in a prosecutor's office, papers sliding out rapidly at night, dramatic shadows on the wall",
    f"Close-up of evidence papers with Korean text '방화 증거' (Evidence of Arson) being printed, high-speed motion",
    f"Ok-sun ({ACTOR_OKSUN}) staring directly into the camera from the darkness, a cold 'predator' smile before the revenge starts"
]

def open_tunnel():
    print("Bridge: Opening secure SSH tunnel...")
    cmd = ["ssh", "-f", "-N", "-L", f"{LOCAL_PORT}:127.0.0.1:8188", "-i", SSH_KEY, "-p", REMOTE_PORT, f"root@{REMOTE_IP}"]
    subprocess.Popen(cmd)
    time.sleep(5)

def close_tunnel():
    print("Bridge: Closing SSH tunnel...")
    subprocess.run(["pkill", "-f", f"L {LOCAL_PORT}:127.0.0.1:8188"])

def queue_prompt(workflow, prompt_text, seed):
    if "42" in workflow: workflow["42"]["inputs"]["text"] = prompt_text
    if "18" in workflow: workflow["18"]["inputs"]["seed"] = seed
    data = json.dumps({"prompt": workflow}).encode('utf-8')
    req = urllib.request.Request(f"{COMFY_URL}/prompt", data=data)
    req.add_header('Content-Type', 'application/json')
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read())['prompt_id']
    except: return None

def download_and_optimize(img_info, target_base):
    filename, subfolder = img_info['filename'], img_info['subfolder']
    query = urllib.parse.urlencode({"filename": filename, "subfolder": subfolder, "type": "output"})
    url = f"{COMFY_URL}/view?{query}"
    png_path, jpg_path = target_base + ".png", target_base + ".jpg"
    try:
        urllib.request.urlretrieve(url, png_path)
        img = Image.open(png_path); rgb_img = img.convert('RGB')
        rgb_img.save(jpg_path, quality=85); os.remove(png_path)
        return jpg_path
    except: return None

def run_parallel_batch():
    start_all = time.time()
    if not os.path.exists(OUTPUT_DIR): os.makedirs(OUTPUT_DIR)
    with open(WORKFLOW_FILE, 'r') as f: workflow = json.load(f)
    if "32" in workflow: workflow["32"]["inputs"]["batch_size"] = 1
    
    close_tunnel(); open_tunnel()
    
    print(f"🚀 드라마 20장 [병렬 큐잉] 생산 모드 가동")
    print(f"📂 저장: {OUTPUT_DIR}\n" + "-"*50)
    
    results = []
    # 20개의 씬을 4개씩 묶어서 병렬로 큐에 던짐
    batch_size = 4
    for i in range(0, len(DRAMA_PROMPTS), batch_size):
        current_batch = DRAMA_PROMPTS[i:i+batch_size]
        print(f"\n⚡️ [Batch {i//batch_size + 1}] 4개 동시 큐잉 중...")
        
        prompt_ids = []
        for j, prompt in enumerate(current_batch):
            pid = queue_prompt(workflow, prompt, int(time.time()*1000) + j)
            if pid:
                prompt_ids.append((i + j + 1, pid))
                print(f"   ㄴ [{i+j+1}] 큐 등록 완료 (ID: {pid[:8]})")
        
        # 해당 배치의 4개가 모두 생성될 때까지 대기 및 다운로드
        for idx, pid in prompt_ids:
            start_wait = time.time()
            while True:
                try:
                    with urllib.request.urlopen(f"{COMFY_URL}/history/{pid}") as resp:
                        history = json.loads(resp.read())
                    if pid in history:
                        img_info = history[pid]['outputs']['31']['images'][0]
                        local_base = os.path.join(OUTPUT_DIR, f"Drama_{idx:02d}_{datetime.now().strftime('%H%M%S')}")
                        path = download_and_optimize(img_info, local_base)
                        if path:
                            print(f"   ✅ [{idx}] 저장 성공: {os.path.basename(path)}")
                            results.append(path)
                        break
                    if time.time() - start_wait > 120: break
                    time.sleep(1)
                except: time.sleep(1)

    close_tunnel()
    duration = time.time() - start_all
    print("\n" + "="*50)
    print(f"🎉 전 공정 완료: 총 {len(results)}장")
    print(f"⏱️ 총 소요 시간: {duration:.2f}초 (평균 {duration/20:.2f}초/장)")

if __name__ == "__main__":
    run_parallel_batch()

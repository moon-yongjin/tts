import websocket
import uuid
import json
import urllib.request
import urllib.parse
import time
import os
import subprocess
import sys
import random

SERVER_ADDRESS = "127.0.0.1:8188"
CLIENT_ID = str(uuid.uuid4())
COMFYUI_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../ComfyUI")
OUTPUT_DIR = os.path.expanduser("~/Downloads/ComfyUI_Flux_Batch")

# [User Settings]
PROMPT_TEXT = "(Full body shot:1.2), (Standing portrait:1.2), A tall and slender Korean woman on an athletic track, fair skin, lean physique, professional running gear, sneakers, (neutral white balance:1.2), cinematic cold lighting, realistic skin texture, f/8, 8k raw photo, film grain"
NEGATIVE_PROMPT = "blurry, low quality, game graphic, 3d render, plastic, jaundice, yellow skin"
STEPS = 20 # Flux Dev 권장
CFG = 3.5  # User requested 3.0~3.5
WIDTH = 832
HEIGHT = 1216
BATCH_COUNT = 10

def start_comfyui():
    """ComfyUI 서버 시작 (Output Directory 설정 추가)"""
    print(f"🚀 ComfyUI 서버 시작 중... (Output: {OUTPUT_DIR})")
    
    # Ensure output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    main_py = os.path.join(COMFYUI_PATH, "main.py")
    log_file = open("comfy_launch.log", "w")
    
    # Add --output-directory argument
    cmd = [sys.executable, main_py, "--output-directory", OUTPUT_DIR]
    
    subprocess.Popen(cmd, cwd=COMFYUI_PATH, stdout=log_file, stderr=log_file)
    time.sleep(10) # 초기 부팅 대기

def check_server():
    try:
        urllib.request.urlopen(f"http://{SERVER_ADDRESS}/history", timeout=5)
        return True
    except:
        return False

def queue_prompt(prompt):
    p = {"prompt": prompt, "client_id": CLIENT_ID}
    data = json.dumps(p).encode('utf-8')
    
    # [Debug] Save JSON to verify structure
    with open("workflow_debug.json", "w") as f:
        json.dump(p, f, indent=2)
        
    req = urllib.request.Request(f"http://{SERVER_ADDRESS}/prompt", data=data)
    return json.loads(urllib.request.urlopen(req).read())

def get_flux_workflow(seed):
    # Workflow Construction (Flux Split Loaders)
    wf = {}

    # 1. UNETLoader
    wf["1"] = {
        "inputs": {
            "unet_name": "flux1-dev-fp8.safetensors",
            "weight_dtype": "bf16"
        },
        "class_type": "UNETLoader"
    }

    # 2. DualCLIPLoader
    wf["2"] = {
        "inputs": {
            "clip_name1": "t5xxl_fp8_e4m3fn.safetensors",
            "clip_name2": "clip_l.safetensors",
            "type": "flux"
        },
        "class_type": "DualCLIPLoader"
    }

    # 3. VAELoader
    wf["3"] = {
        "inputs": {
            "vae_name": "ae.safetensors"
        },
        "class_type": "VAELoader"
    }

    # 4. CLIP Text Encode (Positive)
    wf["4"] = {
        "inputs": {
            "text": PROMPT_TEXT,
            "clip": ["2", 0]
        },
        "class_type": "CLIPTextEncode"
    }

    # 5. CLIP Text Encode (Negative) - Empty but needed
    wf["5"] = {
        "inputs": {
            "text": NEGATIVE_PROMPT,
            "clip": ["2", 0]
        },
        "class_type": "CLIPTextEncode"
    }

    # 6. FluxGuidance
    wf["6"] = {
        "inputs": {
            "guidance": CFG,
            "conditioning": ["4", 0]
        },
        "class_type": "FluxGuidance"
    }

    # 7. Empty Latent Image
    wf["7"] = {
        "inputs": {
            "width": WIDTH,
            "height": HEIGHT,
            "batch_size": 1
        },
        "class_type": "EmptyLatentImage"
    }

    # 8. KSampler
    wf["8"] = {
        "inputs": {
            "seed": seed,
            "steps": STEPS,
            "cfg": 1.0,
            "sampler_name": "euler",
            "scheduler": "simple",
            "denoise": 1.0,
            "model": ["1", 0],
            "positive": ["6", 0],
            "negative": ["5", 0],
            "latent_image": ["7", 0]
        },
        "class_type": "KSampler"
    }

    # 9. VAEDecode
    wf["9"] = {
        "inputs": {
            "samples": ["8", 0],
            "vae": ["3", 0]
        },
        "class_type": "VAEDecode"
    }

    # 10. Save Image
    wf["10"] = {
        "inputs": {
            "filename_prefix": "Flux_Final",
            "images": ["9", 0]
        },
        "class_type": "SaveImage"
    }

    return wf


def main():
    if not check_server():
        start_comfyui()
    
    # Wait for server (Max 60s)
    for i in range(30):
        if check_server(): 
            print("✅ 서버 연결 성공!")
            break
        print(f"⏳ 서버 대기 중... ({i+1}/30)")
        time.sleep(2)
    
    if not check_server():
        print("❌ ComfyUI 서버 연결 실패 (로그를 확인하세요)")
        return

    print(f"🎬 [Flux + FaceDetailer] 10장 생성 시작...")
    
    for i in range(BATCH_COUNT):
        seed = random.randint(1, 9999999999)
        workflow = get_flux_workflow(seed)
        
        try:
            resp = queue_prompt(workflow)
            print(f"   📤 [Image {i+1}/{BATCH_COUNT}] 요청 완료 (Seed: {seed}) -> prompt_id: {resp['prompt_id']}")
        except Exception as e:
            print(f"   ❌ 요청 실패: {e}")
        
    print("✅ 모든 작업이 큐에 등록되었습니다. ComfyUI 웹(http://127.0.0.1:8188)에서 진행 상황을 확인하세요.")

if __name__ == "__main__":
    main()

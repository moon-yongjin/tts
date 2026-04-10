import websocket
import uuid
import json
import urllib.request
import urllib.parse
import time
import os
import random

# [RunPod Connection Settings]
SERVER_ADDRESS = "213.173.108.15:60247" 
CLIENT_ID = str(uuid.uuid4())

# [User Settings]
# 모델을 자동으로 다운로드하거나 특정 이름을 강요하지 않음
# 런팟에 있는 모델 목록을 가져와서 선택하도록 변경
# VAE: ae.safetensors (Z-Image)는 있다고 하셨음

# 대본 요약본 (예시)
SCRIPT_CONTEXT = "A tense martial arts duel in a bamboo forest at sunset."
PROMPT_TEXT = f"(Masterpiece, Best Quality), {SCRIPT_CONTEXT}, dynamic angle, cinematic lighting, photorealistic, 8k, detailed texture"
NEGATIVE_PROMPT = "text, watermark, low quality, blurry, illustration, painting, cartoon"

# Turbo-like Settings for Dev Model
STEPS = 8 
CFG = 1.0 
WIDTH = 832
HEIGHT = 1216
BATCH_COUNT = 10

def check_server():
    try:
        urllib.request.urlopen(f"http://{SERVER_ADDRESS}/history", timeout=5)
        return True
    except:
        return False

def get_available_models():
    """ComfyUI API를 통해 사용 가능한 모델(UNET) 목록 조회"""
    try:
        req = urllib.request.Request(f"http://{SERVER_ADDRESS}/object_info/UNETLoader")
        data = json.loads(urllib.request.urlopen(req).read())
        return data.get('UNETLoader', {}).get('input', {}).get('required', {}).get('unet_name', [])[0]
    except Exception as e:
        print(f"⚠️ 모델 목록 조회 실패: {e}")
        return []

def queue_prompt(prompt):
    p = {"prompt": prompt, "client_id": CLIENT_ID}
    data = json.dumps(p).encode('utf-8')
    req = urllib.request.Request(f"http://{SERVER_ADDRESS}/prompt", data=data)
    return json.loads(urllib.request.urlopen(req).read())

def get_flux_workflow(seed, model_name, vae_name):
    # Workflow Construction (Flux + Z-VAE Turbo Mode)
    wf = {}

    # 1. UNETLoader (Dynamic Model)
    wf["1"] = {
        "inputs": {
            "unet_name": model_name, 
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

    # 3. VAELoader (Z-Image / ae.safetensors)
    wf["3"] = {
        "inputs": {
            "vae_name": vae_name 
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

    # 5. CLIP Text Encode (Negative)
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
            "guidance": 3.5, 
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

    # 8. KSampler (Turbo-like setup)
    wf["8"] = {
        "inputs": {
            "seed": seed,
            "steps": STEPS, 
            "cfg": CFG,
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
            "filename_prefix": "Z_Image_Gen",
            "images": ["9", 0]
        },
        "class_type": "SaveImage"
    }

    return wf

def main():
    print(f"📡 런팟 연결 시도: {SERVER_ADDRESS}")
    if not check_server():
        print("❌ 런팟 ComfyUI 서버에 연결할 수 없습니다.")
        return

    # [모델 자동 감지]
    available_models = get_available_models()
    if not available_models:
        print("❌ ComfyUI에서 로드된 모델(UNET)을 찾을 수 없습니다.")
        return

    print(f"📂 사용 가능한 모델 목록:")
    for idx, m in enumerate(available_models):
        print(f"   [{idx+1}] {m}")
    
    # 기본값: 첫 번째 모델 (또는 flux 포함된 것)
    selected_model = available_models[0]
    for m in available_models:
        if "flux" in m.lower():
            selected_model = m
            break
            
    print(f"\n✅ 선택된 모델: {selected_model}")
    print(f"✅ 선택된 VAE: ae.safetensors (Z-Image)")

    print(f"🎬 [RunPod Z-Image Generator] 10장 생성 시작...")
    
    for i in range(BATCH_COUNT):
        seed = random.randint(1, 9999999999)
        workflow = get_flux_workflow(seed, selected_model, "ae.safetensors")
        
        try:
            resp = queue_prompt(workflow)
            print(f"   📤 [Image {i+1}/{BATCH_COUNT}] 큐 등록 완료! (Seed: {seed})")
        except Exception as e:
            print(f"   ❌ 요청 실패: {e}")
            
    print("\n✅ 모든 요청이 전송되었습니다!")
    print("👉 이제 '99-3_런팟_다운로드...' 스크립트가 런팟에서 완성된 파일을 납치해올 겁니다.")

if __name__ == "__main__":
    main()

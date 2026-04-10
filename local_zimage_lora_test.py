import json
import urllib.request
import time
import os
import shutil

# [설정]
COMFYUI_URL = "http://127.0.0.1:8188"
OUTPUT_DIR = "/Users/a12/projects/tts/ComfyUI/output"
DOWNLOADS_DIR = "/Users/a12/Downloads/LoRA_Test_Output"
LORA_NAME = "realistic_asian_female_v1.safetensors"

os.makedirs(DOWNLOADS_DIR, exist_ok=True)

def queue_prompt(prompt):
    p = {"prompt": prompt}
    data = json.dumps(p).encode('utf-8')
    req = urllib.request.Request(f"{COMFYUI_URL}/prompt", data=data)
    return json.loads(urllib.request.urlopen(req).read())

def get_history(prompt_id):
    try:
        with urllib.request.urlopen(f"{COMFYUI_URL}/history/{prompt_id}") as response:
            return json.loads(response.read())
    except:
        return {}

# Z-Image LoRA Workflow
workflow_template = {
  "12": {
    "inputs": { "unet_name": "z_image_turbo-Q5_K_M.gguf" },
    "class_type": "UnetLoaderGGUF"
  },
  "13": {
    "inputs": {
      "clip_name": "qwen_3_4b_fp8_mixed.safetensors",
      "type": "qwen_image",
      "device": "default"
    },
    "class_type": "CLIPLoader"
  },
  "20": {
    "inputs": {
      "lora_name": LORA_NAME,
      "strength_model": 1.0,
      "strength_clip": 1.0,
      "model": ["12", 0],
      "clip": ["13", 0]
    },
    "class_type": "LoraLoader"
  },
  "15": {
    "inputs": { "vae_name": "ae.safetensors" },
    "class_type": "VAELoader"
  },
  "11": {
    "inputs": {
      "width": 1024,
      "height": 1024,
      "batch_size": 1
    },
    "class_type": "EmptySD3LatentImage"
  },
  "18": {
    "inputs": { "text": "", "clip": ["20", 1] },
    "class_type": "CLIPTextEncode"
  },
  "10": {
    "inputs": {
      "text": "low quality, blurry, distorted, watermark",
      "clip": ["20", 1]
    },
    "class_type": "CLIPTextEncode"
  },
  "16": {
    "inputs": {
      "seed": 42,
      "steps": 6,
      "cfg": 1.0,
      "sampler_name": "euler",
      "scheduler": "simple",
      "denoise": 1.0,
      "model": ["20", 0],
      "positive": ["18", 0],
      "negative": ["10", 0],
      "latent_image": ["11", 0]
    },
    "class_type": "KSampler"
  },
  "17": {
    "inputs": { "samples": ["16", 0], "vae": ["15", 0] },
    "class_type": "VAEDecode"
  },
  "9": {
    "inputs": { "filename_prefix": "LoRA_Test", "images": ["17", 0] },
    "class_type": "SaveImage"
  }
}

def run_test():
    prompt_text = "A full body shot of a beautiful young Korean woman, wearing a tight-fitting modern white dress, slim and curvy hourglass figure, standing in a minimalist modern studio, soft studio lighting, high resolution, realistic skin texture, 8k"
    
    print(f"🚀 LoRA [{LORA_NAME}] 테스트 생성을 시작합니다 (총 2장)...")
    
    for i in range(2):
        wf = json.loads(json.dumps(workflow_template))
        wf["18"]["inputs"]["text"] = prompt_text
        wf["16"]["inputs"]["seed"] = int(time.time()) + i
        
        try:
            res = queue_prompt(wf)
            p_id = res['prompt_id']
            print(f"📤 [{i+1}/2] 큐 등록 완료 (ID: {p_id}). 대기 중...")
            
            # 수거 로직은 각 루프마다 기다리거나, 마지막에 한꺼번에 가능하지만 간단하게 루프별로 대기
            while True:
                history = get_history(p_id)
                if p_id in history:
                    print(f"✨ [{i+1}/2] 생성 완료! 수거 중...")
                    outputs = history[p_id]['outputs']['9']['images']
                    for img in outputs:
                        file_name = img['filename']
                        src = os.path.join(OUTPUT_DIR, file_name)
                        dst = os.path.join(DOWNLOADS_DIR, file_name)
                        if os.path.exists(src):
                            shutil.move(src, dst)
                            print(f"🚚 이동 완료: {file_name}")
                    break
                time.sleep(3)
        except Exception as e:
            print(f"❌ 생성 실패: {e}")

if __name__ == "__main__":
    run_test()

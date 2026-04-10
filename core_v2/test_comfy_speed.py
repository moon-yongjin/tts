import json
import urllib.request
import time
import os
import random
import sys

# ComfyUI 설정
SERVER_ADDRESS = "127.0.0.1:8188"
OUTPUT_DIR = os.path.expanduser("~/Downloads/Comfy_Speed_Test")
os.makedirs(OUTPUT_DIR, exist_ok=True)

def queue_prompt(prompt_workflow):
    p = {"prompt": prompt_workflow}
    data = json.dumps(p).encode('utf-8')
    req = urllib.request.Request(f"http://{SERVER_ADDRESS}/prompt", data=data)
    with urllib.request.urlopen(req) as response:
        return json.loads(response.read())

def get_history(prompt_id):
    try:
        with urllib.request.urlopen(f"http://{SERVER_ADDRESS}/history/{prompt_id}") as response:
            return json.loads(response.read())
    except:
        return {}

def get_z_image_workflow(prompt, seed, width=640, height=640, steps=4):
    # batch_generate_v3.py 기반 Z-Image Turbo 워크플로우
    return {
      "12": {
        "inputs": {
          "unet_name": "z_image_turbo-Q5_K_M.gguf"
        },
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
      "15": {
        "inputs": {
          "vae_name": "ae.safetensors"
        },
        "class_type": "VAELoader"
      },
      "11": {
        "inputs": {
          "width": width,
          "height": height,
          "batch_size": 1
        },
        "class_type": "EmptySD3LatentImage"
      },
      "18": {
        "inputs": {
          "text": prompt,
          "clip": ["13", 0]
        },
        "class_type": "CLIPTextEncode"
      },
      "10": {
        "inputs": {
          "text": "foreigners, anime, cartoon, illustration, drawing, text, watermark, low quality, blurry, distorted",
          "clip": ["13", 0]
        },
        "class_type": "CLIPTextEncode"
      },
      "16": {
        "inputs": {
          "seed": seed,
          "steps": steps,
          "cfg": 1.0,
          "sampler_name": "euler",
          "scheduler": "simple",
          "denoise": 1.0,
          "model": ["12", 0],
          "positive": ["18", 0],
          "negative": ["10", 0],
          "latent_image": ["11", 0]
        },
        "class_type": "KSampler"
      },
      "17": {
        "inputs": {
          "samples": ["16", 0],
          "vae": ["15", 0]
        },
        "class_type": "VAEDecode"
      },
      "9": {
        "inputs": {
          "filename_prefix": f"SpeedTest_{width}x{height}_{steps}steps",
          "images": ["17", 0]
        },
        "class_type": "SaveImage"
      }
    }

def main():
    prompt_text = "A photorealistic cinematic portrait of a Korean warrior in a bamboo forest, high detail, sharp focus"
    if len(sys.argv) > 1:
        prompt_text = sys.argv[1]
        
    print(f"\n⚡️ [ComfyUI Z-Image Test] 시작")
    print(f"📐 설정: 640x640, 4 Steps")
    print(f"📝 프롬프트: {prompt_text}")
    
    seed = random.randint(1, 1000000000)
    workflow = get_z_image_workflow(prompt_text, seed)
    
    start_time = time.time()
    try:
        req_res = queue_prompt(workflow)
        prompt_id = req_res['prompt_id']
        print(f"   📤 큐 등록 완료 (ID: {prompt_id})")
        
        while True:
            history = get_history(prompt_id)
            if prompt_id in history:
                elapsed = time.time() - start_time
                print(f"\n✅ 생성 완료!")
                print(f"⏱️ 총 소요 시간: {elapsed:.2f}초")
                break
            time.sleep(0.5)
            
    except Exception as e:
        print(f"❌ 에러 발생: {e}")

if __name__ == "__main__":
    main()

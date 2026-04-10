import json
import urllib.request
import time
import os
import shutil

def queue_prompt(prompt):
    p = {"prompt": prompt}
    data = json.dumps(p).encode('utf-8')
    req = urllib.request.Request("http://127.0.0.1:8188/prompt", data=data)
    return json.loads(urllib.request.urlopen(req).read())

def get_history(prompt_id):
    with urllib.request.urlopen(f"http://127.0.0.1:8188/history/{prompt_id}") as response:
        return json.loads(response.read())

# Workflow definition with LoRA Loader (Node 20)
workflow = {
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
      "width": 640,
      "height": 640,
      "batch_size": 1
    },
    "class_type": "EmptyLatentImage"
  },
  "18": {
    "inputs": {
      "text": "A stunning cinematic portrait of a beautiful woman with sharp features, dramatic lighting, 8k resolution, highly detailed skin texture, masterpiece, photorealistic, depth of field",
      "clip": ["13", 0]
    },
    "class_type": "CLIPTextEncode"
  },
  "10": {
    "inputs": {
      "text": "low quality, blurry, distorted, deformed, extra fingers, malformed hands, bad anatomy, anime, cartoon, text, watermark",
      "clip": ["13", 0]
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
      "filename_prefix": "NoLoRA_640_Test",
      "images": ["17", 0]
    },
    "class_type": "SaveImage"
  }
}

print("🎨 Starting batch generation (5 images) at 640x640 - NO LoRA...")
seeds = [111, 222, 333, 444, 555]
downloads_dir = "/Users/a12/Downloads"
os.makedirs(downloads_dir, exist_ok=True)

for i, seed in enumerate(seeds):
    start_time = time.time()
    print(f"🎬 Generating Image {i+1}/5 (Seed: {seed})...")
    workflow["16"]["inputs"]["seed"] = seed
    
    try:
        prompt_response = queue_prompt(workflow)
        prompt_id = prompt_response['prompt_id']
        print(f"   Prompt queued, ID: {prompt_id}")

        while True:
            history = get_history(prompt_id)
            if prompt_id in history:
                elapsed = time.time() - start_time
                file_info = history[prompt_id]['outputs']['9']['images'][0]
                file_name = file_info['filename']
                source_path = os.path.join("/Users/a12/projects/tts/ComfyUI/output", file_name)
                target_path = os.path.join(downloads_dir, f"LoRA_640_{i+1}_{file_name}")
                
                # Copy to Downloads
                shutil.copy(source_path, target_path)
                print(f"   ✅ Image {i+1} saved ({elapsed:.2f}s): {target_path}")
                break
            else:
                time.sleep(1)
    except Exception as e:
        print(f"   ❌ Error at Image {i+1}: {e}")

print("\n✨ All tasks completed.")

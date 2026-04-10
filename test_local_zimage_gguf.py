import json
import urllib.request
import time
import os

def queue_prompt(prompt):
    p = {"prompt": prompt}
    data = json.dumps(p).encode('utf-8')
    req = urllib.request.Request("http://127.0.0.1:8188/prompt", data=data)
    return json.loads(urllib.request.urlopen(req).read())

def get_history(prompt_id):
    with urllib.request.urlopen(f"http://127.0.0.1:8188/history/{prompt_id}") as response:
        return json.loads(response.read())

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
      "width": 1024,
      "height": 1024,
      "batch_size": 1
    },
    "class_type": "EmptySD3LatentImage"
  },
  "18": {
    "inputs": {
      "text": "A group of three diverse friends sitting at a simple wooden table, laughing and talking, their hands and fingers are clearly visible on the table, holding coffee cups, photorealistic, sharp focus on hands and faces, masterpiece, 8k, simplified clean background",
      "clip": ["13", 0]
    },
    "class_type": "CLIPTextEncode"
  },
  "10": {
    "inputs": {
      "text": "anime, cartoon, illustration, drawing, text, watermark, low quality, blurry, distorted, deformed, extra fingers, malformed hands, fused fingers, bad anatomy",
      "clip": ["13", 0]
    },
    "class_type": "CLIPTextEncode"
  },
  "16": {
    "inputs": {
      "seed": 101,
      "steps": 4,
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
      "filename_prefix": "Local_ZImage_GGUF_Test",
      "images": ["17", 0]
    },
    "class_type": "SaveImage"
  }
}

print("Queuing GGUF test prompt to local ComfyUI...")
prompt_response = queue_prompt(workflow)
prompt_id = prompt_response['prompt_id']
print(f"Prompt queued, ID: {prompt_id}")

while True:
    history = get_history(prompt_id)
    if prompt_id in history:
        file_name = history[prompt_id]['outputs']['9']['images'][0]['filename']
        source_path = os.path.join("/Users/a12/projects/tts/ComfyUI/output", file_name)
        target_path = os.path.join("/Users/a12/Downloads", file_name)
        
        # Copy to Downloads
        import shutil
        shutil.copy(source_path, target_path)
        
        print(f"Generation complete!")
        print(f"Image saved in ComfyUI: {file_name}")
        print(f"Image copied to Downloads: {target_path}")
        break
    else:
        print("Waiting for generation...")
        time.sleep(2)

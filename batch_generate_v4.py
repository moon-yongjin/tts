import json
import urllib.request
import time
import os
import shutil

# Configuration
COMFYUI_URL = "http://127.0.0.1:8188"
OUTPUT_DIR = "/Users/a12/projects/tts/ComfyUI/output"
DOWNLOADS_DIR = "/Users/a12/Downloads/Script_Scenes_Optimized"

if not os.path.exists(DOWNLOADS_DIR):
    os.makedirs(DOWNLOADS_DIR)

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

# 10 Scenes based on the script
prompts = [
    "A wealthy young woman (Jiyun) in a luxury beige coat, screaming in rage, throwing a designer bag at an old woman (Jeomrye) in a greasy junkyard. Cinematic, 8k.",
    "Jiyun kicking a rusted car part into the mud. Mud splashing. Junkyard background. Cinematic, 8k.",
    "Old Jeomrye wiping sweat with a greasy hand. Rusted parts everywhere. Worn work clothes. Cinematic, 8k.",
    "Jiyun grabbing Jeomrye by the collar, pushing her against a rusted scrap car. Intense rage. Cinematic, 8k.",
    "A fleet of luxury black sedans racing into a dusty junkyard, creating a giant dust cloud. Cinematic, 8k.",
    "Hundreds of men in black suits standing in perfect rows in a messy scrap yard. Wide shot. Cinematic, 8k.",
    "A powerful businessman (Minseok) stepping out of a limousine. Sharp suit. Junkyard. Cinematic, 8k.",
    "Minseok grabbing Jiyun's wrist with a cold, terrifying expression. Close up. Cinematic, 8k.",
    "Minseok throwing Jiyun onto the dirty ground. Jiyun crying in the dirt. Wide shot. Cinematic, 8k.",
    "Minseok gently helping Jeomrye stand up. Oil-covered mother and clean-suited son. Emotional contrast. Cinematic, 8k."
]

workflow_template = {
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
      "text": "",
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
      "filename_prefix": "Scene",
      "images": ["17", 0]
    },
    "class_type": "SaveImage"
  }
}

print(f"Starting optimized sequential generation for 10 scenes...")

for i, p_text in enumerate(prompts):
    start_t = time.time()
    workflow_template["18"]["inputs"]["text"] = p_text
    workflow_template["16"]["inputs"]["seed"] = 300 + i
    workflow_template["9"]["inputs"]["filename_prefix"] = f"Opt_Scene_{i+1:02d}"
    
    print(f"Generating Scene {i+1}/10...")
    response = queue_prompt(workflow_template)
    prompt_id = response['prompt_id']
    
    while True:
        history = get_history(prompt_id)
        if prompt_id in history:
            time_taken = time.time() - start_t
            print(f"Scene {i+1} complete in {time_taken:.1f}s!")
            outputs = history[prompt_id]['outputs']['9']['images']
            for img in outputs:
                file_name = img['filename']
                shutil.copy(os.path.join(OUTPUT_DIR, file_name), os.path.join(DOWNLOADS_DIR, file_name))
            break
        time.sleep(2)

print(f"\nAll 10 images generated and copied to: {DOWNLOADS_DIR}")

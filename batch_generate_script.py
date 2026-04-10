import json
import urllib.request
import time
import os
import shutil

# Configuration
COMFYUI_URL = "http://127.0.0.1:8188"
OUTPUT_DIR = "/Users/a12/projects/tts/ComfyUI/output"
DOWNLOADS_DIR = "/Users/a12/Downloads/Script_Scenes"

if not os.path.exists(DOWNLOADS_DIR):
    os.makedirs(DOWNLOADS_DIR)

def queue_prompt(prompt):
    p = {"prompt": prompt}
    data = json.dumps(p).encode('utf-8')
    req = urllib.request.Request(f"{COMFYUI_URL}/prompt", data=data)
    return json.loads(urllib.request.urlopen(req).read())

def get_history(prompt_id):
    with urllib.request.urlopen(f"{COMFYUI_URL}/history/{prompt_id}") as response:
        return json.loads(response.read())

# 10 Scenes based on the script
prompts = [
    "A wealthy young woman (Jiyun) in a luxury beige coat, screaming in rage, throwing a high-end designer bag at the back of an old woman (Jeomrye) who is covered in oil and grease. Setting: a pile of greasy, rusted scrap metal in a massive junkyard. Cinematic, photorealistic, 8k, sharp focus.",
    "Angry Jiyun kicking a heavy rusted engine part into the mud. Mud splashing everywhere. Messy junkyard background. Cinematic, photorealistic, 8k.",
    "Old Jeomrye wiping sweat from her forehead with a greasy, oil-stained hand. Rusted car parts everywhere. She is wearing worn-out work clothes. Cinematic, photorealistic, 8k.",
    "Jiyun aggressively grabbing Jeomrye by the collar, pushing her back against a rusted scrap car. Intense facial expressions. Junkyard atmosphere. Cinematic, photorealistic, 8k.",
    "A massive fleet of dozens of identical luxury black sedans racing into a dusty junkyard, creating a giant dust cloud. Sun rays through dust. High speed shot. Cinematic, photorealistic, 8k.",
    "Hundreds of tall men in crisp identical black suits and sunglasses, standing in perfect rows in the foreground of a messy scrap metal yard. Cinematic, wide shot, photorealistic, 8k.",
    "A powerful businessman (Minseok) stepping out of a luxury black limousine at the junkyard. Intense, lethal gaze. Expensive sharp suit. Junkyard background. Cinematic, photorealistic, 8k.",
    "Minseok grabbing Jiyun's wrist tightly with a cold, terrifying expression. Jiyun looks terrified and shocked. Close up. Cinematic, photorealistic, 8k.",
    "Minseok throwing Jiyun onto the dirty, dusty ground of the junk yard. Jiyun on her knees in the dirt, crying. Wide shot. Cinematic, photorealistic, 8k.",
    "Minseok gently and respectfully helping Jeomrye stand up from the ground. Jeomrye is covered in oil, Minseok is in a clean suit. Emotional contrast. Cinematic, photorealistic, 8k."
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
      "batch_size": 4  # As requested: batch size 4
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

queued_ids = []

print(f"Starting generation of {len(prompts)} scenes with batch size 4...")

# Note: We generate all scenes. Since each batch is 4, we get 40 images in total (4 per scene).
# If the user wants EXACTLY 10 images, we could stop earlier, but usually batching 
# refers to the technical setting.
for i, p_text in enumerate(prompts):
    workflow_template["18"]["inputs"]["text"] = p_text
    workflow_template["16"]["inputs"]["seed"] = 101 + i  # Unique seed per scene
    workflow_template["9"]["inputs"]["filename_prefix"] = f"Scene_{i+1:02d}"
    
    print(f"Queuing Scene {i+1}...")
    response = queue_prompt(workflow_template)
    queued_ids.append((i+1, response['prompt_id']))
    time.sleep(1) # Small delay

print("\nAll scenes queued. Waiting for completion and copying images...")

completed = set()
while len(completed) < len(queued_ids):
    for scene_num, prompt_id in queued_ids:
        if prompt_id in completed:
            continue
            
        history = get_history(prompt_id)
        if prompt_id in history:
            print(f"Scene {scene_num} complete!")
            outputs = history[prompt_id]['outputs']['9']['images']
            for img in outputs:
                file_name = img['filename']
                source = os.path.join(OUTPUT_DIR, file_name)
                target = os.path.join(DOWNLOADS_DIR, file_name)
                shutil.copy(source, target)
            
            completed.add(prompt_id)
            print(f"Copied {len(outputs)} images for Scene {scene_num} to Downloads.")
            
    if len(completed) < len(queued_ids):
        time.sleep(5)

print(f"\nAll scenes finished! Check results in: {DOWNLOADS_DIR}")

import json
import urllib.request
import time
import os
import shutil
import random

# [설정]
COMFYUI_URL = "http://127.0.0.1:8188"
OUTPUT_DIR = "/Users/a12/projects/tts/ComfyUI/output"
DOWNLOADS_DIR = f"/Users/a12/Downloads/Jumo_Comfy_Final_{time.strftime('%m%d_%H%M')}"

if not os.path.exists(DOWNLOADS_DIR):
    os.makedirs(DOWNLOADS_DIR)

# [국장님 확정 비주얼 가이드]
# - 얼굴: 한국 최신 인기 아이돌 스타일 (K-pop Idol face)
# - 복장: 천민/서민들이 입는 흰색/아이보리 계통의 거친 무명 일하는 옷 (White rough cotton clothes)
# - 체형: 푸짐하고 넉넉한 뚱뚱한 체격 (Plump, generous full-figured body)
# - 배경: 정통 조선 시대 주막 (Authentic Joseon Tavern)

character_prompt = "A stunning Korean woman with a trendy K-pop Idol style face, extremely beautiful facial features, plump and generous full-figured thick body, wearing white rough cotton commoner working clothes, authentic 18th century Joseon dynasty tavern background"

PROMPTS = [
    f"{character_prompt}, secretly mixing water into a liquor jar, greedy but gorgeous idol face, cinematic lighting, 8k detail",
    f"{character_prompt}, showing a large ceramic jar to a handsome traveler, tavern courtyard, sharp focus, detailed textures",
    f"{character_prompt}, pouring watered-down wine with a clever smile, beautiful idol facial features, realistic rough cotton texture",
    f"{character_prompt}, watching a traveler pouring liquid back into the barrel with a shocked expression, dynamic scene, expressive face",
    f"{character_prompt}, looking at her ruined barrel with a dejected face, sunset lighting, masterpiece, high quality"
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
      "width": 640,
      "height": 640,
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
      "text": "silk, colorful, noble dress, foreigners, anime, cartoon, text, watermark, low quality, blurry, distorted, bad anatomy",
      "clip": ["13", 0]
    },
    "class_type": "CLIPTextEncode"
  },
  "16": {
    "inputs": {
      "seed": 101,
      "steps": 8,
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
      "filename_prefix": "Jumo",
      "images": ["17", 0]
    },
    "class_type": "SaveImage"
  }
}

def queue_prompt(prompt):
    p = {"prompt": prompt}
    data = json.dumps(p).encode('utf-8')
    print(f"📡 Sending to ComfyUI: {json.dumps(p, indent=2)[:500]}...")
    req = urllib.request.Request(f"{COMFYUI_URL}/prompt", data=data, method='POST')
    req.add_header('Content-Type', 'application/json')
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read())
    except urllib.error.HTTPError as e:
        print(f"❌ HTTP Error {e.code}: {e.read().decode('utf-8')}")
        raise e

def get_history(prompt_id):
    try:
        with urllib.request.urlopen(f"{COMFYUI_URL}/history/{prompt_id}") as response:
            return json.loads(response.read())
    except:
        return {}

def generate_scene(scene_num, p_text):
    wf = json.loads(json.dumps(workflow_template))
    wf["18"]["inputs"]["text"] = p_text
    wf["16"]["inputs"]["seed"] = random.randint(1, 1000000)
    wf["9"]["inputs"]["filename_prefix"] = f"Jumo_Comfy_Scene_{scene_num:02d}"
    
    print(f"🎬 Scene {scene_num}/{len(PROMPTS)} 생성 중...")
    response = queue_prompt(wf)
    prompt_id = response['prompt_id']
    
    while True:
        history = get_history(prompt_id)
        if prompt_id in history:
            outputs = history[prompt_id]['outputs']['9']['images']
            for img in outputs:
                file_name = img['filename']
                src_path = os.path.join(OUTPUT_DIR, file_name)
                dst_path = os.path.join(DOWNLOADS_DIR, file_name)
                # Wait a bit for file to be written
                time.sleep(1)
                if os.path.exists(src_path):
                    shutil.move(src_path, dst_path)
                    print(f"✅ 완료: {file_name}")
            return
        time.sleep(2)

if __name__ == "__main__":
    print(f"🚀 총 {len(PROMPTS)}장의 이미지 생성을 시작합니다 (ComfyUI 기반).")
    print(f"📂 저장 경로: {DOWNLOADS_DIR}")
    for i, p in enumerate(PROMPTS):
        generate_scene(i+1, p)
    print(f"\n✨ 모든 생성 작업이 완료되었습니다!")
    os.system(f"open {DOWNLOADS_DIR}")

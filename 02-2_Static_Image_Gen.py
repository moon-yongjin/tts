import json
import urllib.request
import time
import os
import shutil
import random

# [설정]
COMFYUI_URL = "http://127.0.0.1:8188"
OUTPUT_DIR = "/Users/a12/projects/tts/ComfyUI/output"
DOWNLOADS_DIR = f"/Users/a12/Downloads/Story_Scenes_{time.strftime('%m%d_%H%M')}"

if not os.path.exists(DOWNLOADS_DIR):
    os.makedirs(DOWNLOADS_DIR)

# [사용자 확정 프롬프트 리스트 - 성별 교정 (남성 주인공)]
# [동적 프롬프트 로드 로직 추가]
JSON_PROMPT_PATH = "/Users/a12/projects/tts/Ollama_Studio/scene_prompts.json"
PROMPTS = []

if os.path.exists(JSON_PROMPT_PATH):
    try:
        with open(JSON_PROMPT_PATH, "r", encoding="utf-8") as f:
            PROMPTS = json.load(f)
        print(f"📂 [자동화] '{JSON_PROMPT_PATH}'에서 {len(PROMPTS)}개의 장면을 불러왔습니다.")
    except Exception as e:
        print(f"⚠️ [자동화] JSON 로드 중 오류: {e}")

if not PROMPTS:
    # 기본 폴백 프롬프트 (파일이 없을 경우 대비)
    PROMPTS = [
        "Watercolor style, a peaceful winter landscape with falling snow",
        "Watercolor style, a cozy fireplace in a warm room"
    ]
    print("ℹ️ [자동화] 자동화 데이터가 없어 기본 프롬프트를 사용합니다.")

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
      "text": "foreigners, anime, cartoon, illustration, drawing, text, watermark, low quality, blurry, distorted, deformed, extra fingers, malformed hands, fused fingers, bad anatomy",
      "clip": ["13", 0]
    },
    "class_type": "CLIPTextEncode"
  },
  "16": {
    "inputs": {
      "seed": 101,
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
      "filename_prefix": "Story",
      "images": ["17", 0]
    },
    "class_type": "SaveImage"
  }
}

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

def generate_scene(scene_num, p_text):
    wf = json.loads(json.dumps(workflow_template))
    # 퀄리티 향상을 위한 베이스 지침 추가
    high_quality_base = "detailed watercolor, soft brush strokes, tender lighting, clean composition, high resolution"
    wf["18"]["inputs"]["text"] = f"{p_text}, {high_quality_base}"
    wf["16"]["inputs"]["seed"] = random.randint(1, 1000000)
    wf["9"]["inputs"]["filename_prefix"] = f"Story_Scene_{scene_num:02d}"
    
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
                if os.path.exists(src_path):
                    shutil.move(src_path, dst_path)
                    print(f"✅ 완료: {file_name}")
            return
        time.sleep(2)

if __name__ == "__main__":
    print(f"🚀 총 {len(PROMPTS)}장의 이미지 생성을 시작합니다.")
    print(f"📂 저장 경로: {DOWNLOADS_DIR}")
    for i, p in enumerate(PROMPTS):
        generate_scene(i+1, p)
    print(f"\n✨ 모든 생성 작업이 완료되었습니다!")
    os.system(f"open {DOWNLOADS_DIR}")

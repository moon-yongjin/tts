import json
import urllib.request
import time
import os
import shutil

# [설정] Local ComfyUI
COMFYUI_URL = "http://127.0.0.1:8188"
OUTPUT_DIR = "/Users/a12/projects/tts/ComfyUI/output"
DOWNLOADS_DIR = "/Users/a12/Downloads/Character_Dataset_20_Late30s"

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

# Z-Image Turbo (GGUF) 워크플로우 템플릿
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
    "inputs": { "text": "", "clip": ["13", 0] },
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
    "inputs": { "samples": ["16", 0], "vae": ["15", 0] },
    "class_type": "VAEDecode"
  },
  "9": {
    "inputs": { "filename_prefix": "Char_Late30s", "images": ["17", 0] },
    "class_type": "SaveImage"
  }
}

# 캐릭터 앵커 프롬프트 (Local용 - 30대 후반, 긴 머리, 평범한 옷, 풍만함)
BASE_CHARACTER_PROMPT = "A beautiful Korean woman in her late 30s, long flowing dark hair, slightly longer than shoulder length, elegant and natural features, very large breasts, extremely voluptuous and curvy full figure, not skinny, healthy glamorous body, wearing plain and casual everyday clothing, simple high-quality cotton t-shirt and comfortable cardigan, modest but stylish, masterpiece, high quality, photorealistic, 8k, sharp focus"

# 조명/배경 변주 (학습용 다양성 확보)
VARIATIONS = [
    "indoor, cozy modern living room, soft morning sunlight",
    "indoor, stylish kitchen background, natural day lighting",
    "outdoor, quiet park bench, overcast soft lighting",
    "indoor, minimalist bedroom background, warm evening light",
    "outdoor, balcony with city view, bright afternoon light"
]

def run_character_batch(count=20):
    print(f"🚀 [Local] 새 캐릭터(30대 후반) 데이터셋 생성을 시작합니다 (총 {count}장)")
    print(f"🔗 Target: {COMFYUI_URL}")
    
    prompt_ids = []
    for i in range(count):
        idx = i + 1
        var = VARIATIONS[i % len(VARIATIONS)]
        full_prompt = f"{BASE_CHARACTER_PROMPT}, {var}"
        
        wf = json.loads(json.dumps(workflow_template))
        wf["18"]["inputs"]["text"] = full_prompt
        wf["16"]["inputs"]["seed"] = int(time.time() * 1000) + 5000 + i # 다른 시드 대역 사용
        wf["9"]["inputs"]["filename_prefix"] = f"Char_Late30s_{idx:02d}"
        
        print(f"📤 [{idx:02d}/{count}] 로컬 큐 등록 중... (배경: {var.split(',')[1].strip()})")
        try:
            res = queue_prompt(wf)
            prompt_ids.append((idx, res['prompt_id']))
            time.sleep(0.5)
        except Exception as e:
            print(f"❌ [{idx:02d}] 큐 등록 실패: {e}")

    print(f"\n✅ {len(prompt_ids)}개 이미지가 컨피 큐에 등록되었습니다. 수거를 시작합니다.")

    pending = prompt_ids.copy()
    while pending:
        for item in pending[:]:
            idx, p_id = item
            history = get_history(p_id)
            if p_id in history:
                print(f"✨ [{idx:02d}] 생성 완료! 이동 중...")
                outputs = history[p_id]['outputs']['9']['images']
                for img in outputs:
                    file_name = img['filename']
                    src = os.path.join(OUTPUT_DIR, file_name)
                    dst = os.path.join(DOWNLOADS_DIR, file_name)
                    if os.path.exists(src):
                        shutil.move(src, dst)
                        print(f"🚚 이동 완료: {file_name} -> {DOWNLOADS_DIR}")
                pending.remove(item)
        time.sleep(5)

    print(f"\n🎉 20장의 キャラクター 데이터셋 수거가 모두 끝났습니다!")
    print(f"📂 경로: {DOWNLOADS_DIR}")

if __name__ == "__main__":
    run_character_batch(20)

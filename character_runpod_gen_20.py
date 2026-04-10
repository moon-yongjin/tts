import json
import urllib.request
import time
import os

# [설정] RunPod 연결용 (보안 터널 8181 사용)
COMFYUI_URL = "http://127.0.0.1:8181"

def queue_prompt(prompt):
    p = {"prompt": prompt}
    data = json.dumps(p).encode('utf-8')
    req = urllib.request.Request(f"{COMFYUI_URL}/prompt", data=data)
    return json.loads(urllib.request.urlopen(req).read())

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
    "inputs": { "filename_prefix": "RunPod_Char", "images": ["17", 0] },
    "class_type": "SaveImage"
  }
}

# 캐릭터 앵커 프롬프트 (RunPod용 - 30대 후반, 긴 머리, 평범한 옷, 풍만함)
BASE_CHARACTER_PROMPT = "A beautiful Korean woman in her late 30s, long flowing dark hair, slightly longer than shoulder length, elegant and natural features, very large breasts, extremely voluptuous and curvy full figure, not skinny, healthy glamorous body, wearing plain and casual everyday clothing, simple high-quality cotton t-shirt and comfortable cardigan, modest but stylish, masterpiece, high quality, photorealistic, 8k, sharp focus"

# 조명/배경 변주 (학습용 다양성 확보)
VARIATIONS = [
    "indoor, cozy modern living room, soft morning sunlight",
    "indoor, stylish kitchen background, natural day lighting",
    "outdoor, quiet park bench, overcast soft lighting",
    "indoor, minimalist bedroom background, warm evening light",
    "outdoor, balcony with city view, bright afternoon light"
]

def run_runpod_character_batch(count=20):
    print(f"🚀 [RunPod] 새 캐릭터 데이터셋 생성을 시작합니다 (총 {count}장)")
    print(f"🔗 Target: {COMFYUI_URL}")
    
    for i in range(count):
        idx = i + 1
        var = VARIATIONS[i % len(VARIATIONS)]
        full_prompt = f"{BASE_CHARACTER_PROMPT}, {var}"
        
        wf = json.loads(json.dumps(workflow_template))
        wf["18"]["inputs"]["text"] = full_prompt
        wf["16"]["inputs"]["seed"] = int(time.time() * 1000) + i
        wf["9"]["inputs"]["filename_prefix"] = f"RunPod_NewChar_{idx:02d}"
        
        print(f"📤 [{idx:02d}/{count}] 런팟 큐 등록 중... (배경: {var.split(',')[1].strip()})")
        try:
            res = queue_prompt(wf)
            # print(f"   ✅ prompt_id: {res['prompt_id']}")
            time.sleep(0.5)
        except Exception as e:
            print(f"❌ [{idx:02d}] 큐 등록 실패: {e}")

    print(f"\n✅ 20개 이미지가 런팟(RunPod) 큐에 모두 등록되었습니다!")
    print(f"🌐 http://localhost:8181 에서 진행 상황을 확인하실 수 있습니다.")
    print(f"📂 이미지는 런팟 서버의 /workspace/ComfyUI/output 폴더에 저장됩니다.")

if __name__ == "__main__":
    run_runpod_character_batch(20)

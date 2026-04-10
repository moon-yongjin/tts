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
    "inputs": { "filename_prefix": "RunPod_MILKnit", "images": ["17", 0] },
    "class_type": "SaveImage"
  }
}

# 캐릭터 앵커 프롬프트 (시어머니 - 니트, 더 수수한 얼굴/머리, 야한 몸, 큰 가슴)
# "머리도 조금더 수수하게", "옷은 니트 입은거", "가슴은 풍만하게"
BASE_CHARACTER_PROMPT = "A beautiful Korean woman in her late 50s to early 60s, extremely plain and modest natural grandmotherly face, very humble appearance, salt and pepper hair in a very simple and natural old-fashioned style, very large breasts, extremely voluptuous and curvy full figure, not skinny, healthy glamorous body, wearing a tight-fitting thin sexy knit sweater, revealing body shape, slightly sheer knit fabric, provocative look with a modest face, masterpiece, high quality, photorealistic, 8k, sharp focus"

# 조명/배경 변주
VARIATIONS = [
    "indoor, cozy living room with soft lighting",
    "indoor, traditional wooden house kitchen, natural light",
    "outdoor, peaceful countryside yard, soft daylight",
    "indoor, simple bedroom with warm lamps",
    "outdoor, quiet garden bench, afternoon soft lighting"
]

def run_runpod_character_batch(count=10):
    print(f"🚀 [RunPod] 시어머니 캐릭터(니트/수수 페이스) 데이터셋 생성을 시작합니다 (총 {count}장)")
    print(f"🔗 Target: {COMFYUI_URL}")
    
    for i in range(count):
        idx = i + 1
        var = VARIATIONS[i % len(VARIATIONS)]
        full_prompt = f"{BASE_CHARACTER_PROMPT}, {var}"
        
        wf = json.loads(json.dumps(workflow_template))
        wf["18"]["inputs"]["text"] = full_prompt
        # 기존 작업과 겹치지 않게 시드 오프셋 조절
        wf["16"]["inputs"]["seed"] = int(time.time() * 1000) + 18000 + i
        wf["9"]["inputs"]["filename_prefix"] = f"RunPod_MILKnit_{idx:02d}"
        
        print(f"📤 [{idx:02d}/{count}] 런팟 큐 등록 중... (배경: {var.split(',')[1].strip()})")
        try:
            res = queue_prompt(wf)
            time.sleep(0.5)
        except Exception as e:
            print(f"❌ [{idx:02d}] 큐 등록 실패: {e}")

    print(f"\n✅ 10개 이미지가 런팟(RunPod) 큐에 모두 등록되었습니다!")
    print(f"🌐 http://localhost:8181 에서 진행 상황을 확인하실 수 있습니다.")

if __name__ == "__main__":
    run_runpod_character_batch(10)

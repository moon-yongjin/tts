import json
import urllib.request
import time

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
      "seed": int(time.time()),
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
    "inputs": { "filename_prefix": "RunPod_Test_Push", "images": ["17", 0] },
    "class_type": "SaveImage"
  }
}

# 테스트 프롬프트
TEST_PROMPT = "A beautiful Korean woman in her late 30s, long flowing dark hair, elegant features, very large breasts, voluptuous body, wearing plain casual daily clothing, simple cotton t-shirt, masterpiece, high quality, photorealistic, 8k"

def run_test():
    print(f"🚀 [RunPod] 테스트 이미지 1장 푸쉬를 시작합니다...")
    wf = json.loads(json.dumps(workflow_template))
    wf["18"]["inputs"]["text"] = TEST_PROMPT
    
    try:
        res = queue_prompt(wf)
        print(f"✅ 큐 등록 성공! prompt_id: {res['prompt_id']}")
        print(f"🌐 http://localhost:8181 에서 생성되는지 확인해보세요.")
    except Exception as e:
        print(f"❌ 큐 등록 실패: {e}")

if __name__ == "__main__":
    run_test()

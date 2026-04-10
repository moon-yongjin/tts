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
  "12": { "inputs": { "unet_name": "z_image_turbo-Q5_K_M.gguf" }, "class_type": "UnetLoaderGGUF" },
  "13": { "inputs": { "clip_name": "qwen_3_4b_fp8_mixed.safetensors", "type": "qwen_image", "device": "default" }, "class_type": "CLIPLoader" },
  "15": { "inputs": { "vae_name": "ae.safetensors" }, "class_type": "VAELoader" },
  "11": { "inputs": { "width": 1024, "height": 1024, "batch_size": 1 }, "class_type": "EmptySD3LatentImage" },
  "18": { "inputs": { "text": "", "clip": ["13", 0] }, "class_type": "CLIPTextEncode" },
  "10": { "inputs": { "text": "man, male, boy, facial hair, foreigners, anime, cartoon, illustration, drawing, text, watermark, low quality, blurry, distorted, deformed, extra fingers, malformed hands, fused fingers, bad anatomy", "clip": ["13", 0] }, "class_type": "CLIPTextEncode" },
  "16": { "inputs": { "seed": 101, "steps": 6, "cfg": 1.0, "sampler_name": "euler", "scheduler": "simple", "denoise": 1.0, "model": ["12", 0], "positive": ["18", 0], "negative": ["10", 0], "latent_image": ["11", 0] }, "class_type": "KSampler" },
  "17": { "inputs": { "samples": ["16", 0], "vae": ["15", 0] }, "class_type": "VAEDecode" },
  "9": { "inputs": { "filename_prefix": "Dataset_MIL_V2", "images": ["17", 0] }, "class_type": "SaveImage" }
}

# --- 시어머니 앵커 (V2: 수수한 복장, 노출 전혀 없음) ---
# "헐벗은거나 가슴 파인거는 쓰면 안됨" 반영
MIL_ANCHOR_V2 = "A beautiful Korean grandmother in her 60s, (extremely plain and modest natural grandmotherly face), salt and pepper hair in a simple natural style, humble and elegant appearance, (wearing a modest and high-neck long-sleeve knit sweater), absolutely NO cleavage, NO skin exposure on chest, conservative clothing, (but having an extremely voluminous and glamorous body), curvy full figure, masterpiece, photorealistic, 8k"

VARIATIONS = [
    "indoor, cozy living room", "indoor, traditional kitchen", "outdoor, quiet countryside garden",
    "indoor, simple reading room", "outdoor, peaceful park bench", "indoor, warm dining area",
    "outdoor, greenhouse with plants", "indoor, well-lit hallway", "outdoor, balcony with sunset", "indoor, laundry room"
]

def run_mil_v2_dataset_generation(count=20):
    print(f"🚀 [RunPod] 시어머니(MIL V2 - 수수한 복장) 데이터셋 생성 시작 (총 {count}장)")
    
    for i in range(count):
        idx = i + 1
        var = VARIATIONS[i % len(VARIATIONS)]
        full_prompt = f"{MIL_ANCHOR_V2}, {var}, soft natural lighting, sharp focus"
        
        wf = json.loads(json.dumps(workflow_template))
        wf["18"]["inputs"]["text"] = full_prompt
        wf["16"]["inputs"]["seed"] = int(time.time() * 1000) + 70000 + i
        wf["9"]["inputs"]["filename_prefix"] = f"Dataset_MIL_V2_{idx:02d}"
        
        try:
            queue_prompt(wf)
            if idx % 5 == 0: print(f"📤 MIL V2 등록 완료: {idx}/{count}")
            time.sleep(0.3)
        except Exception as e:
            print(f"❌ MIL V2 {idx}번 실패: {e}")

    print(f"\n✅ 시어머니 V2 데이터셋 큐 등록 완료! http://localhost:8181")

if __name__ == "__main__":
    run_mil_v2_dataset_generation(20)

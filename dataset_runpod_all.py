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

# Z-Image Turbo 워크플로우 템플릿
workflow_template = {
  "12": { "inputs": { "unet_name": "z_image_turbo-Q5_K_M.gguf" }, "class_type": "UnetLoaderGGUF" },
  "13": { "inputs": { "clip_name": "qwen_3_4b_fp8_mixed.safetensors", "type": "qwen_image", "device": "default" }, "class_type": "CLIPLoader" },
  "15": { "inputs": { "vae_name": "ae.safetensors" }, "class_type": "VAELoader" },
  "11": { "inputs": { "width": 1024, "height": 1024, "batch_size": 1 }, "class_type": "EmptySD3LatentImage" },
  "18": { "inputs": { "text": "", "clip": ["13", 0] }, "class_type": "CLIPTextEncode" },
  "10": { "inputs": { "text": "foreigners, anime, cartoon, illustration, drawing, text, watermark, low quality, blurry, distorted, deformed, extra fingers, malformed hands, fused fingers, bad anatomy", "clip": ["13", 0] }, "class_type": "CLIPTextEncode" },
  "16": { "inputs": { "seed": 101, "steps": 6, "cfg": 1.0, "sampler_name": "euler", "scheduler": "simple", "denoise": 1.0, "model": ["12", 0], "positive": ["18", 0], "negative": ["10", 0], "latent_image": ["11", 0] }, "class_type": "KSampler" },
  "17": { "inputs": { "samples": ["16", 0], "vae": ["15", 0] }, "class_type": "VAEDecode" },
  "9": { "inputs": { "filename_prefix": "Dataset_MIL", "images": ["17", 0] }, "class_type": "SaveImage" }
}

# 공통 몸매/복장 앵커
BODY_ANCHOR = "extremely large breasts, very voluptuous and curvy full figure, not skinny, healthy glamorous body, wearing a very tight-fitting sexy revealing outfit"

# 캐릭터 정의
MIL_ANCHOR = f"A beautiful Korean grandmother in her 60s, salt and pepper natural hair, elegant but aged natural face, {BODY_ANCHOR}"
DIL1_ANCHOR = f"A beautiful Korean woman in her late 30s, sharp and cold features, arrogant face, short bob hair, {BODY_ANCHOR}"
DIL2_ANCHOR = f"A beautiful young Korean woman in her late 20s, kind and bright friendly face, long flowing hair, {BODY_ANCHOR}"

CHARACTERS = [
    {"name": "MIL", "anchor": MIL_ANCHOR, "prefix": "Dataset_MIL"},
    {"name": "DIL1", "anchor": DIL1_ANCHOR, "prefix": "Dataset_DIL1"},
    {"name": "DIL2", "anchor": DIL2_ANCHOR, "prefix": "Dataset_DIL2"}
]

# 배경 변주
VARIATIONS = [
    "indoor, cozy living room", "indoor, modern kitchen", "outdoor, sunny garden", 
    "indoor, luxury bedroom", "outdoor, urban street", "indoor, library",
    "indoor, department store", "outdoor, park bench", "indoor, traditional hanok", "outdoor, balcony"
]

def run_dataset_generation(count_per_char=20):
    print(f"🚀 [RunPod] 3개 캐릭터 통합 데이터셋 생성 시작 (총 {count_per_char * 3}장)")
    
    for char in CHARACTERS:
        print(f"\n👤 캐릭터: {char['name']} 생성 중...")
        for i in range(count_per_char):
            idx = i + 1
            var = VARIATIONS[i % len(VARIATIONS)]
            full_prompt = f"{char['anchor']}, {var}, photorealistic, 8k, masterpiece"
            
            wf = json.loads(json.dumps(workflow_template))
            wf["18"]["inputs"]["text"] = full_prompt
            wf["16"]["inputs"]["seed"] = int(time.time() * 1000) + i + (ord(char['name'][0]) * 100)
            wf["9"]["inputs"]["filename_prefix"] = f"{char['prefix']}_{idx:02d}"
            
            try:
                queue_prompt(wf)
                if idx % 5 == 0: print(f"📤 {char['name']} 큐 등록: {idx}/{count_per_char}")
                time.sleep(0.3)
            except Exception as e:
                print(f"❌ {char['name']} {idx}번 등록 실패: {e}")

    print(f"\n✅ 모든 큐 등록 완료! http://localhost:8181 에서 확인해 주세요.")

if __name__ == "__main__":
    run_dataset_generation(20)

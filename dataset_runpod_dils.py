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
  "9": { "inputs": { "filename_prefix": "Dataset_DIL", "images": ["17", 0] }, "class_type": "SaveImage" }
}

# --- 정교화된 며느리 앵커 (V6 기준) ---
DIL1_ANCHOR = "A stunningly beautiful Korean woman in her late 30s, sharp cold features, arrogant face, (medium bob hair style), wearing a (Dongtan-missy style sexy outfit) with an (extremely deep plunging neckline), revealing deep cleavage, extremely large breasts, very voluptuous and curvy body, healthy glamorous and full figure"
DIL2_ANCHOR = "A very beautiful Korean woman in her late 20s, (extremely pure and modest innocent face), kind and bright angelic smile, natural long hair, (but having an extremely glamorous and voluminous body), very large breasts, curvy full figure, wearing a thin and skin-tight sexy casual outfit"

CHARACTERS = [
    {"name": "DIL1", "anchor": DIL1_ANCHOR, "prefix": "Dataset_DIL1"},
    {"name": "DIL2", "anchor": DIL2_ANCHOR, "prefix": "Dataset_DIL2"}
]

VARIATIONS = [
    "indoor, luxury apartment living room", "indoor, high-end kitchen", "outdoor, sunny street",
    "indoor, stylish dressing room", "outdoor, coffee shop terrace", "indoor, cozy bedroom",
    "indoor, modern library", "outdoor, balcony with city view", "indoor, hotel lobby", "outdoor, peaceful park"
]

def run_dil_dataset_generation(count_per_char=20):
    print(f"🚀 [RunPod] 며느리 캐릭터(DIL1, DIL2) 데이터셋 생성 시작 (총 {count_per_char * 2}장)")
    
    for char in CHARACTERS:
        print(f"\n👤 {char['name']} (학습용 20장) 등록 중...")
        for i in range(count_per_char):
            idx = i + 1
            var = VARIATIONS[i % len(VARIATIONS)]
            # 20장을 채우기 위해 조명을 다르게 하거나 미세 변주
            lighting = "soft natural lighting" if i < 10 else "cinematic dramatic lighting"
            full_prompt = f"{char['anchor']}, {var}, {lighting}, photorealistic, masterpiece, 8k"
            
            wf = json.loads(json.dumps(workflow_template))
            wf["18"]["inputs"]["text"] = full_prompt
            wf["16"]["inputs"]["seed"] = int(time.time() * 1000) + i + (ord(char['name'][3]) * 500)
            wf["9"]["inputs"]["filename_prefix"] = f"{char['prefix']}_{idx:02d}"
            
            try:
                queue_prompt(wf)
                if idx % 5 == 0: print(f"📤 {char['name']} 등록 완료: {idx}/{count_per_char}")
                time.sleep(0.3)
            except Exception as e:
                print(f"❌ {char['name']} {idx}번 실패: {e}")

    print(f"\n✅ 모든 로라용 데이터셋 큐 등록 완료! http://localhost:8181")

if __name__ == "__main__":
    run_dil_dataset_generation(20)

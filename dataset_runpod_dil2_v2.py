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
  "9": { "inputs": { "filename_prefix": "Dataset_DIL2_V2", "images": ["17", 0] }, "class_type": "SaveImage" }
}

# DIL2 앵커 프롬프트 (극도로 상세화, 300자 이상 확보)
DIL2_PROMPT = "c2_dil2, a stunningly beautiful young Korean woman in her late 20s with an extremely pure and kind angelic face, innocent friendly expression that radiates warmth, natural long silky black hair flowing down her shoulders, possessing a distinctively chubby and plump healthy body, soft and voluminous thick figure with heavy curves, very large breasts with deep cleavage, curvy full figure that is both glamorous and healthy, masterful photorealistic texture of skin, wearing a sexy but cozy skin-tight casual outfit that fits her voluptuous body perfectly, high quality, 8k, sharp focus, cinematic lighting"

VARIATIONS = [
    "indoor, high-end luxury cozy living room with soft plush furniture, warm evening sun filtering through large windows, dust motes dancing in the light, peaceful and domestic atmosphere, highly detailed classical interior design with oil paintings and bookshelf, soft amber lighting",
    "indoor, sunny modern kitchen with clean marble countertops, bright morning light spilling in, fresh healthy breakfast prepared on the wooden table, candid close-up shot of her smiling kindly while holding a white ceramic coffee mug, vibrant and cheerful morning colors, morning dew outside",
    "outdoor, peaceful park bench under a large blooming cherry blossom tree, soft pink petals falling like snow around her, natural dappled sunlight through the leaves, serene and romantic springtime atmosphere, beautiful nature background with soft depth of field bokeh",
    "outdoor, urban street at blue hour just after sunset, glowing city lights and colorful neon signs in the background creating a cinematic night atmosphere, sharp contrast between her pure innocent face and the vibrant busy city night, highly detailed asphalt and sidewalk texture",
    "indoor, high-end department store clothing section with elegant mirrors, bright studio-quality lighting reflecting everywhere, sophisticated and premium shopping mall atmosphere, rich textures of expensive silk and velvet fabrics in the background, professional sales floor appearance",
    "indoor, warm and elegant dining area with a large mahogany table, soft candlelight creating a romantic and intimate mood, fine china and wine glasses set for a special dinner, her expression is gentle and inviting, sophisticated home decor in the background, soft shadows",
    "outdoor, high-rise luxury balcony at sunset, the sky painted in deep oranges and purples, panoramic city view in the distant background, gentle breeze blowing through her hair, she looks out at the horizon with a peaceful and thoughtful gaze, cinematic wide shot",
    "indoor, authentic messy laundry room with baskets of colorful clothes, soft afternoon light coming through a small window, a realistic and domestic scene of daily life, her pure face contrasting with the relatable everyday environment, high detail of soap bubbles and fabric textures",
    "outdoor, local supermarket aisle filled with vibrant vegetables and fruits, bright overhead fluorescent lighting, she is holding a grocery basket and looking at the camera with a friendly smile, a natural and candid slice of life moment, highly detailed product packaging",
    "indoor, modern minimalist hallway with polished concrete floors and abstract art on the walls, sharp geometric shadows from a skylight above, artistic and contemporary atmosphere, her voluptuous figure standing out against the simple and clean lines of the architecture"
]

def run_dil2_v2_dataset_generation(count=20):
    print(f"🚀 [RunPod] 둘째 며느리(DIL2 V2 - 통통/청순/글래머) 데이터셋 생성 시작 (총 {count}장)")
    
    for i in range(count):
        idx = i + 1
        var = VARIATIONS[i % len(VARIATIONS)]
        full_prompt = f"{DIL2_PROMPT}, {var}"
        
        wf = json.loads(json.dumps(workflow_template))
        wf["18"]["inputs"]["text"] = full_prompt
        wf["16"]["inputs"]["seed"] = int(time.time() * 1000) + 80000 + i
        wf["9"]["inputs"]["filename_prefix"] = f"Dataset_DIL2_V2_{idx:02d}"
        
        try:
            queue_prompt(wf)
            if idx % 5 == 0: print(f"📤 DIL2 V2 등록 완료: {idx}/{count}")
            time.sleep(0.3)
        except Exception as e:
            print(f"❌ DIL2 V2 {idx}번 실패: {e}")

    print(f"\n✅ 둘째 며느리 V2 데이터셋 큐 등록 완료! http://localhost:8181")

if __name__ == "__main__":
    run_dil2_v2_dataset_generation(20)

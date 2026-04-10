import json
import urllib.request
import time
import os
import shutil

# [설정]
COMFYUI_URL = "http://127.0.0.1:8188"
OUTPUT_DIR = "/Users/a12/projects/tts/ComfyUI/output"
DOWNLOADS_DIR = "/Users/a12/Downloads/LoRA_Training_Dataset_V3_Retry"

os.makedirs(DOWNLOADS_DIR, exist_ok=True)

# 한국형 아이돌 비주얼 + 깨끗한 화장 + 고유 단발머리 강조
BASE_CHARACTER = "A stunningly beautiful K-pop idol visual Korean woman. She has a unique and stylish short messy black layered bob hair, exactly like a high-end fashion model. Her face is sharp, sophisticated, and incredibly pretty. Clear pale glass skin, clean and natural idol-style makeup, bright and sparkling large eyes, NO heavy under-eye makeup or dark shadows. Slim yet glamorous and curvy hourglass body."

NEGATIVE_PROMPT = "heavy makeup, under-eye shadow, dark circles, messy eye makeup, thick eyeliner, dirty face, low quality, blurry, distorted, watermark, bad anatomy, text, cartoon, illustration, messy hair, old, mature, western features"

# 정예 10개 프롬프트 (아이돌 화보 느낌)
SCENES = [
    {"outfit": "a sleek black sleeveless evening dress", "angle": "Full body shot, standing in a chic modern living room, elegant pose"},
    {"outfit": "a trendy white crop top and high-waisted wide-leg denim", "angle": "Full body shot, urban street background, natural sunlight, idol street style"},
    {"outfit": "a luxurious red silk mini dress", "angle": "Full body shot, 45-degree angle, high-end hotel lobby background"},
    {"outfit": "a sophisticated white blazer with matching shorts", "angle": "Full body shot, studio lighting, professional fashion photography"},
    {"outfit": "a cute oversized pastel knit sweater and mini skirt", "angle": "Full body shot, sitting on a designer chair, soft warm lighting"},
    {"outfit": "a classic black leather jacket and tight black pants", "angle": "Full body shot, side view, edgy idol concept"},
    {"outfit": "a dreamy blue floral strap dress", "angle": "Full body shot, garden background, soft and feminine look"},
    {"outfit": "a simple white rib-knit bodycon midi dress", "angle": "Full body shot, minimalist grey studio, straight-on view"},
    {"outfit": "a sporty matching grey lounge set", "angle": "Full body shot, fitness studio background, natural and healthy look"},
    {"outfit": "an emerald green velvet cocktail dress", "angle": "Full body shot, cinematic night city background, glamorous vibe"}
]

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

# Z-Image LoRA Dataset Workflow (Vertical 832x1216)
workflow_template = {
  "12": { "inputs": { "unet_name": "z_image_turbo-Q5_K_M.gguf" }, "class_type": "UnetLoaderGGUF" },
  "13": { "inputs": { "clip_name": "qwen_3_4b_fp8_mixed.safetensors", "type": "qwen_image", "device": "default" }, "class_type": "CLIPLoader" },
  "15": { "inputs": { "vae_name": "ae.safetensors" }, "class_type": "VAELoader" },
  "11": { "inputs": { "width": 832, "height": 1216, "batch_size": 1 }, "class_type": "EmptySD3LatentImage" },
  "18": { "inputs": { "text": "", "clip": ["13", 0] }, "class_type": "CLIPTextEncode" },
  "10": { "inputs": { "text": NEGATIVE_PROMPT, "clip": ["13", 0] }, "class_type": "CLIPTextEncode" },
  "16": { "inputs": { "seed": 42, "steps": 6, "cfg": 1.0, "sampler_name": "euler", "scheduler": "simple", "denoise": 1.0, "model": ["12", 0], "positive": ["18", 0], "negative": ["10", 0], "latent_image": ["11", 0] }, "class_type": "KSampler" },
  "17": { "inputs": { "samples": ["16", 0], "vae": ["15", 0] }, "class_type": "VAEDecode" },
  "9": { "inputs": { "filename_prefix": "Dataset_V3", "images": ["17", 0] }, "class_type": "SaveImage" }
}

def generate_dataset_v3():
    print(f"🚀 [V3 Retry] 한국 아이돌 비주얼 단발 캐릭터 10장 생성 시작...")
    
    prompt_ids = []
    for i, scene in enumerate(SCENES):
        num = i + 1
        full_prompt = f"{scene['angle']} of {BASE_CHARACTER} Wearing {scene['outfit']}. High-end commercial photography, ultra high resolution, clean makeup, sharp features, perfect hair style, 8k, cinematic lighting."
        
        wf = json.loads(json.dumps(workflow_template))
        wf["18"]["inputs"]["text"] = full_prompt
        wf["16"]["inputs"]["seed"] = 9900 + i 
        wf["9"]["inputs"]["filename_prefix"] = f"V3_Sample_{num:02d}"
        
        try:
            res = queue_prompt(wf)
            print(f"📤 [{num}/{len(SCENES)}] 예약 완료 (ID: {res['prompt_id']})")
            prompt_ids.append((num, res['prompt_id']))
            time.sleep(1)
        except Exception as e:
            print(f"❌ [{num}/{len(SCENES)}] 실패: {e}")

    print("\n⏳ 렌더링 및 수거 중 (눈밑 화장 제거 버전)...")
    pending = prompt_ids.copy()
    while pending:
        for item in pending[:]:
            n, pid = item
            history = get_history(pid)
            if pid in history:
                print(f"✨ [{n}/{len(SCENES)}] 생성 완료!")
                images = history[pid]['outputs']['9']['images']
                for img in images:
                    src = os.path.join(OUTPUT_DIR, img['filename'])
                    dst = os.path.join(DOWNLOADS_DIR, f"lora_v3_clean_{n:02d}.png")
                    if os.path.exists(src):
                        shutil.move(src, dst)
                        print(f"🚚 [이동 완료] {dst}")
                pending.remove(item)
        time.sleep(5)

    print(f"\n🎉 V3 재성성 작업이 완료되었습니다! (폴더 확인 부탁드립니다)")
    print(f"📂 경로: {DOWNLOADS_DIR}")

if __name__ == "__main__":
    generate_dataset_v3()

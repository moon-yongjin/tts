import json
import urllib.request
import time
import os
import shutil

# [설정]
COMFYUI_URL = "http://127.0.0.1:8188"
OUTPUT_DIR = "/Users/a12/projects/tts/ComfyUI/output"
DOWNLOADS_DIR = "/Users/a12/Downloads/LoRA_Training_Dataset_V2_Local"

os.makedirs(DOWNLOADS_DIR, exist_ok=True)

# 새로운 캐릭터 설정 (단발머리/검은 드레스 여성 사진 기반)
BASE_CHARACTER = "A stunningly beautiful young Korean woman with stylish short messy black bob hair, clear pale skin, and large expressive eyes. She has a slim yet glamorous and curvy figure. Her facial features are sharp and sophisticated."

# 15개 프롬프트 구성 (다양한 각도와 의상, 단발머리 유지)
SCENES = [
    {"outfit": "a plunging V-neck black evening dress with silver sequin details", "angle": "Full body shot, surprised expression, holding a smartphone, indoor setting"},
    {"outfit": "a crisp white button-down shirt and slim fit blue jeans", "angle": "Full body shot, casual pose, natural daylight"},
    {"outfit": "an elegant red silk slip dress", "angle": "Full body shot, 45-degree angle, standing elegantly in a hotel hallway"},
    {"outfit": "a tailored black pant suit with no shirt underneath", "angle": "Full body shot, confident and edgy look, front view"},
    {"outfit": "a cozy oversized beige knit sweater", "angle": "Full body shot, sitting comfortably on a modern sofa"},
    {"outfit": "a casual white graphic t-shirt and wide-leg cargos", "angle": "Full body shot, street style photography, looking at camera"},
    {"outfit": "a classic black leather biker jacket over a white top", "angle": "Full body shot, cool pose, side view"},
    {"outfit": "a sleek athletic matching black yoga set", "angle": "Full body shot, stretching pose, gym background"},
    {"outfit": "a luxurious white faux fur coat over a black mini dress", "angle": "Full body shot, winter city street, walking"},
    {"outfit": "a professional grey pencil skirt and white silk blouse", "angle": "Full body shot, office setting, arms crossed"},
    {"outfit": "a traditional Korean Hanbok with a modern twist, pastel colors", "angle": "Full body shot, graceful pose, traditional garden"},
    {"outfit": "a floral summer strap dress", "angle": "Full body shot, sunny beach background, soft smile"},
    {"outfit": "a simple black high-neck tight sweater and denim pants", "angle": "Full body shot, minimalist studio, straight-on"},
    {"outfit": "a luxury silk bathrobe", "angle": "Full body shot, sitting by a large window, morning light"},
    {"outfit": "a dark emerald green velvet gown", "angle": "Full body shot, glamorous event lighting, looking back over shoulder"}
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
      "width": 832,
      "height": 1216,
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
      "text": "low quality, blurry, distorted, watermark, bad anatomy, text, cartoon, illustration, messy hair",
      "clip": ["13", 0]
    },
    "class_type": "CLIPTextEncode"
  },
  "16": {
    "inputs": {
      "seed": 42,
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
    "inputs": { "filename_prefix": "Dataset_V2", "images": ["17", 0] },
    "class_type": "SaveImage"
  }
}

def generate_dataset_local():
    print(f"🚀 [Local] 단발머리 캐릭터 데이터셋 생성 시작 (총 {len(SCENES)}장)...")
    
    prompt_ids = []
    for i, scene in enumerate(SCENES):
        num = i + 1
        full_prompt = f"{scene['angle']} of {BASE_CHARACTER} Wearing {scene['outfit']}. Highly detailed skin texture, photorealistic, 8k resolution, cinematic lighting, extremely consistent face."
        
        wf = json.loads(json.dumps(workflow_template))
        wf["18"]["inputs"]["text"] = full_prompt
        wf["16"]["inputs"]["seed"] = 8000 + i 
        wf["9"]["inputs"]["filename_prefix"] = f"Training_Sample_v2_{num:02d}"
        
        try:
            res = queue_prompt(wf)
            print(f"📤 [{num}/{len(SCENES)}] 로컬 큐 등록 완료 (ID: {res['prompt_id']})")
            prompt_ids.append((num, res['prompt_id']))
            time.sleep(1)
        except Exception as e:
            print(f"❌ [{num}/{len(SCENES)}] 등록 실패: {e}")

    print("\n⏳ 렌더링 및 파일 수거 대기 중...")
    pending = prompt_ids.copy()
    while pending:
        for item in pending[:]:
            n, pid = item
            history = get_history(pid)
            if pid in history:
                print(f"✨ [{n}/{len(SCENES)}] 로컬 생성 완료! 이동 중...")
                images = history[pid]['outputs']['9']['images']
                for img in images:
                    src = os.path.join(OUTPUT_DIR, img['filename'])
                    dst = os.path.join(DOWNLOADS_DIR, f"lora_v2_base_{n:02d}.png")
                    if os.path.exists(src):
                        shutil.move(src, dst)
                        print(f"🚚 [이동 완료] {dst}")
                pending.remove(item)
        time.sleep(5)

    print(f"\n🎉 단발머리 캐릭터 로컬 데이터셋 생성이 완료되었습니다!")
    print(f"📂 저장 폴더: {DOWNLOADS_DIR}")

if __name__ == "__main__":
    generate_dataset_local()

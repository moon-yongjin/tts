import json
import urllib.request
import time
import os
import shutil

# [설정]
COMFYUI_URL = "http://127.0.0.1:8188"
OUTPUT_DIR = "/Users/a12/projects/tts/ComfyUI/output"
DOWNLOADS_DIR = "/Users/a12/Downloads/LoRA_Training_Dataset_V1"

os.makedirs(DOWNLOADS_DIR, exist_ok=True)

# 캐릭터 기본 설정 (글래머러스/육감적 체형 강조)
BASE_CHARACTER = "A stunningly beautiful young Korean woman with a soft, round oval face, clear skin, and voluminous long black hair. She has a very voluptuous, full-figured, and glamorous hourglass body (large bust, slim but soft waist, very wide hips, and thick thighs). She is a plus-size model type with a healthy and curvy physique. Her expression is calm and sophisticated."

# 15개 프롬프트 구성 (전신샷 위주, 단정한 옷차림)
SCENES = [
    {"outfit": "an elegant traditional Korean Hanbok (pale pink Jeogori, beige Chima)", "angle": "Full body shot, front view, standing gracefully, showing her full-figured silhouette"},
    {"outfit": "a tight-fitting white turtleneck sweater and a knee-length dark blue pencil skirt, emphasizing her curvy hourglass figure", "angle": "Full body shot, 45-degree side view"},
    {"outfit": "a professional grey tailored business suit with a white silk blouse, well-fitted to her voluptuous shape", "angle": "Full body shot, confident posture, front view"},
    {"outfit": "a crisp white button-down shirt tucked into high-waisted beige slacks, highlighting her wide hips", "angle": "Full body shot, walking naturally, side view"},
    {"outfit": "a cozy beige cashmere cardigan over a white scoop-neck top and dark blue jeans, showing a soft and curvy build", "angle": "Full body shot, leaning against a clean wall"},
    {"outfit": "a simple but elegant black midi dress with long sleeves, tight-fitted to show her glamorous physique", "angle": "Full body shot, standing in a modern hallway"},
    {"outfit": "a luxury ivory trench coat tied at the waist, emphasizing her waist and hip curves", "angle": "Full body shot, front view, outdoor steps"},
    {"outfit": "a sophisticated floral silk midi dress with a modest neckline, showing her full-bodied elegance", "angle": "Full body shot, 45-degree angle, soft lighting"},
    {"outfit": "a white blazer over a black knitted dress, showcasing her powerful and curvy silhouette", "angle": "Full body shot, standing straight, professional look"},
    {"outfit": "a casual but neat grey hoodie and well-fitted flare yoga pants, showing her thick and healthy figure", "angle": "Full body shot, athletic yet feminine pose"},
    {"outfit": "a light blue denim shirt tucked into a white pleated skirt, emphasizing her full figure", "angle": "Full body shot, front view, bright daylight"},
    {"outfit": "a premium camel wool coat over a black turtleneck and slacks, solid and curvy build", "angle": "Full body shot, walking towards camera, winter setting"},
    {"outfit": "a modest white sleeveless summer dress with a straw hat, soft and voluminous look", "angle": "Full body shot, back-lit by sun, 45-degree view"},
    {"outfit": "a stylish check-patterned blazer and matching trousers, tailored for a glamorous body type", "angle": "Full body shot, sitting elegantly on a chair"},
    {"outfit": "a simple white t-shirt and wide-leg denim pants, highlighting a healthy and curvy profile", "angle": "Full body shot, relaxed front view"}
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
      "text": "slim, skinny, thin, lanky, underweight, boney, low quality, blurry, distorted, watermark, bad anatomy, text, cartoon, illustration, messy hair",
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
    "inputs": { "filename_prefix": "Dataset", "images": ["17", 0] },
    "class_type": "SaveImage"
  }
}

def generate_dataset():
    print(f"🚀 LoRA 캐릭터 기초 데이터셋 생성 시작 (총 {len(SCENES)}장)...")
    
    prompt_ids = []
    for i, scene in enumerate(SCENES):
        num = i + 1
        # 배경은 깔끔한 실내/가정 혹은 화이트 스튜디오로 믹스 (현장성 확보)
        full_prompt = f"{scene['angle']} of {BASE_CHARACTER} Wearing {scene['outfit']}. Highly detailed skin texture, photorealistic, 8k resolution, cinematic lighting, soft shadows, extremely consistent face."
        
        wf = json.loads(json.dumps(workflow_template))
        wf["18"]["inputs"]["text"] = full_prompt
        wf["16"]["inputs"]["seed"] = 1234 + i 
        wf["9"]["inputs"]["filename_prefix"] = f"Training_Sample_{num:02d}"
        
        try:
            res = queue_prompt(wf)
            print(f"📤 [{num}/{len(SCENES)}] 큐 등록 완료 (ID: {res['prompt_id']})")
            prompt_ids.append((num, res['prompt_id']))
            time.sleep(1)
        except Exception as e:
            print(f"❌ [{num}/{len(SCENES)}] 실패: {e}")

    # 수거 루프
    print("\n⏳ 생성된 파일 수거 대기 중...")
    pending = prompt_ids.copy()
    while pending:
        for item in pending[:]:
            n, pid = item
            history = get_history(pid)
            if pid in history:
                print(f"✨ [{n}/{len(SCENES)}] 생성 완료! 이동 중...")
                images = history[pid]['outputs']['9']['images']
                for img in images:
                    src = os.path.join(OUTPUT_DIR, img['filename'])
                    dst = os.path.join(DOWNLOADS_DIR, f"lora_base_{n:02d}.png")
                    if os.path.exists(src):
                        shutil.move(src, dst)
                        print(f"🚚 [이동] {dst}")
                pending.remove(item)
        time.sleep(5)

    print(f"\n🎉 15장의 고퀄리티 기초 이미지 생성이 완료되었습니다!")
    print(f"📂 결과 폴더: {DOWNLOADS_DIR}")

if __name__ == "__main__":
    generate_dataset()

import json
import urllib.request
import time
import os
import shutil

# [설정]
COMFYUI_URL = "http://127.0.0.1:8188"
OUTPUT_DIR = "/Users/a12/projects/tts/ComfyUI/output"
DOWNLOADS_DIR = "/Users/a12/Downloads/Shabby_Man_Test"

os.makedirs(DOWNLOADS_DIR, exist_ok=True)

# 프롬프트: 60대 괴짜 자산가 (허름한 옷을 입었지만 눈빛은 살아있는)
PROMPT_TEXT = "Full length shot of a sophisticated 60-year-old Korean man with an enigmatic smile. He has clean-shaven or well-groomed grey facial hair, wise eyes, wearing a comfortable but very old and faded olive work jacket and a vintage cap. He is sitting on a simple wooden bench in a quiet park, looking relaxed and wealthy despite his old clothes. High-end photography, cinematic lighting, hyper-realistic, 8k, bokeh background, masterpiece."
NEGATIVE_PROMPT = "tragic, crying, begging, dirty face, messy beard, low quality, blurry, watermark, text, cartoon, illustration"

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

workflow_template = {
  "12": { "inputs": { "unet_name": "z_image_turbo-Q5_K_M.gguf" }, "class_type": "UnetLoaderGGUF" },
  "13": { "inputs": { "clip_name": "qwen_3_4b_fp8_mixed.safetensors", "type": "qwen_image", "device": "default" }, "class_type": "CLIPLoader" },
  "15": { "inputs": { "vae_name": "ae.safetensors" }, "class_type": "VAELoader" },
  "11": { "inputs": { "width": 832, "height": 1216, "batch_size": 1 }, "class_type": "EmptySD3LatentImage" },
  "18": { "inputs": { "text": PROMPT_TEXT, "clip": ["13", 0] }, "class_type": "CLIPTextEncode" },
  "10": { "inputs": { "text": NEGATIVE_PROMPT, "clip": ["13", 0] }, "class_type": "CLIPTextEncode" },
  "16": { "inputs": { "seed": 7777, "steps": 6, "cfg": 1.0, "sampler_name": "euler", "scheduler": "simple", "denoise": 1.0, "model": ["12", 0], "positive": ["18", 0], "negative": ["10", 0], "latent_image": ["11", 0] }, "class_type": "KSampler" },
  "17": { "inputs": { "samples": ["16", 0], "vae": ["15", 0] }, "class_type": "VAEDecode" },
  "9": { "inputs": { "filename_prefix": "Shabby_Man", "images": ["17", 0] }, "class_type": "SaveImage" }
}

def generate_batch(count=5):
    print(f"🚀 [로컬 테스트] 60대 허름한 아저씨 이미지 {count}장 생성 시작...")
    prompt_ids = []
    
    for i in range(count):
        num = i + 1
        wf = json.loads(json.dumps(workflow_template))
        wf["16"]["inputs"]["seed"] = 7777 + i # 각기 다른 시드
        wf["9"]["inputs"]["filename_prefix"] = f"Shabby_Man_{num:02d}"
        
        try:
            res = queue_prompt(wf)
            print(f"📤 [{num}/{count}] 예약 완료 (ID: {res['prompt_id']})")
            prompt_ids.append((num, res['prompt_id']))
            time.sleep(1)
        except Exception as e:
            print(f"❌ [{num}/{count}] 실패: {e}")

    print("\n⏳ 렌더링 및 수거 중...")
    pending = prompt_ids.copy()
    while pending:
        for item in pending[:]:
            n, pid = item
            history = get_history(pid)
            if pid in history:
                print(f"✨ [{n}/{count}] 생성 완료!")
                images = history[pid]['outputs']['9']['images']
                for img in images:
                    src = os.path.join(OUTPUT_DIR, img['filename'])
                    dst = os.path.join(DOWNLOADS_DIR, f"eccentric_master_{n:02d}.png")
                    if os.path.exists(src):
                        shutil.move(src, dst)
                        print(f"🚚 [이동 완료] {dst}")
                pending.remove(item)
        time.sleep(5)

    print(f"\n🎉 총 {count}장의 생성이 완료되었습니다!")
    print(f"📂 경로: {DOWNLOADS_DIR}")

if __name__ == "__main__":
    generate_batch(5)

import json
import urllib.request
import time
import os
import shutil
from pathlib import Path

# [설정]
COMFYUI_URL = "http://127.0.0.1:8188"
OUTPUT_DIR = "/Users/a12/projects/tts/ComfyUI/output"
DOWNLOADS_DIR = "/Users/a12/Downloads/Local_ZImage_Scenes"
PROMPTS_FILE = "/Users/a12/projects/tts/watercolor_prompts.json"

os.makedirs(DOWNLOADS_DIR, exist_ok=True)

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

# Z-Image Turbo 640x640 (1:1) 워크플로우 템플릿
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
      "width": 640, # 1:1 고해상도
      "height": 640,
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
      "steps": 6,          # 퀄리티를 위해 6단계 설정
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
    "inputs": { "filename_prefix": "ZImage", "images": ["17", 0] },
    "class_type": "SaveImage"
  }
}

def run_local_batch():
    if not os.path.exists(PROMPTS_FILE):
        print(f"❌ 프롬프트 파일이 없습니다: {PROMPTS_FILE}")
        return

    with open(PROMPTS_FILE, "r", encoding="utf-8") as f:
        scenes = json.load(f)

    print(f"🚀 총 {len(scenes)}장의 로컬 Z-이미지 [래피드 큐] 연사를 시작합니다.")
    
    prompt_ids = []
    for i, scene in enumerate(scenes):
        scene_num = i + 1
        p_text = scene.get("visual_prompt") or scene.get("prompt")
        
        wf = json.loads(json.dumps(workflow_template))
        wf["18"]["inputs"]["text"] = p_text
        wf["16"]["inputs"]["seed"] = int(time.time()) + i
        wf["9"]["inputs"]["filename_prefix"] = f"Z_Scene_{scene_num:02d}"
        
        print(f"📤 [장면 {scene_num:02d}] 큐에 던지는 중...")
        try:
            res = queue_prompt(wf)
            prompt_ids.append((scene_num, res['prompt_id']))
            time.sleep(0.5) # 컨피 UI가 꼬이지 않게 아주 짧은 간격
        except Exception as e:
            print(f"❌ 장면 {scene_num} 큐 등록 실패: {e}")

    print(f"\n✅ {len(prompt_ids)}개 장면이 모두 컨피 큐에 등록되었습니다!")
    print(f"📸 지금부터 로컬 ComfyUI가 화면 뒤에서 열심히 그림을 그립니다.")
    print(f"📂 파일은 생성이 끝나는 대로 {DOWNLOADS_DIR} 로 자동 이동됩니다.")

    # 백그라운드에서 파일 수거 대기
    pending = prompt_ids.copy()
    while pending:
        for item in pending[:]:
            s_num, p_id = item
            history = get_history(p_id)
            if p_id in history:
                print(f"✨ [장면 {s_num:02d}] 생성 완료! 수거 중...")
                outputs = history[p_id]['outputs']['9']['images']
                for img in outputs:
                    file_name = img['filename']
                    src = os.path.join(OUTPUT_DIR, file_name)
                    dst = os.path.join(DOWNLOADS_DIR, file_name)
                    if os.path.exists(src):
                        shutil.move(src, dst)
                        print(f"🚚 이동 완료: {file_name}")
                pending.remove(item)
        time.sleep(3)

    print(f"\n🎉 모든 {len(scenes)}개 장면의 수거가 완료되었습니다!")

if __name__ == "__main__":
    run_local_batch()

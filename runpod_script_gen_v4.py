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
      "seed": 101,
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
    "inputs": { "filename_prefix": "Script_V4", "images": ["17", 0] },
    "class_type": "SaveImage"
  }
}

# --- 핵심: 모든 캐릭터 공통 '볼륨 바디' 앵커 ---
BODY_ANCHOR = "extremely large breasts, very voluptuous and curvy full figure, not skinny, healthy glamorous body, sexy and provocative revealing outfit"

# --- 캐릭터 앵커 정의 (V4) ---

# 1. 시어머니 (MIL)
MIL_ANCHOR = f"A beautiful Korean grandmother in her 60s, salt and pepper hair, elegant but aged face, {BODY_ANCHOR}, wearing a tight-fitting thin sexy knit sweater"

# 2. 첫째 며느리 (1st DIL)
DIL1_ANCHOR = f"A beautiful Korean woman in her late 30s, sharp and cold features, arrogant face, {BODY_ANCHOR}, wearing a very low-cut provocative designer dress, heavy makeup"

# 3. 둘째 며느리 (2nd DIL)
DIL2_ANCHOR = f"A beautiful young Korean woman in her late 20s, kind and bright face, {BODY_ANCHOR}, wearing a thin and revealing sexy casual outfit, natural beauty"

# --- 장면 구성 ---
SCENES = [
    {"char": MIL_ANCHOR, "desc": "Mother worrying", "prompt": "sad expression, holding phone in kitchen, traditional mood"},
    {"char": DIL1_ANCHOR, "desc": "1st DIL annoying", "prompt": "annoyed face, talking on phone in a luxury car"},
    {"char": MIL_ANCHOR, "desc": "Mother hurt", "prompt": "crying eyes, heartbroken, dim indoor light"},
    {"char": DIL2_ANCHOR, "desc": "2nd DIL kind", "prompt": "bright angelic expression, talking on phone in a sunny kitchen"},
    {"char": "A scene with both: " + MIL_ANCHOR + " and " + DIL2_ANCHOR, "desc": "Bank visit", "prompt": "walking to a bank, DIL2 helping MIL, both with voluptuous figures, sunny afternoon street"},
    {"char": MIL_ANCHOR, "desc": "Lottery Win", "prompt": "holding a lottery ticket, gasping with surprise, sitting at a bank counter"},
    {"char": DIL1_ANCHOR, "desc": "1st DIL regret", "prompt": "desperate expression, looking at phone in shock, wearing messy but revealing clothes"},
    {"char": MIL_ANCHOR, "desc": "Mother Resolution", "prompt": "dignified powerful gaze, cold satisfied smile, urban sunset background"}
]

def run_script_v4():
    print(f"🚀 [RunPod] 대본 v4 (몸매/복장 극대화) 시작합니다.")
    for i, scene in enumerate(SCENES):
        idx = i + 1
        full_prompt = f"{scene['char']}, {scene['prompt']}, masterpiece, high quality, photorealistic, 8k"
        wf = json.loads(json.dumps(workflow_template))
        wf["18"]["inputs"]["text"] = full_prompt
        wf["16"]["inputs"]["seed"] = int(time.time() * 1000) + 40000 + i
        wf["9"]["inputs"]["filename_prefix"] = f"Script_V4_Scene_{idx:02d}"
        print(f"📤 [{idx:02d}/08] 등록 중: {scene['desc']}")
        queue_prompt(wf)
        time.sleep(0.5)
    print(f"\n✅ 8개 장면이 등록되었습니다. http://localhost:8181 확인!")

if __name__ == "__main__":
    run_script_v4()

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
    "inputs": { "filename_prefix": "Script_Scene", "images": ["17", 0] },
    "class_type": "SaveImage"
  }
}

# 고정 캐릭터 앵커 (시어머니 니트 버전)
CHARACTER_ANCHOR = "A beautiful Korean woman in her late 50s to early 60s, extremely plain and modest natural grandmotherly face, salt and pepper hair in a simple natural old-fashioned style, very large breasts, extremely voluptuous and curvy full figure, not skinny, wearing a tight-fitting thin sexy knit sweater, masterpiece, high quality, photorealistic, 8k"

# 대본 기반 장면 구성
SCENES = [
    {
        "desc": "Calling the first daughter-in-law, looking worried and humble",
        "prompt": "sad and worried expression, holding an old smartphone to her ear, standing in a humble traditional Korean house kitchen, soft morning light, emotional atmosphere"
    },
    {
        "desc": "Listening to the cold response, looking deeply hurt and sad",
        "prompt": "teary eyes, looking down with a deeply hurt and sorrowful expression, holding phone, humble living room background, dim indoor lighting"
    },
    {
        "desc": "Calling the second daughter-in-law, feeling a bit relieved",
        "prompt": "slight hopeful smile, talking on the phone with a warm expression, sitting on a wooden floor of a traditional house (Hanok), soft sunlight"
    },
    {
        "desc": "Going to the bank with the second daughter-in-law, looking calm",
        "prompt": "walking near a modern bank building, looking calm and peaceful, elegant posture, bright outdoor daylight, urban street background"
    },
    {
        "desc": "At the bank counter, finding out about the 2 billion won win",
        "prompt": "sitting at a high-end bank counter, looking shocked but dignified, holding a small lottery ticket, bright professional lighting, bank interior decoration"
    },
    {
        "desc": "Calling the first daughter-in-law again, looking firm and determined",
        "prompt": "firm and cold expression, talking on the phone with a sophisticated and dignified aura, refined posture, expensive-looking indoor background"
    },
    {
        "desc": "Final firm resolution, looking away with dignity",
        "prompt": "walking away from the camera, looking over her shoulder with a sharp and firm gaze, satisfied and dignified smile, urban sunset background, cinematic lighting"
    }
]

def run_script_generation():
    print(f"🚀 [RunPod] 대본(대본.txt) 기반 장면 생성을 시작합니다.")
    print(f"🔗 Target: {COMFYUI_URL}")
    print(f"👤 Character: MIL (Modest Face / Sexy Knit)")
    
    for i, scene in enumerate(SCENES):
        idx = i + 1
        full_prompt = f"{CHARACTER_ANCHOR}, {scene['prompt']}"
        
        wf = json.loads(json.dumps(workflow_template))
        wf["18"]["inputs"]["text"] = full_prompt
        wf["16"]["inputs"]["seed"] = int(time.time() * 1000) + 20000 + i
        wf["9"]["inputs"]["filename_prefix"] = f"Script_MIL_Scene_{idx:02d}"
        
        print(f"📤 [{idx:02d}/{len(SCENES)}] 장먼 등록 중: {scene['desc']}")
        try:
            res = queue_prompt(wf)
            time.sleep(0.5)
        except Exception as e:
            print(f"❌ [{idx:02d}] 큐 등록 실패: {e}")

    print(f"\n✅ 대본 기반 모든 {len(SCENES)}개 장면이 런팟 큐에 등록되었습니다!")
    print(f"🌐 http://localhost:8181 에서 확인해 보세요.")

if __name__ == "__main__":
    run_script_generation()

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
    "inputs": { "filename_prefix": "Script_V2", "images": ["17", 0] },
    "class_type": "SaveImage"
  }
}

# --- 캐릭터 앵커 정의 ---
# 1. 시어머니 (MIL - 니트 버전)
MIL_ANCHOR = "A beautiful Korean woman in her late 50s to early 60s, elegant and natural grandmotherly image, salt and pepper or dark hair in a simple natural style, very large breasts, extremely voluptuous and curvy full figure, wearing a thin sexy knit sweater"

# 2. 첫째 며느리 (1st DIL - 차갑고 세련됨, 욕심 많아 보임)
DIL1_ANCHOR = "A beautiful Korean woman in her late 30s, sharp and cold features, arrogant and chic face, elegant but mean-spirited look, expensive designer clothes, heavy makeup, luxurious jewelry, sophisticated sharp bob hair style, slender but glamorous body"

# 3. 둘째 며느리 (2nd DIL - 착하고 밝음, 수수한 미인)
DIL2_ANCHOR = "A beautiful Korean woman in her early 30s, warm and kind features, bright and friendly face, pure and natural beauty, soft flowing long hair, simple but neat casual clothing, warm and caring aura, healthy and charming look"

# --- 대본 기반 장면 구성 (버전 2) ---
SCENES = [
    {
        "char": MIL_ANCHOR,
        "desc": "Mother calling 1st DIL, looking worried",
        "prompt": "sad and worried expression, holding phone to ear, traditional house kitchen background, morning light"
    },
    {
        "char": DIL1_ANCHOR,
        "desc": "1st DIL responding coldly and irritably",
        "prompt": "annoyed and irritable expression, talking on a smartphone, looking at a mirror in a luxurious dressing room, holding a credit card, cold and arrogant gaze"
    },
    {
        "char": MIL_ANCHOR,
        "desc": "Mother deeply hurt by 1st DIL's words",
        "prompt": "teary eyes, looking down with a deeply hurt expression, holding phone in a dim living room, feeling lonely"
    },
    {
        "char": DIL2_ANCHOR,
        "desc": "2nd DIL answering with a bright smile",
        "prompt": "bright and happy smile, talking on the phone with a warm expression, sunny park background, looking very kind and helpful"
    },
    {
        "char": "A scene with both: " + MIL_ANCHOR + " and " + DIL2_ANCHOR,
        "desc": "Mother and 2nd DIL together at the bank",
        "prompt": "walking together near a modern bank building, 2nd DIL is kindly supporting MIL's arm, both looking peaceful and friendly, bright daylight"
    },
    {
        "char": MIL_ANCHOR,
        "desc": "Mother finding out about lottery win at the bank counter",
        "prompt": "sitting at a bank counter, holding a lottery ticket, looking shocked but dignified, high-end bank interior background"
    },
    {
        "char": DIL1_ANCHOR,
        "desc": "1st DIL shocked and regretful after hearing news",
        "prompt": "pale and shocked face, dropping a luxury handbag, looking desperate and regretful, urban apartment interior background, dramatic shadows"
    },
    {
        "char": MIL_ANCHOR,
        "desc": "Final firm resolution of the Mother",
        "prompt": "dignified and sharp cold expression, looking at the camera with a satisfied smile, urban sunset background, cinematic lighting"
    }
]

def run_script_v2():
    print(f"🚀 [RunPod] 대본 v2 (다중 캐릭터) 장면 생성을 시작합니다.")
    
    for i, scene in enumerate(SCENES):
        idx = i + 1
        full_prompt = f"{scene['char']}, {scene['prompt']}, masterpiece, high quality, photorealistic, 8k"
        
        wf = json.loads(json.dumps(workflow_template))
        wf["18"]["inputs"]["text"] = full_prompt
        wf["16"]["inputs"]["seed"] = int(time.time() * 1000) + 25000 + i
        wf["9"]["inputs"]["filename_prefix"] = f"Script_V2_Scene_{idx:02d}"
        
        print(f"📤 [{idx:02d}/{len(SCENES)}] 등록 중: {scene['desc']}")
        try:
            res = queue_prompt(wf)
            time.sleep(0.5)
        except Exception as e:
            print(f"❌ [{idx:02d}] 큐 등록 실패: {e}")

    print(f"\n✅ 다중 캐릭터 기반 모든 장먼이 런팟 큐에 등록되었습니다!")
    print(f"🌐 http://localhost:8181 에서 확인해 보세요.")

if __name__ == "__main__":
    run_script_v2()

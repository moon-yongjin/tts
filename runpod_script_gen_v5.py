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
  "10": { "inputs": { "text": "foreigners, anime, cartoon, illustration, drawing, text, watermark, low quality, blurry, distorted, deformed, extra fingers, malformed hands, fused fingers, bad anatomy", "clip": ["13", 0] }, "class_type": "CLIPTextEncode" },
  "16": { "inputs": { "seed": 101, "steps": 6, "cfg": 1.0, "sampler_name": "euler", "scheduler": "simple", "denoise": 1.0, "model": ["12", 0], "positive": ["18", 0], "negative": ["10", 0], "latent_image": ["11", 0] }, "class_type": "KSampler" },
  "17": { "inputs": { "samples": ["16", 0], "vae": ["15", 0] }, "class_type": "VAEDecode" },
  "9": { "inputs": { "filename_prefix": "Script_V5", "images": ["17", 0] }, "class_type": "SaveImage" }
}

# --- 핵심 캐릭터 앵커 조합 (V5) ---
COMMON_BODY = "extremely large breasts, very voluptuous and curvy full figure, not skinny, healthy glamorous body"

# 1. 첫째 며느리 (1st DIL): 40대 도시적, 보브컷, 차갑고 오만한 미인
DIL1_ANCHOR = f"A beautiful Korean woman in her late 30s to early 40s, sharp and cold features, arrogant face, (medium bob hair style), sophisticated urban image, {COMMON_BODY}, wearing provocative high-end urban clothing with deep cleavage"

# 2. 둘째 며느리 (2nd DIL): 30대 후반, 긴 머리, 착하고 청순하지만 야한 몸
DIL2_ANCHOR = f"A beautiful Korean woman in her early 30s, long flowing dark hair, elegant and natural kind features, bright friendly face, {COMMON_BODY}, wearing thin and tight-fitting sexy casual clothing"

# 3. 시어머니 (MIL): 수수한 할머니 얼굴, 수수한 머리, 하지만 야한 몸(니트)
MIL_ANCHOR = f"A beautiful Korean woman in her early 60s, (extremely plain and modest grandmotherly face), salt and pepper hair in a simple natural old-fashioned style, humble appearance, {COMMON_BODY}, wearing a tight-fitting thin sexy knit sweater"

# --- 대본 기반 장면 구성 (V5) ---
SCENES = [
    {"char": MIL_ANCHOR, "desc": "Mother calling 1st DIL, worrying", "prompt": "sad expression, holding phone in a humble kitchen, morning light"},
    {"char": DIL1_ANCHOR, "desc": "1st DIL being cold and mean", "prompt": "annoyed and cold expression, talking on a smartphone, luxurious dressing room background, looking arrogant"},
    {"char": MIL_ANCHOR, "desc": "Mother feeling hurt", "prompt": "teary eyes, heartbroken, sitting alone in a dim traditional living room"},
    {"char": DIL2_ANCHOR, "desc": "2nd DIL being kind and warm", "prompt": "bright angelic smile, talking on phone, sunny park background, looking very helpful"},
    {"char": f"A scene with both: {MIL_ANCHOR} and {DIL2_ANCHOR}", "desc": "Bank visit together", "prompt": "walking to a bank, DIL2 supporting MIL's arm, both characters showing voluptuous figures, sunny urban street"},
    {"char": MIL_ANCHOR, "desc": "Shocked at Lottery Win", "prompt": "holding a lottery ticket, gasping with surprise, sitting at a high-end bank counter, dramatic lighting"},
    {"char": DIL1_ANCHOR, "desc": "1st DIL's total regret", "prompt": "desperate and shocked expression, dropping phone, messy but sexy clothes, dim interior light"},
    {"char": MIL_ANCHOR, "desc": "Resolution & Satisfaction", "prompt": "dignified powerful gaze, cold satisfied smile, urban sunset background, cinematic lighting"}
]

def run_script_v5():
    print(f"🚀 [RunPod] 대본 V5 (캐릭터 조합 완성판) 시작합니다.")
    for i, scene in enumerate(SCENES):
        idx = i + 1
        full_prompt = f"{scene['char']}, {scene['prompt']}, masterpiece, photorealistic, 8k"
        wf = json.loads(json.dumps(workflow_template))
        wf["18"]["inputs"]["text"] = full_prompt
        wf["16"]["inputs"]["seed"] = int(time.time() * 1000) + 50000 + i
        wf["9"]["inputs"]["filename_prefix"] = f"Script_V5_Scene_{idx:02d}"
        print(f"📤 [{idx:02d}/08] 등록 중: {scene['desc']}")
        queue_prompt(wf)
        time.sleep(0.5)
    print(f"✅ 모든 V5 장면 등록 완료. http://localhost:8181")

if __name__ == "__main__":
    run_script_v5()

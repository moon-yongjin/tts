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
  "9": { "inputs": { "filename_prefix": "Script_V6", "images": ["17", 0] }, "class_type": "SaveImage" }
}

# --- 캐릭터 앵커 조합 (V6 - 사용자 요청 반영) ---

# 1. 첫째 며느리 (DIL1): 동탄미시 스타일, 가슴이 훅 패인 옷, 오만한 미인
DIL1_ANCHOR = "A stunningly beautiful Korean woman in her late 30s, sharp cold features, arrogant face, (medium bob hair style), wearing a (Dongtan-missy style sexy outfit) with an (extremely deep plunging neckline), revealing deep cleavage, extremely large breasts, very voluptuous and curvy body, healthy glamorous and full figure"

# 2. 둘째 며느리 (DIL2): 수수하고 청순한 얼굴, 하지만 엄청난 글래머/풍만함
DIL2_ANCHOR = "A very beautiful Korean woman in her late 20s, (extremely pure and modest innocent face), kind and bright angelic smile, natural long hair, (but having an extremely glamorous and voluminous body), very large breasts, curvy full figure, wearing a thin and skin-tight sexy casual outfit"

# 시어머니 (MIL) - V6에서는 시어머니 씬은 제외하고 며느리들만 다시 뽑음
MIL_ANCHOR = "A beautiful Korean grandmother in her 60s, plain modest face, salt and pepper hair, very large breasts, voluptuous body, wearing a sexy knit sweater"

# --- 대본 기반 장면 구성 (V6 - 며느리들 중심 재추출) ---
SCENES = [
    {
        "char": DIL1_ANCHOR,
        "desc": "1st DIL being cold and mean on the phone",
        "prompt": "annoyed and cold expression, talking on a smartphone, sitting in a luxury car, showing off deep cleavage, arrogant gaze"
    },
    {
        "char": DIL2_ANCHOR,
        "desc": "2nd DIL being kind and warm on the phone",
        "prompt": "bright pure smile, talking on phone with a warm expression, sunny house background, angelic look but showing a very glamorous figure"
    },
    {
        "char": f"A scene with both: {MIL_ANCHOR} and {DIL2_ANCHOR}",
        "desc": "Bank visit: MIL supported by 2nd DIL",
        "prompt": "walking to a bank, 2nd DIL (pure face/glamorous body) is kindly supporting MIL's arm, both characters showing voluptuous figures, sunny urban street"
    },
    {
        "char": DIL1_ANCHOR,
        "desc": "1st DIL's shock and desperation after hearing news",
        "prompt": "desperate and shocked expression, pale face, dropping a luxury handbag, messy bob hair, wearing the sexy deep neckline outfit, looking regretful"
    }
]

def run_script_v6():
    print(f"🚀 [RunPod] 대본 V6 (며느리 캐릭터 정교화) 시작합니다.")
    print(f"👗 DIL1: 동탄미시 & 푹 파인 옷 / DIL2: 청순 페이스 & 글래머 바디")
    for i, scene in enumerate(SCENES):
        idx = i + 1
        full_prompt = f"{scene['char']}, {scene['prompt']}, masterpiece, photorealistic, 8k"
        wf = json.loads(json.dumps(workflow_template))
        wf["18"]["inputs"]["text"] = full_prompt
        # 시드 겹치지 않게 오프셋 부여
        wf["16"]["inputs"]["seed"] = int(time.time() * 1000) + 60000 + i
        wf["9"]["inputs"]["filename_prefix"] = f"Script_V6_Scene_{idx:02d}"
        print(f"📤 [{idx:02d}/04] 등록 중: {scene['desc']}")
        queue_prompt(wf)
        time.sleep(0.5)
    print(f"✅ V6 며느리 장면들 등록 완료. http://localhost:8181")

if __name__ == "__main__":
    run_script_v6()

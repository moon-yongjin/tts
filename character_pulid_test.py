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

# PuLID-Flux 워크플로우 템플릿
workflow_template = {
  "12": { "inputs": { "unet_name": "z_image_turbo-Q5_K_M.gguf" }, "class_type": "UnetLoaderGGUF" },
  "13": { "inputs": { "clip_name": "qwen_3_4b_fp8_mixed.safetensors", "type": "qwen_image", "device": "default" }, "class_type": "CLIPLoader" },
  "15": { "inputs": { "vae_name": "ae.safetensors" }, "class_type": "VAELoader" },
  "11": { "inputs": { "width": 1024, "height": 1024, "batch_size": 1 }, "class_type": "EmptySD3LatentImage" },
  
  # [PuLID 로더 노드]
  "51": { "inputs": {}, "class_type": "PulidFluxEvaClipLoader" },
  "53": { "inputs": { "provider": "CUDA" }, "class_type": "PulidFluxInsightFaceLoader" },
  "45": { "inputs": { "pulid_file": "pulid_flux_v0.9.1.safetensors" }, "class_type": "PulidFluxModelLoader" },
  "54": { "inputs": { "image": "DIL2_ref.png", "upload": "image" }, "class_type": "LoadImage" },
  
  # [PuLID 메인 어댑터]
  "62": { 
    "inputs": { 
        "weight": 1.0, 
        "start_at": 0.0, 
        "end_at": 1.0, 
        "model": ["12", 0], 
        "pulid_flux": ["45", 0], 
        "eva_clip": ["51", 0], 
        "face_analysis": ["53", 0], 
        "image": ["54", 0] 
    }, 
    "class_type": "PulidFlux" 
  },
  
  "18": { "inputs": { "text": "", "clip": ["13", 0] }, "class_type": "CLIPTextEncode" },
  "10": { "inputs": { "text": "man, male, boy, facial hair, foreigners, anime, cartoon, illustration, drawing, text, watermark, low quality, blurry, distorted, deformed, extra fingers, malformed hands, fused fingers, bad anatomy", "clip": ["13", 0] }, "class_type": "CLIPTextEncode" },
  
  "16": { 
    "inputs": { 
        "seed": 101, "steps": 6, "cfg": 1.0, "sampler_name": "euler", "scheduler": "simple", "denoise": 1.0, 
        "model": ["62", 0], # PuLID에서 나온 모델 사용
        "positive": ["18", 0], "negative": ["10", 0], "latent_image": ["11", 0] 
    }, 
    "class_type": "KSampler" 
  },
  
  "17": { "inputs": { "samples": ["16", 0], "vae": ["15", 0] }, "class_type": "VAEDecode" },
  "9": { "inputs": { "filename_prefix": "PuLID_Test_DIL2", "images": ["17", 0] }, "class_type": "SaveImage" }
}

def run_test():
    prompt = "c2_dil2, young Korean woman, extremely pure and kind face, innocent friendly expression, natural long black hair, chubby healthy figure, voluptuous body, wearing a simple white dress, indoor cozy living room, high quality, 8k"
    
    wf = json.loads(json.dumps(workflow_template))
    wf["18"]["inputs"]["text"] = prompt
    wf["16"]["inputs"]["seed"] = int(time.time() * 1000)
    
    print(f"🚀 [RunPod] PuLID-Flux 얼굴 고정 테스트 시작...")
    try:
        res = queue_prompt(wf)
        print(f"✅ 테스트 큐 등록 완료: {res['prompt_id']}")
    except Exception as e:
        print(f"❌ 실패: {e}")

if __name__ == "__main__":
    run_test()

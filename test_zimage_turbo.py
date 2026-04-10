import json
import urllib.request
import urllib.parse
import os
import sys
import time

# [설정]
COMFY_URL = "http://127.0.0.1:8188"

def queue_prompt(prompt):
    p = {"prompt": prompt}
    data = json.dumps(p).encode('utf-8')
    req = urllib.request.Request(f"{COMFY_URL}/prompt", data=data)
    return json.loads(urllib.request.urlopen(req).read())

def get_history(prompt_id):
    with urllib.request.urlopen(f"{COMFY_URL}/history/{prompt_id}") as response:
        return json.loads(response.read())

def test_gen(user_prompt):
    print(f"🎨 Z-Image Turbo 생성 시도: {user_prompt}")
    
    # [최종 수정본] 스키마에서 확인한 정확한 포맷 적용
    # style 필드는 큰따옴표로 감싸진 형태가 유효값 ("\"Vintage Photo\"")
    prompt = {
      "32": { 
          "inputs": { 
              "landscape": False,
              "ratio": "3:2  (photo)", 
              "size": "medium (recommended)", 
              "batch_size": 1 
          }, 
          "class_type": "EmptyZImageLatentImage //ZImagePowerNodes"
      },
      "35": { 
          "inputs": { "unet_name": "z_image_turbo_bf16.safetensors", "weight_dtype": "default" }, 
          "class_type": "UNETLoader" 
      },
      "37": { 
          "inputs": { "vae_name": "ae.safetensors" }, 
          "class_type": "VAELoader" 
      },
      "44": { 
          "inputs": { "clip_name": "qwen_3_4b.safetensors", "type": "lumina2" }, 
          "class_type": "CLIPLoader" 
      },
      "42": { 
          "inputs": { 
              "clip": ["44", 0],
              "collection": "photo", 
              "text": user_prompt,              "style": "\"Vintage Photo\"",
          }, 
          "class_type": "StylePromptEncoder //ZImagePowerNodes"
      },
      "18": { 
          "inputs": { 
              "seed": int(time.time()), 
              "steps": 4, 
              "cfg": 1.0, 
              "sampler_name": "euler", 
              "scheduler": "normal", 
              "denoise": 1.0, 
              "model": ["35", 0], 
              "positive": ["42", 0], 
              "negative": ["42", 1], 
              "latent_input": ["32", 0] 
          }, 
          "class_type": "ZSamplerTurbo //ZImagePowerNodes"
      },
      "8": { 
          "inputs": { "samples": ["18", 0], "vae": ["37", 0] }, 
          "class_type": "VAEDecode" 
      },
      "31": { 
          "inputs": { 
              "images": ["8", 0],
              "filename_prefix": "ZImage/Test/ZI", 
              "civitai_compatible_metadata": True 
          }, 
          "class_type": "SaveImage //ZImagePowerNodes"
      }
    }
    
    try:
        res = queue_prompt(prompt)
        prompt_id = res['prompt_id']
        print(f"🚀 큐 등록 완료 (ID: {prompt_id})")
        
        start_time = time.time()
        while True:
            history = get_history(prompt_id)
            if prompt_id in history:
                print("✅ 생성 성공!")
                print(f"📂 출력 위치: /workspace/runpod-slim/ComfyUI/output/ZImage/Test/")
                break
            
            if time.time() - start_time > 120:
                print("⏳ 타임아웃: 생성이 너무 오래 걸립니다.")
                break
                
            time.sleep(2)
    except Exception as e:
        print(f"❌ 생성 실패: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    p = sys.argv[1] if len(sys.argv) > 1 else "A hyper-realistic cinematic photo of a futuristic neon city, 8k"
    test_gen(p)

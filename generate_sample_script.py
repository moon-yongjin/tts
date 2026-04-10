
import json
import urllib.request
import urllib.parse
import os
import sys
import time

# [설정]
COMFY_URL = "http://127.0.0.1:8188"

PROMPT_TEXT = "A cinematic shot of a 50-year-old wealthy Korean woman, handcuffed, being dragged by police officers, expression of cold fury, in the background a luxury penthouse living room engulfed in flames, a younger woman with a fake injury smiling forcefully, dramatic lighting, high quality, photorealistic, 8k, dark atmosphere, rain"
NEGATIVE_TEXT = "text, watermark, low quality, blurry, illustration, painting, cartoon"

def queue_prompt(prompt):
    p = {"prompt": prompt}
    data = json.dumps(p).encode('utf-8')
    req = urllib.request.Request(f"{COMFY_URL}/prompt", data=data)
    return json.loads(urllib.request.urlopen(req).read())

def get_history(prompt_id):
    with urllib.request.urlopen(f"{COMFY_URL}/history/{prompt_id}") as response:
        return json.loads(response.read())

def test_gen():
    print(f"🎨 Z-Image Turbo 샘플 생성 시작...")
    print(f"📜 프롬프트: {PROMPT_TEXT}")
    
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
              "text": PROMPT_TEXT, 
              "clip": ["44", 0]
          }, 
          "class_type": "CLIPTextEncode"
      },
      "43": { 
          "inputs": { 
              "text": NEGATIVE_TEXT, 
              "clip": ["44", 0]
          }, 
          "class_type": "CLIPTextEncode"
      },
      "18": { 
          "inputs": { 
              "seed": int(time.time()), 
              "steps": 6, 
              "cfg": 1.5, 
              "sampler_name": "euler", 
              "scheduler": "normal", 
              "denoise": 1.0, 
              "model": ["35", 0], 
              "positive": ["42", 0], 
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
              "filename_prefix": "ZImage/Sample/ZI_Sample", 
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
                # Get filename
                outputs = history[prompt_id]['outputs']
                for node_id in outputs:
                    for img in outputs[node_id].get('images', []):
                        print(f"📂 파일명: {img['filename']}")
                break
            
            if time.time() - start_time > 120:
                print("⏳ 타임아웃")
                break
                
            time.sleep(1)
    except Exception as e:
        print(f"❌ 생성 실패: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_gen()

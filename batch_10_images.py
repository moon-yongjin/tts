
import json
import urllib.request
import urllib.parse
import time
import sys

COMFY_URL = "http://127.0.0.1:8188"

# 10가지 다양한 프롬프트
PROMPTS = [
    "A wealthy Korean woman in handcuffs, dramatic lighting, cinematic, 8k",
    "A luxury penthouse on fire, smoke and flames, photorealistic",
    "A young woman with fake tears, manipulative expression, dark atmosphere",
    "Police officers in a burning building, intense action scene",
    "A courtroom scene, judge and lawyers, Korean drama style",
    "A prison cell, cold and dark, dramatic shadows",
    "A hospital room, medical equipment, emotional scene",
    "A corporate office, glass windows, modern architecture",
    "A traditional Korean house, wooden interior, warm lighting",
    "A city street at night, neon lights, rain, cinematic"
]

def queue_prompt(prompt):
    p = {"prompt": prompt}
    data = json.dumps(p).encode('utf-8')
    req = urllib.request.Request(f"{COMFY_URL}/prompt", data=data)
    return json.loads(urllib.request.urlopen(req).read())

def get_history(prompt_id):
    with urllib.request.urlopen(f"{COMFY_URL}/history/{prompt_id}") as response:
        return json.loads(response.read())

def generate_image(prompt_text, seed):
    workflow = {
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
              "text": prompt_text, 
              "clip": ["44", 0]
          }, 
          "class_type": "CLIPTextEncode"
      },
      "43": { 
          "inputs": { 
              "text": "text, watermark, low quality, blurry", 
              "clip": ["44", 0]
          }, 
          "class_type": "CLIPTextEncode"
      },
      "18": { 
          "inputs": { 
              "seed": seed, 
              "steps": 6, 
              "cfg": 1.5, 
              "sampler_name": "euler", 
              "scheduler": "normal", 
              "denoise": 1.0, 
              "model": ["35", 0], 
              "positive": ["42", 0], 
              "negative": ["43", 0], 
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
              "filename_prefix": "Batch10/ZI_Batch", 
              "civitai_compatible_metadata": True 
          }, 
          "class_type": "SaveImage //ZImagePowerNodes"
      }
    }
    
    try:
        res = queue_prompt(workflow)
        prompt_id = res['prompt_id']
        
        # Wait for completion with timeout
        timeout = 120  # 2 minutes per image
        start = time.time()
        while True:
            if time.time() - start > timeout:
                print(f"  ⏱️ Timeout after {timeout}s")
                return False
            
            history = get_history(prompt_id)
            if prompt_id in history:
                print(f"  ✅ Done!")
                return True
            time.sleep(1)
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting 10-image batch generation...")
    start_time = time.time()
    
    for i, prompt in enumerate(PROMPTS):
        print(f"[{i+1}/10] Generating: {prompt[:50]}...")
        seed = int(time.time() * 1000) + i
        generate_image(prompt, seed)
    
    elapsed = time.time() - start_time
    print(f"\n✅ All done!")
    print(f"⏱️  Total time: {elapsed:.2f} seconds")
    print(f"📊 Average: {elapsed/10:.2f} sec/image")

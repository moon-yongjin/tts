
import json
import urllib.request
import time

# [설정]
COMFY_URL = "http://127.0.0.1:8188"

# 20개 프롬프트
PROMPTS = [
    "A wealthy Korean woman in handcuffs, dramatic lighting, photorealistic, 8k",
    "A luxury penthouse on fire, smoke and flames, photorealistic, cinematic",
    "A young woman with fake tears, manipulative expression, dramatic scene",
    "Police officers in a burning building, intense action, photorealistic",
    "A courtroom scene, judge and lawyers, Korean drama style, cinematic",
    "A prison cell, cold and dark, dramatic shadows, photorealistic",
    "A hospital room, medical equipment, emotional scene, cinematic lighting",
    "A corporate office, glass windows, modern architecture, photorealistic",
    "A traditional Korean house, wooden interior, warm lighting, cinematic",
    "A city street at night, neon lights, rain, cinematic atmosphere",
    "A wealthy businessman in a suit, serious expression, office background",
    "A detective examining evidence, crime scene, dramatic lighting",
    "A family dinner scene, tension in the air, Korean drama style",
    "A rooftop confrontation, city skyline background, dramatic sunset",
    "A car chase scene, motion blur, intense action, cinematic",
    "A wedding ceremony, elegant venue, emotional moment, photorealistic",
    "A funeral scene, mourners in black, somber atmosphere, cinematic",
    "A beach at sunset, romantic scene, warm colors, photorealistic",
    "A mountain landscape, dramatic clouds, epic vista, cinematic",
    "A modern apartment interior, minimalist design, natural lighting"
]

def queue_prompt(prompt):
    p = {"prompt": prompt}
    data = json.dumps(p).encode('utf-8')
    req = urllib.request.Request(f"{COMFY_URL}/prompt", data=data)
    return json.loads(urllib.request.urlopen(req).read())

def get_history(prompt_id):
    with urllib.request.urlopen(f"{COMFY_URL}/history/{prompt_id}") as response:
        return json.loads(response.read())

def generate_batch(prompts_batch, batch_num):
    """Generate a batch of 4 images at once"""
    print(f"\n🚀 배치 {batch_num} 시작 (4장 동시 생성)...")
    
    # 배치 크기 4로 설정
    workflow = {
      "32": { 
          "inputs": { 
              "landscape": False,
              "ratio": "3:2  (photo)", 
              "size": "medium (recommended)", 
              "batch_size": 4  # 4장 동시 생성
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
              "text": prompts_batch[0],  # 첫 번째 프롬프트 사용
              "clip": ["44", 0]
          }, 
          "class_type": "CLIPTextEncode"
      },
      "18": { 
          "inputs": { 
              "seed": int(time.time()) + batch_num * 1000, 
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
              "filename_prefix": f"Batch20/Batch{batch_num}_", 
              "civitai_compatible_metadata": True 
          }, 
          "class_type": "SaveImage //ZImagePowerNodes"
      }
    }
    
    try:
        res = queue_prompt(workflow)
        prompt_id = res['prompt_id']
        print(f"  ✅ 큐 등록: {prompt_id}")
        
        # 완료 대기
        timeout = 180  # 3분
        start = time.time()
        while True:
            if time.time() - start > timeout:
                print(f"  ⏱️ 타임아웃")
                return False
            
            history = get_history(prompt_id)
            if prompt_id in history:
                print(f"  ✅ 배치 {batch_num} 완료! (4장)")
                return True
            time.sleep(2)
    except Exception as e:
        print(f"  ❌ 에러: {e}")
        return False

if __name__ == "__main__":
    print("🚀 20장 배치 최적화 생성 시작...")
    print("📊 전략: 4장씩 5개 배치로 분할")
    
    total_start = time.time()
    success_count = 0
    
    # 5개 배치 (각 4장씩)
    for i in range(5):
        batch_prompts = PROMPTS[i*4:(i+1)*4]
        if generate_batch(batch_prompts, i+1):
            success_count += 4
    
    total_time = time.time() - total_start
    
    print(f"\n✅ 완료!")
    print(f"⏱️  총 시간: {total_time:.1f}초")
    print(f"📊 성공: {success_count}/20장")
    print(f"📈 평균: {total_time/20:.1f}초/장")

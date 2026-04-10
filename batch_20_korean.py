
import json
import urllib.request
import time

# [설정]
COMFY_URL = "http://127.0.0.1:8188"

# 한국인 고정 프롬프트 (강력)
KOREAN_BASE = "Korean person, East Asian features, Korean ethnicity, Korean face, black hair, Korean drama style"
NEGATIVE_BASE = "western, caucasian, white person, blonde, foreign, non-Asian"

# 20개 프롬프트 (각각 다름)
PROMPTS = [
    f"{KOREAN_BASE}, wealthy Korean woman in handcuffs, dramatic lighting, photorealistic, 8k",
    f"{KOREAN_BASE}, luxury penthouse on fire, smoke and flames, photorealistic, cinematic",
    f"{KOREAN_BASE}, young Korean woman with fake tears, manipulative expression, dramatic scene",
    f"{KOREAN_BASE}, Korean police officers in burning building, intense action, photorealistic",
    f"{KOREAN_BASE}, Korean courtroom scene, judge and lawyers, cinematic",
    f"{KOREAN_BASE}, Korean prisoner in cell, cold and dark, dramatic shadows, photorealistic",
    f"{KOREAN_BASE}, Korean patient in hospital room, medical equipment, emotional scene, cinematic lighting",
    f"{KOREAN_BASE}, Korean businessman in corporate office, glass windows, modern architecture, photorealistic",
    f"{KOREAN_BASE}, traditional Korean house interior, wooden design, warm lighting, cinematic",
    f"{KOREAN_BASE}, Korean person on city street at night, neon lights, rain, cinematic atmosphere",
    f"{KOREAN_BASE}, wealthy Korean businessman in suit, serious expression, office background",
    f"{KOREAN_BASE}, Korean detective examining evidence, crime scene, dramatic lighting",
    f"{KOREAN_BASE}, Korean family dinner scene, tension in the air, drama style",
    f"{KOREAN_BASE}, Korean rooftop confrontation, city skyline background, dramatic sunset",
    f"{KOREAN_BASE}, Korean car chase scene, motion blur, intense action, cinematic",
    f"{KOREAN_BASE}, Korean wedding ceremony, elegant venue, emotional moment, photorealistic",
    f"{KOREAN_BASE}, Korean funeral scene, mourners in black, somber atmosphere, cinematic",
    f"{KOREAN_BASE}, Korean couple at beach sunset, romantic scene, warm colors, photorealistic",
    f"{KOREAN_BASE}, Korean mountain landscape, dramatic clouds, epic vista, cinematic",
    f"{KOREAN_BASE}, Korean modern apartment interior, minimalist design, natural lighting"
]

def queue_prompt(prompt):
    p = {"prompt": prompt}
    data = json.dumps(p).encode('utf-8')
    req = urllib.request.Request(f"{COMFY_URL}/prompt", data=data)
    return json.loads(urllib.request.urlopen(req).read())

def get_history(prompt_id):
    with urllib.request.urlopen(f"{COMFY_URL}/history/{prompt_id}") as response:
        return json.loads(response.read())

def generate_single(prompt_text, img_num):
    """단일 이미지 생성 (순차 번호)"""
    
    workflow = {
      "32": { 
          "inputs": { 
              "landscape": False,
              "ratio": "3:2  (photo)", 
              "size": "medium (recommended)", 
              "batch_size": 1  # 1장씩 생성
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
              "text": NEGATIVE_BASE,
              "clip": ["44", 0]
          }, 
          "class_type": "CLIPTextEncode"
      },
      "18": { 
          "inputs": { 
              "seed": int(time.time() * 1000) + img_num, 
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
              "filename_prefix": f"Korean_Drama/KD_{img_num:04d}", 
              "civitai_compatible_metadata": True 
          }, 
          "class_type": "SaveImage //ZImagePowerNodes"
      }
    }
    
    try:
        res = queue_prompt(workflow)
        prompt_id = res['prompt_id']
        
        # 완료 대기
        timeout = 120
        start = time.time()
        while True:
            if time.time() - start > timeout:
                print(f"  ⏱️ 타임아웃")
                return False
            
            history = get_history(prompt_id)
            if prompt_id in history:
                return True
            time.sleep(1)
    except Exception as e:
        print(f"  ❌ 에러: {e}")
        return False

if __name__ == "__main__":
    print("🚀 20장 한국 드라마 스타일 생성 시작...")
    print("📊 전략: 한국인 고정 + 각각 다른 프롬프트")
    
    total_start = time.time()
    success_count = 0
    
    for i, prompt in enumerate(PROMPTS, start=1):
        print(f"\n[{i}/20] 생성 중...")
        print(f"  📜 {prompt[:60]}...")
        
        if generate_single(prompt, i):
            print(f"  ✅ 완료! (KD_{i:04d})")
            success_count += 1
        else:
            print(f"  ❌ 실패")
    
    total_time = time.time() - total_start
    
    print(f"\n✅ 완료!")
    print(f"⏱️  총 시간: {total_time:.1f}초")
    print(f"📊 성공: {success_count}/20장")
    print(f"📈 평균: {total_time/success_count:.1f}초/장" if success_count > 0 else "")

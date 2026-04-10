import requests
import json
import time
import os
import re

RUNPOD_API_URL = "https://ktshs13vdfmcia-8188.proxy.runpod.net"

def generate_chosun_image(prompt, filename_prefix, width=1024, height=1536):
    print(f"🚀 [RunPod] '조선스낵' 고해상도({width}x{height}) 생성 요청: {prompt[:50]}...")
    
    workflow = {
      "9": {
        "inputs": {
          "filename_prefix": filename_prefix,
          "images": ["57:8", 0]
        },
        "class_type": "SaveImage"
      },
      "57:30": {
        "inputs": {
          "clip_name": "qwen_3_4b.safetensors",
          "type": "lumina2",
          "device": "default"
        },
        "class_type": "CLIPLoader"
      },
      "57:29": {
        "inputs": {
          "vae_name": "ae.safetensors"
        },
        "class_type": "VAELoader"
      },
      "57:33": {
        "inputs": {
          "conditioning": ["57:27", 0]
        },
        "class_type": "ConditioningZeroOut"
      },
      "57:8": {
        "inputs": {
          "samples": ["57:3", 0],
          "vae": ["57:29", 0]
        },
        "class_type": "VAEDecode"
      },
      "57:28": {
        "inputs": {
          "unet_name": "z_image_turbo_bf16.safetensors",
          "weight_dtype": "default"
        },
        "class_type": "UNETLoader"
      },
      "57:27": {
        "inputs": {
          "text": f"(Masterpiece, best quality, 8k), {prompt}, traditional Korean Joseon style, cinematic lighting, highly detailed, photorealistic, historical accuracy",
          "clip": ["57:30", 0]
        },
        "class_type": "CLIPTextEncode"
      },
      "57:13": {
        "inputs": {
          "width": width,
          "height": height,
          "batch_size": 1
        },
        "class_type": "EmptySD3LatentImage"
      },
      "57:11": {
        "inputs": {
          "shift": 3.0,
          "model": ["57:28", 0]
        },
        "class_type": "ModelSamplingSD3"
      },
      "57:3": {
        "inputs": {
          "seed": int(time.time() % 1000000000),
          "steps": 6,
          "cfg": 1,
          "sampler_name": "euler",
          "scheduler": "simple",
          "denoise": 1,
          "model": ["57:11", 0],
          "positive": ["57:27", 0],
          "negative": ["57:33", 0],
          "latent_image": ["57:13", 0]
        },
        "class_type": "KSampler"
      }
    }

    try:
        response = requests.post(f"{RUNPOD_API_URL}/prompt", json={"prompt": workflow}, timeout=30)
        if response.status_code == 200:
            prompt_id = response.json().get("prompt_id")
            return prompt_id
    except Exception as e:
        print(f"⚠️ 연결 오류: {e}")
    return None

def check_and_download(prompt_id, output_path):
    start_time = time.time()
    while time.time() - start_time < 300: 
        try:
            res = requests.get(f"{RUNPOD_API_URL}/history/{prompt_id}", timeout=10)
            if res.status_code == 200:
                history = res.json().get(prompt_id)
                if history:
                    outputs = history.get('outputs', {})
                    if '9' in outputs:
                        images = outputs['9']['images']
                        for img in images:
                            filename = img['filename']
                            img_url = f"{RUNPOD_API_URL}/view?filename={filename}&type=output"
                            img_data = requests.get(img_url, timeout=60).content
                            with open(output_path, "wb") as f:
                                f.write(img_data)
                            return True
            time.sleep(3)
        except Exception as e:
            time.sleep(3)
    return False

if __name__ == "__main__":
    # 국장님 피드백: "주막 이모가 이뻐야되 풍만하고" 
    # [욕심 주모와 빈 항아리 - 미녀 주모 버전]
    jumo_desc = "extremely beautiful and seductive young Korean woman in her 20s, voluptuous and curvy body with large bust, wearing elegant but slightly loose traditional Hanbok"
    
    script_prompts = [
        f"(Masterpiece, best quality, 8k), {jumo_desc}, a greedy tavern keeper (Jumo) in a traditional Joseon tavern, pouring watered-down rice wine into a large ceramic jar held by a traveler, the jar is labeled '신령', cinematic lighting, photorealistic",
        f"(Masterpiece, best quality, 8k), a close-up of a humble traveler tasting wine, while looking at the {jumo_desc} with a dazed expression, the woman is smiling mockingly, humorous scene, photorealistic",
        f"(Masterpiece, best quality, 8k), the traveler pouring wine back into the vat, the {jumo_desc} shouting and moving dynamically in shock, showing her voluptuous figure, splashing liquid, cinematic action, photorealistic",
        f"(Masterpiece, best quality, 8k), the {jumo_desc} looking devastated sitting by her wine vat, staring at the watered wine, showing her beautiful face and curvy figure, the traveler walking away behind her, photorealistic"
    ]
    
    output_dir = "/Users/a12/projects/tts/tmp_samples_dark"
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"📋 [절세미녀 주모] 테마로 총 {len(script_prompts)}개의 고해상도 장면 생성을 시작합니다.")
    
    for i, prompt in enumerate(script_prompts):
        output_file = os.path.join(output_dir, f"jumo_beauty_{i+1}.png")
        p_id = generate_chosun_image(prompt, f"Jumo_Beauty_{i+1}", width=1024, height=1536)
        if p_id:
            print(f"⏳ {i+1}번 장면 생성 중 (ID: {p_id})...")
            if check_and_download(p_id, output_file):
                print(f"✅ 장면 {i+1} 성공 저장: {output_file}")
            else:
                print(f"❌ 장면 {i+1} 실패")
        time.sleep(1)

    print("🏁 미녀 주모 버전 전 장면 생성 완료.")

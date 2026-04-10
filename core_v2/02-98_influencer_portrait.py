import json
import urllib.request
import time
import os
import random

# ComfyUI 설정
SERVER_ADDRESS = "127.0.0.1:8188"
OUTPUT_DIR = os.path.expanduser("~/Downloads/Influencer_Portrait")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 유저 요청 프롬프트
USER_PROMPT = (
    "A high-quality, photorealistic portrait of a glamorous Korean female influencer. "
    "She has long wavy black hair and trendy makeup. Wearing a tight gray ribbed cropped cardigan and white sweatpants. "
    "Shot from a high-angle POV, looking down from above. Outdoor urban street background with asphalt texture. "
    "Holding a plastic cup of iced americano with a yellow straw. Natural daylight, cinematic lighting, 8k, "
    "highly detailed skin texture, masterpiece, raw photo."
)

def queue_prompt(prompt_workflow):
    p = {"prompt": prompt_workflow}
    data = json.dumps(p).encode('utf-8')
    req = urllib.request.Request(f"http://{SERVER_ADDRESS}/prompt", data=data)
    with urllib.request.urlopen(req) as response:
        return json.loads(response.read())

def get_history(prompt_id):
    with urllib.request.urlopen(f"http://{SERVER_ADDRESS}/history/{prompt_id}") as response:
        return json.loads(response.read())

def get_flux_schnell_workflow(prompt, seed):
    # Flux Schnell 최적화 워크플로우 (6단계)
    return {
        "3": {
            "inputs": {
                "seed": seed,
                "steps": 6,
                "cfg": 1.0,
                "sampler_name": "euler",
                "scheduler": "simple",
                "denoise": 1.0,
                "model": ["4", 0],
                "positive": ["6", 0],
                "negative": ["7", 0],
                "latent_image": ["5", 0]
            },
            "class_type": "KSampler"
        },
        "4": {
            "inputs": {
                "unet_name": "flux1-schnell-fp8.safetensors",
                "weight_dtype": "fp8_e4m3fn"
            },
            "class_type": "UNETLoader"
        },
        "5": {
            "inputs": {
                "width": 720,
                "height": 1280,
                "batch_size": 1
            },
            "class_type": "EmptyLatentImage"
        },
        "6": {
            "inputs": {
                "text": prompt,
                "clip": ["8", 0]
            },
            "class_type": "CLIPTextEncode"
        },
        "7": {
            "inputs": {
                "text": "blurry, low quality, distorted, bad anatomy, text, watermark",
                "clip": ["8", 0]
            },
            "class_type": "CLIPTextEncode"
        },
        "8": {
            "inputs": {
                "clip_name1": "t5xxl_fp8_e4m3fn.safetensors",
                "clip_name2": "clip_l.safetensors",
                "type": "flux"
            },
            "class_type": "DualCLIPLoader"
        },
        "9": {
            "inputs": {
                "vae_name": "ae.safetensors"
            },
            "class_type": "VAELoader"
        },
        "10": {
            "inputs": {
                "samples": ["3", 0],
                "vae": ["9", 0]
            },
            "class_type": "VAEDecode"
        },
        "11": {
            "inputs": {
                "filename_prefix": "Influencer_Portrait",
                "images": ["10", 0]
            },
            "class_type": "SaveImage"
        }
    }

def main():
    print(f"🚀 [ComfyUI] 인플루언서 초상화 생성 시작 (6단계)...")
    seed = random.randint(1, 1000000000)
    workflow = get_flux_schnell_workflow(USER_PROMPT, seed)
    
    try:
        req_res = queue_prompt(workflow)
        prompt_id = req_res['prompt_id']
        print(f"   📤 큐 등록 완료 (ID: {prompt_id})")
        
        print("   ⏳ 생성 중... (ComfyUI 화면을 확인하세요)")
        while True:
            history = get_history(prompt_id)
            if prompt_id in history:
                print(f"✅ 생성 완료!")
                # 이미지 파일명 확인
                outputs = history[prompt_id].get('outputs', {})
                for node_id in outputs:
                    for img in outputs[node_id].get('images', []):
                        print(f"💡 파일 생성됨: {img['filename']}")
                break
            time.sleep(5)
            
    except Exception as e:
        print(f"❌ 에러 발생: {e}")

if __name__ == "__main__":
    main()

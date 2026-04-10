import json
import urllib.request
import time
import os
import random
import sys

# ComfyUI 설정
SERVER_ADDRESS = "127.0.0.1:8188"
OUTPUT_DIR = os.path.expanduser("~/Downloads/Comfy_Gen_Results")
os.makedirs(OUTPUT_DIR, exist_ok=True)

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
                "width": 1024, # 배경용/일반용은 1024x1024가 무난하지만, 세로형 선호 시 수정 가능
                "height": 1024,
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
                "filename_prefix": "Comfy_Manual",
                "images": ["10", 0]
            },
            "class_type": "SaveImage"
        }
    }

def main():
    if len(sys.argv) < 2:
        print("❌ 프롬프트가 입력되지 않았습니다.")
        return

    prompt_text = sys.argv[1]
    print(f"\n🚀 [ComfyUI] 이미지 생성 시작")
    print(f"📝 프롬프트: {prompt_text}")
    
    seed = random.randint(1, 1000000000)
    workflow = get_flux_schnell_workflow(prompt_text, seed)
    
    try:
        req_res = queue_prompt(workflow)
        prompt_id = req_res['prompt_id']
        print(f"   📤 큐 등록 완료 (ID: {prompt_id})")
        
        while True:
            history = get_history(prompt_id)
            if prompt_id in history:
                print(f"✅ 생성 완료!")
                outputs = history[prompt_id].get('outputs', {})
                for node_id in outputs:
                    for img in outputs[node_id].get('images', []):
                        print(f"💡 파일 생성됨: {img['filename']}")
                break
            time.sleep(2)
            
    except Exception as e:
        print(f"❌ 에러 발생: {e}")

if __name__ == "__main__":
    main()

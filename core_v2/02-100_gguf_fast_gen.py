import json
import urllib.request
import urllib.parse
import uuid

# ---------------------------------------------------------
# [CONFIG] RunPod ComfyUI 접속 정보
# ---------------------------------------------------------
SERVER_ADDRESS = "127.0.0.1:8188"  # 터널링(8181)은 맥북용이고, 스크립트가 런팟에서 돌면 8188입니다.
CLIENT_ID = str(uuid.uuid4())

def queue_prompt(prompt):
    p = {"prompt": prompt, "client_id": CLIENT_ID}
    data = json.dumps(p).encode('utf-8')
    req =  urllib.request.Request(f"http://{SERVER_ADDRESS}/prompt", data=data)
    return json.loads(urllib.request.urlopen(req).read())

# ---------------------------------------------------------
# [WORKFLOW] GGUF Z-Image-Turbo 최적화 워크플로우
# ---------------------------------------------------------
workflow_json = {
    "1": {
        "inputs": {
            "unet_name": "z_image_turbo-Q5_K_M.gguf"
        },
        "class_type": "UnetLoaderGGUF"
    },
    "2": {
        "inputs": {
            "clip_name": "qwen_3_4b_fp8_mixed.safetensors",
            "type": "lumina2"
        },
        "class_type": "CLIPLoader"
    },
    "3": {
        "inputs": {
            "vae_name": "ae.safetensors"
        },
        "class_type": "VAELoader"
    },
    "4": {
        "inputs": {
            "width": 1024,
            "height": 1024,
            "batch_size": 1
        },
        "class_type": "EmptyLatentImage"
    },
    "5": {
        "inputs": {
            "text": "A beautiful cinematic shot of a Korean warrior in a bamboo forest, extreme detail, photorealistic, 8k",
            "clip": ["2", 0]
        },
        "class_type": "CLIPTextEncode"
    },
    "6": {
        "inputs": {
            "seed": 42,
            "steps": 6,
            "cfg": 1.5,
            "sampler_name": "euler",
            "scheduler": "simple",
            "denoise": 1.0,
            "model": ["1", 0],
            "positive": ["5", 0],
            "negative": ["7", 0],
            "latent_image": ["4", 0]
        },
        "class_type": "KSampler"
    },
    "7": {
        "inputs": {
            "text": "low quality, blurry, distorted, messy",
            "clip": ["2", 0]
        },
        "class_type": "CLIPTextEncode"
    },
    "8": {
        "inputs": {
            "samples": ["6", 0],
            "vae": ["3", 0]
        },
        "class_type": "VAEDecode"
    },
    "9": {
        "inputs": {
            "filename_prefix": "GGUF_Gen",
            "images": ["8", 0]
        },
        "class_type": "SaveImage"
    }
}

if __name__ == "__main__":
    print(f"🚀 GGUF 초고속 이미지 생성 요청 중... (Server: {SERVER_ADDRESS})")
    try:
        response = queue_prompt(workflow_json)
        if "prompt_id" in response:
            print(f"✅ 요청 성공! Prompt ID: {response['prompt_id']}")
            print("💡 ComfyUI 화면에서 진행 상황을 확인하세요.")
        else:
            print(f"❌ 요청 실패 (검증 오류 가능성): {json.dumps(response, indent=2, ensure_ascii=False)}")
    except Exception as e:
        print(f"❌ 요청 과정에서 네트워크/문법 에러 발생: {e}")

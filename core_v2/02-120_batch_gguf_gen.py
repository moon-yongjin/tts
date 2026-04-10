import json
import urllib.request
import urllib.parse
import uuid
import time

# ---------------------------------------------------------
# [CONFIG] RunPod ComfyUI 접속 정보
# ---------------------------------------------------------
SERVER_ADDRESS = "127.0.0.1:8188"
CLIENT_ID = str(uuid.uuid4())

def queue_prompt(prompt):
    p = {"prompt": prompt, "client_id": CLIENT_ID}
    data = json.dumps(p).encode('utf-8')
    req =  urllib.request.Request(f"http://{SERVER_ADDRESS}/prompt", data=data)
    return json.loads(urllib.request.urlopen(req).read())

def check_queue():
    req = urllib.request.Request(f"http://{SERVER_ADDRESS}/queue")
    with urllib.request.urlopen(req) as response:
        return json.loads(response.read())

# ---------------------------------------------------------
# [SCENES] 10개의 상세 프롬프트 정의
# ---------------------------------------------------------
prompts = [
    "A young Korean daughter-in-law sweating in a messy traditional kitchen, steam rising from large pots, various Korean holiday foods (jeon, galbi) on the table, exhausted expression, cinematic lighting, 8k, photorealistic",
    "A greedy-looking middle-aged Korean woman (sister-in-law) with an annoying smirk, holding empty plastic food containers, entering a kitchen, vibrant colors, extreme detail",
    "Korean sister-in-law pointing fingers at a large steaming pot of beef ribs (Galbi-jjim) with a demanding expression, kitchen background, photorealistic",
    "Exhausted Korean daughter-in-law looking flustered and holding a spatula, trying to stop her sister-in-law, emotional scene, cinematic lighting",
    "Mean-looking Korean woman shouting at another woman in a kitchen, aggressive posture, messy kitchen environment, extreme facial details",
    "An elderly Korean mother-in-law (70s) appearing at the kitchen door, sharp angry eyes, traditional Korean house background, powerful presence, cinematic",
    "Korean mother-in-law shouting at her own daughter, protecting her daughter-in-law who is crying in the background, high drama, emotional contrast",
    "A woman being pushed out of a traditional house's front door by an angry elderly woman, face red with shame and shock, outdoor, daylight",
    "Close up of an elderly Korean woman holding the rough, scarred hands of a younger woman, warm and apologetic expression, soft lighting, emotional warmth",
    "A smiling elderly Korean woman handing a white envelope (money) to a younger woman, both standing in a warm-lit Korean living room, happy ending, peaceful atmosphere"
]

# ---------------------------------------------------------
# [WORKFLOW TEMPLATE]
# ---------------------------------------------------------
def get_workflow(positive_prompt, index):
    return {
        "1": {
            "inputs": {"unet_name": "z_image_turbo-Q5_K_M.gguf"},
            "class_type": "UnetLoaderGGUF"
        },
        "2": {
            "inputs": {"clip_name": "qwen_3_4b_fp8_mixed.safetensors", "type": "lumina2"},
            "class_type": "CLIPLoader"
        },
        "3": {
            "inputs": {"vae_name": "ae.safetensors"},
            "class_type": "VAELoader"
        },
        "4": {
            "inputs": {"width": 1024, "height": 1024, "batch_size": 1},
            "class_type": "EmptyLatentImage"
        },
        "5": {
            "inputs": {"text": positive_prompt, "clip": ["2", 0]},
            "class_type": "CLIPTextEncode"
        },
        "6": {
            "inputs": {
                "seed": 42 + index,
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
            "inputs": {"text": "low quality, blurry, distorted, messy, animation, anime, cartoon, painting", "clip": ["2", 0]},
            "class_type": "CLIPTextEncode"
        },
        "8": {
            "inputs": {"samples": ["6", 0], "vae": ["3", 0]},
            "class_type": "VAEDecode"
        },
        "9": {
            "inputs": {"filename_prefix": f"Batch_Scene_{index+1:02d}", "images": ["8", 0]},
            "class_type": "SaveImage"
        }
    }

if __name__ == "__main__":
    print(f"🚀 총 {len(prompts)}개의 장면 생성을 시작합니다...")
    
    for i, p_text in enumerate(prompts):
        print(f"📸 [{i+1}/{len(prompts)}] 생성 중: {p_text[:50]}...")
        workflow = get_workflow(p_text, i)
        try:
            res = queue_prompt(workflow)
            print(f"   ✅ 대기열 진입 성공 (ID: {res['prompt_id']})")
        except Exception as e:
            print(f"   ❌ 요청 실패: {e}")
        
        # 과부하 방지를 위해 잠깐 대기 (GGUF는 워낙 빨라서 2초면 충분)
        time.sleep(2)

    print("\n✨ 모든 장면의 생성이 요청되었습니다. ComfyUI에서 확인해 주세요!")

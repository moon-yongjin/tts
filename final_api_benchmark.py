import json
import urllib.request
import time

def queue_prompt(prompt):
    p = {"prompt": prompt}
    data = json.dumps(p).encode('utf-8')
    req = urllib.request.Request("http://127.0.0.1:8188/prompt", data=data)
    with urllib.request.urlopen(req) as response:
        return json.loads(response.read().decode('utf-8'))

def get_history(prompt_id):
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:8188/history/{prompt_id}") as response:
            return json.loads(response.read().decode('utf-8'))
    except:
        return {}

api_prompt = {
    "1": {
        "inputs": {
            "ckpt_name": "ltx-video-2b-v0.9-Q4_K_M.gguf"
        },
        "class_type": "CheckpointLoaderSimple"
    },
    "2": {
        "inputs": {
            "clip_name": "t5xxl_fp8_e4m3fn.safetensors",
            "type": "ltxv",
            "device": "default"
        },
        "class_type": "CLIPLoader"
    },
    "3": {
        "inputs": {
            "image": "benchmark_input.png",
            "upload": "image"
        },
        "class_type": "LoadImage"
    },
    "4": {
        "inputs": {
            "vae_name": "LTX-Video-VAE-BF16.safetensors"
        },
        "class_type": "VAELoader"
    },
    "5": {
        "inputs": {
            "text": "A high quality cinematic video with smooth movement.",
            "clip": ["2", 0]
        },
        "class_type": "CLIPTextEncode"
    },
    "6": {
        "inputs": {
            "text": "low quality, blurry, static, distorted",
            "clip": ["2", 0]
        },
        "class_type": "CLIPTextEncode"
    },
    "7": {
        "inputs": {
            "positive": ["5", 0],
            "negative": ["6", 0],
            "vae": ["4", 0],
            "image": ["3", 0],
            "width": 768,
            "height": 512,
            "length": 33,
            "batch_size": 1,
            "strength": 1.0
        },
        "class_type": "LTXVImgToVideo"
    },
    "8": {
        "inputs": {
            "samples": ["7", 2], # index 2 is LATENT based on object_info
            "vae": ["4", 0]
        },
        "class_type": "VAEDecode"
    },
    "9": {
        "inputs": {
            "images": ["8", 0],
            "filename_prefix": "FINAL_API_BENCH"
        },
        "class_type": "SaveVideo"
    }
}

print("Initiating direct API generation benchmark...")
start_time = time.time()

try:
    result = queue_prompt(api_prompt)
    prompt_id = result['prompt_id']
    print(f"Prompt queued! ID: {prompt_id}")
    
    last_print = 0
    while True:
        history = get_history(prompt_id)
        if prompt_id in history:
            print("\nGeneration FINISHED successfully!")
            break
        
        current_time = time.time()
        if current_time - last_print > 5:
            print(f"Still generating... Elapsed: {current_time - start_time:.1f}s")
            last_print = current_time
            
        time.sleep(2)
        if current_time - start_time > 1200: # 20 min cap
            print("\nBenchmark timeout (20 mins reached).")
            break

    total_time = time.time() - start_time
    print(f"\n--- BENCHMARK RESULT ---")
    print(f"Total end-to-end time: {total_time:.2f} seconds")
    print(f"------------------------")

except Exception as e:
    print(f"\nAPI Error: {e}")

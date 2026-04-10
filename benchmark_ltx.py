import json
import urllib.request
import time
import os

def queue_prompt(prompt):
    p = {"prompt": prompt}
    data = json.dumps(p).encode('utf-8')
    req = urllib.request.Request("http://127.0.0.1:8188/prompt", data=data)
    with urllib.request.urlopen(req) as response:
        return json.loads(response.read().decode('utf-8'))

def get_history(prompt_id):
    with urllib.request.urlopen(f"http://127.0.0.1:8188/history/{prompt_id}") as response:
        return json.loads(response.read().decode('utf-8'))

# The workflow file is in save format, we need to convert to API format or use the regular one.
# ComfyUI API usually expects the "export as API" format.
# If we have the regular JSON, we can try to send it if ComfyUI-Manager's API supports it.
# However, standard ComfyUI /prompt expects the API format.

# I will use a simplified API-format version of the LTX workflow for this benchmark.
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
            "image": "i2v_input_test.png",
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
            "width": 768,
            "height": 512,
            "num_frames": 33,
            "frame_rate": 24,
            "positive": "A cinematic video of a fox in the snow.",
            "negative": "low quality, blurry",
            "model": ["1", 0],
            "clip": ["2", 0],
            "vae": ["4", 0],
            "image": ["3", 0]
        },
        "class_type": "LTXVImgToVideo"
    },
    "6": {
        "inputs": {
            "samples": ["5", 0],
            "vae": ["4", 0]
        },
        "class_type": "VAEDecode"
    },
    "7": {
        "inputs": {
            "images": ["6", 0],
            "filename_prefix": "Benchmark_LTX"
        },
        "class_type": "SaveVideo"
    }
}

print("Starting benchmark at:", time.ctime())
start_time = time.time()

try:
    result = queue_prompt(api_prompt)
    prompt_id = result['prompt_id']
    print(f"Prompt queued with ID: {prompt_id}")
    
    while True:
        history = get_history(prompt_id)
        if prompt_id in history:
            print("Generation complete!")
            break
        time.sleep(2)
        elapsed = time.time() - start_time
        if elapsed > 600: # 10 min timeout
            print("Timeout!")
            break
        print(f"Elapsed: {elapsed:.2f}s...", end='\r')

    end_time = time.time()
    total_time = end_time - start_time
    print(f"\nTotal generation time: {total_time:.2f} seconds")
except Exception as e:
    print(f"Error: {e}")

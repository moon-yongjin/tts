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

# Exact API Mapping from the optimized GGUF workflow
api_prompt = {
    "38": { "inputs": { "clip_name": "t5xxl_fp8_e4m3fn.safetensors", "type": "ltxv", "device": "default" }, "class_type": "CLIPLoader" },
    "44": { "inputs": { "ckpt_name": "ltx-video-2b-v0.9-Q4_K_M.gguf" }, "class_type": "UnetLoaderGGUF" },
    "45": { "inputs": { "vae_name": "LTX-Video-VAE-BF16.safetensors" }, "class_type": "VAELoader" },
    "78": { "inputs": { "image": "benchmark_input.png", "upload": "image" }, "class_type": "LoadImage" },
    "6": { "inputs": { "text": "A beautiful cinematic video, high quality, smooth movement.", "clip": ["38", 0] }, "class_type": "CLIPTextEncode" },
    "7": { "inputs": { "text": "low quality, blurry, static, distorted", "clip": ["38", 0] }, "class_type": "CLIPTextEncode" },
    "77": {
        "inputs": {
            "positive": ["6", 0], "negative": ["7", 0], "vae": ["45", 0], "image": ["78", 0],
            "width": 768, "height": 512, "length": 33, "batch_size": 1, "strength": 1.0
        },
        "class_type": "LTXVImgToVideo"
    },
    "69": { "inputs": { "positive": ["77", 0], "negative": ["77", 1] }, "class_type": "LTXVConditioning" },
    "71": { "inputs": { "steps": 30, "cfg": 2.05, "stochasticity": 0.95, "offload_model": True, "latent": ["77", 2] }, "class_type": "LTXVScheduler" },
    "73": { "inputs": { "sampler_name": "euler" }, "class_type": "KSamplerSelect" },
    "72": {
        "inputs": {
            "add_noise": True, "noise_seed": int(time.time()), "steps": 3, "cfg": 1,
            "model": ["44", 0], "positive": ["69", 0], "negative": ["69", 1], "sampler": ["73", 0], "sigmas": ["71", 0], "latent_image": ["77", 2]
        },
        "class_type": "SamplerCustom"
    },
    "8": { "inputs": { "samples": ["72", 0], "vae": ["45", 0] }, "class_type": "VAEDecode" },
    "80": { "inputs": { "frame_rate": 24, "images": ["8", 0] }, "class_type": "CreateVideo" },
    "81": { "inputs": { "video": ["80", 0], "filename_prefix": "API_GEN_SUCCESS" }, "class_type": "SaveVideo" }
}

print("Initiating API Video Generation...")
start_time = time.time()

try:
    result = queue_prompt(api_prompt)
    prompt_id = result['prompt_id']
    print(f"Prompt successfully queued! ID: {prompt_id}")
    
    while True:
        history = get_history(prompt_id)
        if prompt_id in history:
            print("\n--- GENERATION COMPLETE! ---")
            break
        time.sleep(5)
        print(f"Generating... {time.time()-start_time:.1f}s elapsed", end='\r')

    print(f"\nTotal time: {time.time()-start_time:.2f} seconds")
    print(f"Output saved in ComfyUI/output with prefix 'API_GEN_SUCCESS'")
except Exception as e:
    print(f"\nError: {e}")

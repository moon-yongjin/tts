import json
import urllib.request
import time
import os

# --- CONFIGURATION ---
URL = "http://127.0.0.1:8188/prompt"
INPUT_IMAGE = "i2v_input_test.png"  # Place your image in ComfyUI/input folder
PROMPT = "A beautiful cinematic video, high quality, smooth movement."
NEG_PROMPT = "low quality, blurry, static, distorted, bad anatomy"

def run_generation():
    # Exact GGUF API mapping verified on your Mac
    prompt_data = {
        "1": { "class_type": "UnetLoaderGGUF", "inputs": { "ckpt_name": "ltx-video-2b-v0.9-Q4_K_M.gguf" } },
        "2": { "class_type": "CLIPLoader", "inputs": { "clip_name": "t5xxl_fp8_e4m3fn.safetensors", "type": "ltxv", "device": "default" } },
        "3": { "class_type": "VAELoader", "inputs": { "vae_name": "LTX-Video-VAE-BF16.safetensors" } },
        "4": { "class_type": "LoadImage", "inputs": { "image": INPUT_IMAGE, "upload": "image" } },
        "5": { "class_type": "CLIPTextEncode", "inputs": { "text": PROMPT, "clip": ["2", 0] } },
        "6": { "class_type": "CLIPTextEncode", "inputs": { "text": NEG_PROMPT, "clip": ["2", 0] } },
        "7": { "class_type": "LTXVImgToVideo", "inputs": { "positive": ["5", 0], "negative": ["6", 0], "vae": ["3", 0], "image": ["4", 0], "width": 768, "height": 512, "length": 33, "batch_size": 1, "strength": 1.0 } },
        "8": { "class_type": "LTXVConditioning", "inputs": { "positive": ["7", 0], "negative": ["7", 1], "frame_rate": 24 } },
        "9": { "class_type": "LTXVScheduler", "inputs": { "steps": 30, "cfg": 2.05, "stochasticity": 0.95, "offload_model": True, "latent": ["7", 2] } },
        "10": { "class_type": "KSamplerSelect", "inputs": { "sampler_name": "euler" } },
        "11": { "class_type": "SamplerCustom", "inputs": { "add_noise": True, "noise_seed": int(time.time()), "steps": 3, "cfg": 1, "model": ["1", 0], "positive": ["8", 0], "negative": ["8", 1], "sampler": ["10", 0], "sigmas": ["9", 0], "latent_image": ["7", 2] } },
        "12": { "class_type": "VAEDecode", "inputs": { "samples": ["11", 0], "vae": ["3", 0] } },
        "13": { "class_type": "CreateVideo", "inputs": { "frame_rate": 24, "images": ["12", 0] } },
        "14": { "class_type": "SaveVideo", "inputs": { "video": ["13", 0], "filename_prefix": "FINAL_AUTO_GEN" } }
    }

    print(f"🚀 Starting LTX-Video I2V Generation for {INPUT_IMAGE}...")
    start_time = time.time()
    
    try:
        req = urllib.request.Request(URL, data=json.dumps({"prompt": prompt_data}).encode('utf-8'))
        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read().decode('utf-8'))
            print(f"✅ Success! Prompt Queued. ID: {result['prompt_id']}")
            print(f"⏱️ Check ComfyUI for progress. Output will be saved with prefix 'FINAL_AUTO_GEN'.")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    run_generation()

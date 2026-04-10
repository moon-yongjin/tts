import requests
import json
import time

API_KEY = "rpa_FHG3CVKINI8UZ0II8UU0V4O482A57CBUCMZDLU261yr9lz"
ENDPOINT_ID = "wvz92hpw73rmdw"

# A minimal valid standard ComfyUI API workflow (SD 1.5 Text to Image)
# We just want to see if the server parses it and tries to execute it.
# Even if It fails due to missing model, it proves the server is alive.
dummy_workflow = {
    "3": {
        "class_type": "KSampler",
        "inputs": {
            "cfg": 8,
            "denoise": 1,
            "latent_image": ["5", 0],
            "model": ["4", 0],
            "negative": ["7", 0],
            "positive": ["6", 0],
            "sampler_name": "euler",
            "scheduler": "normal",
            "seed": 8566257,
            "steps": 20
        }
    },
    "4": {
        "class_type": "CheckpointLoaderSimple",
        "inputs": {
            "ckpt_name": "v1-5-pruned-emaonly.safetensors"
        }
    },
    "5": {
        "class_type": "EmptyLatentImage",
        "inputs": {
            "batch_size": 1,
            "height": 512,
            "width": 512
        }
    },
    "6": {
        "class_type": "CLIPTextEncode",
        "inputs": {
            "clip": ["4", 1],
            "text": "masterpiece best quality girl"
        }
    },
    "7": {
        "class_type": "CLIPTextEncode",
        "inputs": {
            "clip": ["4", 1],
            "text": "bad hands"
        }
    },
    "8": {
        "class_type": "VAEDecode",
        "inputs": {
            "samples": ["3", 0],
            "vae": ["4", 2]
        }
    },
    "9": {
        "class_type": "SaveImage",
        "inputs": {
            "filename_prefix": "ComfyUI",
            "images": ["8", 0]
        }
    }
}

payload = {
    "input": {
        "workflow": dummy_workflow
    }
}

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

url = f"https://api.runpod.ai/v2/{ENDPOINT_ID}/runsync"

print(f"Sending request to RunPod Serverless Endpoint '{ENDPOINT_ID}'...")
print("This might take a while if the container is still initializing (Cold Start)...")

try:
    response = requests.post(url, headers=headers, json=payload, timeout=300)
    print(f"Status Code: {response.status_code}")
    print("Response JSON:")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))
except requests.exceptions.Timeout:
    print("Request timed out. The server might still be downloading the large 20GB+ Docker image.")
except Exception as e:
    print(f"An error occurred: {e}")

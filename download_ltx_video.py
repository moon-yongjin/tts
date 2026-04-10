import os
from huggingface_hub import hf_hub_download

def download_file(repo_id, filename, target_dir):
    print(f"Downloading {filename} from {repo_id} to {target_dir}...")
    os.makedirs(target_dir, exist_ok=True)
    try:
        path = hf_hub_download(repo_id=repo_id, filename=filename, local_dir=target_dir)
        print(f"Downloaded to {path}")
    except Exception as e:
        print(f"Error downloading {filename}: {e}")

base_path = "/Users/a12/projects/tts/ComfyUI/models"

# 1. LTX-Video Main Model (GGUF Q4_K_M - 1.6GB)
download_file("city96/LTX-Video-gguf", "ltx-video-2b-v0.9-Q4_K_M.gguf", os.path.join(base_path, "unet"))

# 2. LTX-Video VAE (BF16 - 150MB)
download_file("city96/LTX-Video-gguf", "LTX-Video-VAE-BF16.safetensors", os.path.join(base_path, "vae"))

# 3. T5XXL Text Encoder (FP8 - 4.9GB)
download_file("comfyanonymous/flux_text_encoders", "t5xxl_fp8_e4m3fn.safetensors", os.path.join(base_path, "text_encoders"))

print("LTX-Video (I2V) model download initiated!")

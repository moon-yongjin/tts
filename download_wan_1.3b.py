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

# 1. VAE (Wan 2.1)
download_file("Comfy-Org/Wan_2.1_ComfyUI_repackaged", "split_files/vae/wan_2.1_vae.safetensors", os.path.join(base_path, "vae"))

# 2. Text Encoder (T5 FP8 - Lightweight)
download_file("Comfy-Org/Wan_2.1_ComfyUI_repackaged", "split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors", os.path.join(base_path, "text_encoders"))

# 3. GGUF Model (1.3B - Ultra-Lightweight for 24GB RAM)
download_file("samuelchristlie/Wan2.1-T2V-1.3B-GGUF", "Wan2.1-T2V-1.3B-Q8_0.gguf", os.path.join(base_path, "unet"))

print("Wan 2.1 1.3B models download initiated!")

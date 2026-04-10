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

# Wan 2.2 GGUF Repo (Quantized for 24GB RAM)
repo_gguf = "huchukato/Wan2.2-Remix-I2V-v2.1-GGUF"
repo_lora = "Comfy-Org/Wan_2.2_ComfyUI_Repackaged"

# 1. GGUF Models (High/Low Noise) - Much smaller (~8-9GB each)
download_file(repo_gguf, "High/wan22RemixT2VI2V_i2vHighV21-Q4_K_M.gguf", os.path.join(base_path, "unet"))
download_file(repo_gguf, "Low/wan22RemixT2VI2V_i2vLowV21-Q4_K_M.gguf", os.path.join(base_path, "unet"))

# 2. LoRAs (Lightx2v 4-step) - Small files, okay to keep
download_file(repo_lora, "split_files/loras/wan2.2_i2v_lightx2v_4steps_lora_v1_high_noise.safetensors", os.path.join(base_path, "loras"))
download_file(repo_lora, "split_files/loras/wan2.2_i2v_lightx2v_4steps_lora_v1_low_noise.safetensors", os.path.join(base_path, "loras"))

print("Wan 2.2 I2V models and LoRAs download initiated!")

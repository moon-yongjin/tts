from huggingface_hub import hf_hub_download
import os

def download_models():
    base_path = "/Users/a12/projects/tts/ComfyUI/models"
    
    # PuLID Model (Corrected repo: guozinan/PuLID)
    print("Downloading PuLID v1 model from guozinan/PuLID...")
    try:
        hf_hub_download(
            repo_id="guozinan/PuLID",
            filename="pulid_v1.bin",
            local_dir=os.path.join(base_path, "pulid"),
            local_dir_use_symlinks=False
        )
    except Exception as e:
        print(f"Failed to download pulid_v1.bin: {e}")
    
    # Eva02 CLIP Vision Model (Corrected path if needed)
    print("Downloading Eva02 CLIP Vision model from h94/IP-Adapter...")
    try:
        hf_hub_download(
            repo_id="h94/IP-Adapter",
            filename="models/image_encoder/Eva02_L_14_336_v90_baked.pt",
            local_dir=os.path.join(base_path, "clip_vision"),
            local_dir_use_symlinks=False
        )
    except Exception as e:
        print(f"Failed to download Eva02 model: {e}")
    
    print("✅ Process complete. Check output for success/failure.")

if __name__ == "__main__":
    download_models()

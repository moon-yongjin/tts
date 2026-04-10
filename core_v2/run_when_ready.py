import time
import os
import subprocess
import sys

# Target File: Full Flux Checkpoint (11GB FP8 version)
TARGET_FILE = "/Users/a12/projects/tts/ComfyUI/models/checkpoints/flux1-dev-fp8_full.safetensors"
MIN_SIZE = 11_000_000_000 # ~11GB

COMFY_SCRIPT = "/Users/a12/projects/tts/core_v2/02-3_comfyui_flux_batch.py"
PYTHON_EXE = "/Users/a12/miniforge3/envs/qwen-tts/bin/python"

def check_file():
    print("-" * 50)
    if os.path.exists(TARGET_FILE):
        size = os.path.getsize(TARGET_FILE)
        if size >= MIN_SIZE:
            print(f"✅ Ready: {os.path.basename(TARGET_FILE)} ({size/1024/1024/1024:.2f} GB)")
            return True
        else:
            print(f"⏳ Downloading: {os.path.basename(TARGET_FILE)} ({size/1024/1024/1024:.2f} GB / 17.2 GB)")
    else:
        print(f"❌ Missing: {os.path.basename(TARGET_FILE)}")
    print("-" * 50)
    return False

def main():
    print("🚀 Monitoring FULL Flux Download & Auto-Launch Started...")
    
    while True:
        if check_file():
            print("\n🎉 Full model ready! Launching ComfyUI Batch in 5 seconds...")
            time.sleep(5)
            
            # Kill existing ComfyUI
            os.system("pkill -f main.py")
            time.sleep(2)
            
            # Run the batch script
            subprocess.run([PYTHON_EXE, COMFY_SCRIPT])
            break
        
        print(f"💤 Waiting 60s... (Next check: {time.strftime('%H:%M:%S', time.localtime(time.time() + 60))})")
        time.sleep(60)

if __name__ == "__main__":
    main()

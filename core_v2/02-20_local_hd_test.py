import os
import subprocess
import time
from pathlib import Path

# Configuration
MFLUX_GENERATE_PATH = "/Users/a12/miniforge3/envs/qwen-tts/bin/mflux-generate"
FLUX_MODEL = "mzbac/flux1.schnell.8bit.mlx"
OUTPUT_DIR = Path.home() / "Downloads" / "local_hd_test"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# User's provided prompt (Adjusted for "Natural HD" as requested earlier)
# Original: "A hyper-realistic close-up portrait of a stunning 25-year-old Korean woman with perfect glass skin, wearing a sophisticated professional navy blazer. She is standing in a sunlit modern luxury office. In her hand, she holds a sleek transparent glass tablet displaying the clear text 'PREMIUM CARE'. Incredible skin details, visible pores, cinematic soft lighting, 8k resolution, photorealistic, masterpiece, shot on 85mm lens."

ADJUSTED_PROMPT = (
    "A natural close-up portrait of a 25-year-old Korean woman with authentic skin texture, "
    "wearing a sophisticated professional navy blazer. She is standing in a sunlit modern luxury office. "
    "In her hand, she holds a sleek transparent glass tablet displaying the text 'PREMIUM CARE'. "
    "Soft cinematic lighting, Korean drama aesthetic, soft HD quality (720p), natural skin, "
    "gentle film grain, shot on 85mm lens."
)

def run_local_gen(prompt):
    filename = f"local_natural_hd_{int(time.time())}.png"
    filepath = OUTPUT_DIR / filename
    
    print(f"🚀 [Local Flux] Generating image: {filename}...")
    print(f"📝 Prompt: {prompt}")
    
    cmd = [
        MFLUX_GENERATE_PATH,
        "--model", FLUX_MODEL,
        "--prompt", prompt,
        "--steps", "4",
        "--width", "720",
        "--height", "1280",
        "--output", str(filepath),
        "--seed", str(int(time.time()) % 10000)
    ]
    
    start_time = time.time()
    try:
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stdout, stderr = process.communicate()
        
        elapsed = time.time() - start_time
        if process.returncode == 0 and filepath.exists():
            print(f"✅ Success: {filepath}")
            print(f"⏱️ Generation Time: {elapsed:.2f} seconds")
            return str(filepath), elapsed
        else:
            print(f"❌ Failed (Code: {process.returncode})")
            print(f"--- STDERR ---\n{stderr}")
    except Exception as e:
        print(f"❌ Error: {e}")
    return None, 0

if __name__ == "__main__":
    path, elapsed = run_local_gen(ADJUSTED_PROMPT)
    if path:
        print(f"\n🎉 File saved to: {path}")

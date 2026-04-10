import os
import requests
import time
from pathlib import Path

# Hugging Face API configuration
HF_TOKENS = [
    "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",
    "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",
    "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"
]
# Using the standard FLUX.1-schnell model as a baseline for Turbo test
API_URL = "https://router.huggingface.co/hf-inference/models/black-forest-labs/FLUX.1-schnell"

OUTPUT_DIR = Path.home() / "Downloads" / "hf_turbo_test"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Natural Cinematic Overhaul: Authentic Drama Look
PROMPT = (
    "A high-quality commercial film still of a high-end Seoul penthouse scene. "
    "Authentic cinematic realism, natural skin textures with subtle imperfections, "
    "professional cinematography. An elderly Korean mother-in-law (Oksun) kneeling on "
    "cool white marble, her expression carrying heavy emotional weight. "
    "A younger woman (Hyerim) standing with an arrogant posture. "
    "Cold professional color grading, soft professional lighting, Arri Alexa color science, "
    "natural bokeh, 2010s premium TV drama aesthetic, believable environment."
)

def generate_hf_turbo(prompt):
    filename = f"hf_turbo_official_{int(time.time())}.png"
    filepath = OUTPUT_DIR / filename
    
    print(f"🚀 [HF API Turbo] Generating: {filename}...")
    print(f"📝 Prompt: {prompt}")
    
    # Official settings found in the Space
    payload = {
        "inputs": prompt,
        "parameters": {
            "num_inference_steps": 9,
            "guidance_scale": 0.0,
            "width": 1024, # Optimized for 1k as seen in Space
            "height": 1024
        }
    }
    
    start_time = time.time()
    for token in HF_TOKENS:
        headers = {"Authorization": f"Bearer {token}"}
        try:
            response = requests.post(API_URL, headers=headers, json=payload, timeout=120)
            if response.status_code == 200:
                with open(filepath, "wb") as f:
                    f.write(response.content)
                elapsed = time.time() - start_time
                print(f"✅ Success: {filepath}")
                print(f"⏱️ HF API Time: {elapsed:.2f} seconds")
                return str(filepath), elapsed
            elif response.status_code == 503:
                print(f"⏳ Model loading on HF... waiting 20s")
                time.sleep(20)
                continue
            else:
                print(f"❌ HF API Error {response.status_code}: {response.text}")
        except Exception as e:
            print(f"❌ Exception: {e}")
            
    return None, 0

if __name__ == "__main__":
    path, elapsed = generate_hf_turbo(PROMPT)
    if path:
        print(f"\n🎉 HF Result saved to: {path}")

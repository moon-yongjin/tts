import os
import requests
import json
import time
from pathlib import Path
import argparse

# Hugging Face API Settings
HF_TOKENS = [
    "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",
    "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",
    "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"
]
API_URL = "https://router.huggingface.co/hf-inference/models/black-forest-labs/FLUX.1-schnell"

def generate_image_hf(prompt, output_path, width=1024, height=1024):
    """Generates an image using Hugging Face Flux API (Schnell)."""
    payload = {
        "inputs": prompt,
        "parameters": {
            "num_inference_steps": 4, # Schnell is optimized for 4 steps
            "guidance_scale": 0.0,
            "width": width,
            "height": height
        }
    }
    
    for token in HF_TOKENS:
        headers = {"Authorization": f"Bearer {token}"}
        try:
            print(f"🎨 [HF API] Generating to: {output_path.name}")
            response = requests.post(API_URL, headers=headers, json=payload, timeout=120)
            if response.status_code == 200:
                with open(output_path, "wb") as f:
                    f.write(response.content)
                print(f"✅ Success: {output_path.name}")
                return True
            elif response.status_code == 503:
                print(f"⏳ Model loading on HF... waiting 15s")
                time.sleep(15)
                continue
            else:
                print(f"❌ HF API Error {response.status_code}: {response.text}")
        except Exception as e:
            print(f"❌ Exception during HF generation: {e}")
            
    return False

def batch_generate_from_script(script_path, output_dir, limit=None):
    """Reads a script (JSON or TXT) and generates images."""
    os.makedirs(output_dir, exist_ok=True)
    
    # Placeholder for script parsing logic (similar to existing visual directors)
    # For now, let's assume a list of prompts if it's a test or simple list
    prompts = []
    if script_path.endswith('.json'):
        with open(script_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Support different JSON structures found in the codebase
            if isinstance(data, list):
                prompts = [item.get('visual_prompt', item.get('prompt', '')) for item in data]
            elif 'scenes' in data:
                prompts = [scene.get('visual_prompt', '') for scene in data['scenes']]
    else:
        with open(script_path, 'r', encoding='utf-8') as f:
            prompts = [line.strip() for line in f if line.strip()]

    if limit:
        prompts = prompts[:limit]

    print(f"🚀 [Toffee Visual Director] Starting batch generation ({len(prompts)} images)")
    start_time = time.time()
    
    success_count = 0
    for i, prompt in enumerate(prompts):
        filename = f"scene_{i+1:03d}.png"
        out_path = Path(output_dir) / filename
        
        # Style injection for ToffeeTime aesthetic: Cinematic, High-end, Dramatic
        full_prompt = (
            f"A high-quality cinematic film still, professional photography, natural lighting, "
            f"8k resolution, highly detailed, realistic textures. {prompt} "
            f"--ar 9:16" # Note: FLUX API handles actual pixels, but we can put this in prompt just in case
        )
        
        # 9:16 Vertical Ratio (e.g., 720x1280 or 1024x1792)
        # We'll use 896x1536 as a high-quality vertical option that fits HF limits well
        if generate_image_hf(full_prompt, out_path, width=896, height=1536):
            success_count += 1
        
        # Rate limit spacing
        time.sleep(0.5)

    elapsed = time.time() - start_time
    print(f"\n✨ Batch Completion: {success_count}/{len(prompts)} images")
    print(f"⏱️ Total time: {elapsed/60:.1f} minutes")
    return success_count

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", action="store_true", help="Run a quick test generation")
    parser.add_argument("--script", type=str, help="Path to script/prompts file")
    parser.add_argument("--output", type=str, default="temp_toffee_out", help="Output directory")
    args = parser.parse_args()

    if args.test:
        test_prompt = "A mysterious traveler standing in front of a glowing ancient temple in a dark forest, cinematic lighting, 8k."
        test_out = Path("temp_toffee_test.png")
        generate_image_hf(test_prompt, test_out, width=896, height=1536)
    elif args.script:
        batch_generate_from_script(args.script, args.output)
    else:
        print("Please provide --script or --test")

import os
import requests
import json
import time
from pathlib import Path

# Hugging Face API 설정
HF_TOKEN = "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"
API_URL = "https://router.huggingface.co/hf-inference/models/black-forest-labs/FLUX.1-schnell"
headers = {"Authorization": f"Bearer {HF_TOKEN}"}

DOWNLOADS_DIR = Path.home() / "Downloads"
OUTPUT_DIR = DOWNLOADS_DIR / "다이어리_세로_manual_skip"
os.makedirs(OUTPUT_DIR, exist_ok=True)

PROMPTS = [
    "A cinematic Korean drama scene: An elderly Korean woman Oksun in traditional field worker clothes kneeling on cold marble floor in a luxury penthouse in Apgujeong. Her daughter-in-law stands over her mockingly, holding expensive designer bags. Dramatic lighting, photorealistic, 4K.",
    "A beautiful young Korean woman, dressed in head-to-toe luxury brands, laughing mockingly at an old woman on the floor. She is swinging a multi-million won designer handbag. Luxury penthouse background, 4K.",
    "Close-up of an evil smile on a young Korean woman's face, lifting the chin of an old woman with a manicured hand. High-end penthouse interior, cinematic lighting.",
    "The old woman's wrinkled hand suddenly grabbing the young woman's wrist with incredible strength. The young woman looks shocked and pained. Dramatic close-up.",
    "The old woman Oksun standing up in her luxury living room, sharp eyes filled with hidden power. She is brushing back her wet hair elegantly. Cinematic depth of field.",
    "A large high-definition TV screen in a luxury living room showing secret surveillance footage of a woman in a hotel room. The young woman is looking at the screen in pure horror.",
    "A mountain of luxury dresses and designer bags being poured out onto a cold marble floor by security guards in black suits. Luxury penthouse background.",
    "The old woman Oksun holding a gasoline can, pouring it over a pile of expensive designer bags and dresses. Cold, determined expression on her face.",
    "The old woman throwing a lit lighter onto a pile of luxury goods. Intense orange flames starting to erupt in a luxury penthouse living room, cinematic.",
    "Two security guards in black suits dragging a screaming, struggling young woman out of a luxury apartment towards the front door. Chaotic dramatic scene.",
    "The old woman Oksun elegantly sipping a glass of wine, standing with her back to the rising flames in her luxury living room. Epic cinematic masterpiece.",
    "Close-up of a police handcuffs being snapped onto the young woman's wrists. In the background, the old woman whispers into her ear. Dark dramatic lighting."
]

def generate_image(prompt, index):
    filename = f"story-scene-{index+1:02d}.png"
    output_path = OUTPUT_DIR / filename
    
    print(f"🎨 Generating {filename}...")
    
    payload = {
        "inputs": prompt,
        "parameters": {"num_inference_steps": 4} # schnell is fast
    }
    
    for attempt in range(3):
        try:
            response = requests.post(API_URL, headers=headers, json=payload, timeout=120)
            if response.status_code == 200:
                with open(output_path, "wb") as f:
                    f.write(response.content)
                print(f"✅ Success: {filename}")
                return True
            elif response.status_code == 503:
                print(f"⏳ Model loading (attempt {attempt+1})... waiting 10s")
                time.sleep(10)
            else:
                print(f"❌ Error {response.status_code}: {response.text}")
                break
        except Exception as e:
            print(f"❌ Exception: {e}")
            time.sleep(2)
            
    return False

if __name__ == "__main__":
    print(f"🚀 Starting Batch Generation ({len(PROMPTS)} images)")
    start_time = time.time()
    
    success_count = 0
    for i, prompt in enumerate(PROMPTS):
        if generate_image(prompt, i):
            success_count += 1
        # Rate limit protection
        time.sleep(1)
        
    elapsed = time.time() - start_time
    print(f"\n✨ Completed: {success_count}/{len(PROMPTS)} images generated.")
    print(f"⏱️ Total time: {elapsed/60:.1f} minutes.")
    print(f"📂 Location: {OUTPUT_DIR}")

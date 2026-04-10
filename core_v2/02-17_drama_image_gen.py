import os
import requests
import json
import time
from pathlib import Path

# Hugging Face API configuration
HF_TOKENS = [
    "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",
    "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",
    "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"
]
API_URL = "https://router.huggingface.co/hf-inference/models/black-forest-labs/FLUX.1-schnell"

DOWNLOADS_DIR = Path.home() / "Downloads"
OUTPUT_DIR = DOWNLOADS_DIR / "drama_scenes_vertical"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Character consistency snippets
OKSUN_DESC = "Oksun, an elegant Korean woman in her 60s, short gray-streaked bob haircut, cold sharp eyes, pearl necklace, sophisticated beige silk blouse"
HYERIM_DESC = "Hyerim, a glamorous Korean woman in her 30s, long wavy black hair, heavy makeup, flashy designer red dress, arrogant expression"

PROMPTS = [
    f"(Vertical 9:16) Cinematic shot of a luxurious Apgujeong penthouse. {OKSUN_DESC} is kneeling on a cold white marble floor. {HYERIM_DESC} stands over her, holding a luxury handbag, looking down with a sneer. Dramatic top-down lighting.",
    f"(Vertical 9:16) Close-up dramatic shot. {HYERIM_DESC} is forcefully trying to press Oksun's thumb onto a red ink stamp for a legal document. {OKSUN_DESC}'s hand suddenly showing intense strength, her fingers gripping Hyerim's wrist tightly.",
    f"(Vertical 9:16) Dynamic motion shot. {OKSUN_DESC} has stood up, her wet hair slicked back. She is delivering a powerful slap to {HYERIM_DESC}'s face. Hyerim's head is whipped to the side, hair flying.",
    f"(Vertical 9:16) Wide cinematic shot. {OKSUN_DESC} stands tall in a grand living room, pointing at a massive wall-mounted screen. The screen shows evidence of {HYERIM_DESC}'s infidelity. Hyerim is on the floor in horror.",
    f"(Vertical 9:16) Dramatic shot. {OKSUN_DESC} is pouring gasoline from a red canister over a mountain of luxury handbags and designer dresses in the middle of a marble living room. Cold expression.",
    f"(Vertical 9:16) Extreme close-up. {OKSUN_DESC}'s face, cold eyes illuminated by the orange flicker of a Zippo lighter. Her expression is heartless and regal.",
    f"(Vertical 9:16) Cinematic shot. The luxurious living room is engulfed in flames. {HYERIM_DESC} is crawling on the floor, surrounded by burning luxury items, screaming in despair. Realistic fire.",
    f"(Vertical 9:16) Action shot. Two security guards in black suits are lifting {HYERIM_DESC} like luggage and throwing her out onto the penthouse hallway carpet. High tension.",
    f"(Vertical 9:16) Close-up. {HYERIM_DESC} is being handcuffed by police officers. {OKSUN_DESC} is leaning in, whispering into Hyerim's ear with a terrifyingly calm smile.",
    f"(Vertical 9:16) Elegant final victory shot. {OKSUN_DESC} standing with her back to the camera, silhouetted against the raging fire in the luxury living room. She is gracefully sipping red wine from a glass."
]

def generate_image(prompt, index):
    filename = f"drama-scene-{index+1:02d}.png"
    output_path = OUTPUT_DIR / filename
    
    # Try different tokens if one fails
    for token in HF_TOKENS:
        headers = {"Authorization": f"Bearer {token}"}
        print(f"🎨 Generating {filename} using token starting with {token[:8]}...")
        
        payload = {
            "inputs": prompt,
            "parameters": {
                "num_inference_steps": 4,
                "width": 720,
                "height": 1280
            }
        }
        
        for attempt in range(2):
            try:
                response = requests.post(API_URL, headers=headers, json=payload, timeout=120)
                if response.status_code == 200:
                    with open(output_path, "wb") as f:
                        f.write(response.content)
                    print(f"✅ Success: {filename}")
                    return True
                elif response.status_code == 503:
                    print(f"⏳ Model loading... waiting 10s")
                    time.sleep(10)
                else:
                    print(f"❌ Error {response.status_code}: {response.text}")
                    break # Try next token
            except Exception as e:
                print(f"❌ Exception: {e}")
                time.sleep(2)
    return False

if __name__ == "__main__":
    print(f"🚀 Starting Drama Scene Generation ({len(PROMPTS)} images)")
    success_count = 0
    for i, prompt in enumerate(PROMPTS):
        if generate_image(prompt, i):
            success_count += 1
        time.sleep(1) # Small delay
        
    print(f"\n✨ Completed: {success_count}/{len(PROMPTS)} images.")
    print(f"📂 Location: {OUTPUT_DIR}")

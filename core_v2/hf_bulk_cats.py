import os
import sys
import json
import time
from pathlib import Path

# Add project root to path for imports
PROJ_ROOT = Path("/Users/a12/projects/tts")
sys.path.append(str(PROJ_ROOT))

# Load Config for HF Token
CONFIG_PATH = PROJ_ROOT / "config.json"
config = {}
if CONFIG_PATH.exists():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        config = json.load(f)

HF_TOKEN = config.get("HuggingFace_API_KEY", "")

if not HF_TOKEN:
    print("Error: HuggingFace API Key not found in config.json")
    sys.exit(1)

from huggingface_hub import InferenceClient

client = InferenceClient(api_key=HF_TOKEN)

# Output Directory
INPUT_DIR = os.path.expanduser("~/Downloads/Grok_Video_Input")
os.makedirs(INPUT_DIR, exist_ok=True)

CAT_JOBS = [
    {"name": "space_astronaut_cat", "prompt": "A fluffy ginger kitten in a tiny hyper-realistic space suit, floating inside a spaceship with earth in the background, cinematic lighting, 8k."},
    {"name": "chef_kitten_baking", "prompt": "A cute grey kitten wearing a tiny chef hat, paws covered in flour, sitting next to a miniature cupcake, warm bakery lighting, high detail."},
    {"name": "royal_persian_cat", "prompt": "A majestic white Persian cat wearing a tiny golden crown with jewels, sitting on a velvet red throne, dramatic royal lighting, 8k."},
    {"name": "cyberpunk_neon_cat", "prompt": "A sleek black cat with glowing neon blue circuitry patterns on its fur, sitting on a rainy rooftop in a futuristic city, vibrant neon lighting."},
    {"name": "detective_sphynx", "prompt": "A serious Sphynx cat wearing a tiny detective trench coat and hat, holding a miniature magnifying glass, moody noir lighting, 8k."},
    {"name": "flower_fairy_cat", "prompt": "A tiny calico kitten with delicate iridescent butterfly wings, sleeping inside a blooming lotus flower, magical forest lighting, bokeh petals."},
    {"name": "samurai_warrior_cat", "prompt": "A brave tabby cat in miniature samurai armor, sitting under a falling cherry blossom tree, traditional Japanese art style, 8k."},
    {"name": "viking_explorer_cat", "prompt": "A large fluffy Maine Coon cat wearing a tiny viking helmet, standing on the prow of a miniature longship in a misty fjord, epic lighting."},
    {"name": "wizard_hat_cat", "prompt": "A black kitten with glowing emerald eyes wearing a tall purple wizard hat, surrounded by floating magical orbs and books, mystical atmosphere."},
    {"name": "scuba_diver_cat", "prompt": "A cute kitten in a tiny steampunk diving suit, exploring a colorful coral reef with bubbles, bioluminescent fish around, 8k."},
    {"name": "ballerina_tutu_kitten", "prompt": "A tiny white kitten wearing a pink tulle tutu, standing on its hind legs in a soft spotlight on a wooden stage, graceful and cute."},
    {"name": "detective_sherlock_cat", "prompt": "A British Shorthair wearing a tiny deerstalker hat and smoking a miniature pipe (bubble pipe), sitting in a cozy study, 8k."},
    {"name": "pilot_goggles_cat", "prompt": "A brave kitten wearing leather pilot goggles and a scarf, sitting in the cockpit of a miniature vintage biplane, sunny sky background."},
    {"name": "painter_artist_kitten", "prompt": "A messy kitten with colorful paint splatters on its fur, holding a small paintbrush, sitting in front of a miniature canvas, soft studio light."},
    {"name": "pirate_captain_cat", "prompt": "A rugged but cute cat with a tiny eye patch and captain's hat, standing on a chest of gold coins, tropical island background."},
    {"name": "gardener_straw_hat_cat", "prompt": "A kitten wearing a tiny straw hat and sitting in a clay pot, surrounded by vibrant sunflowers and a small watering can, golden hour."},
    {"name": "dj_headphones_cat", "prompt": "A cool cat wearing oversized neon headphones, paws on a miniature turntable, vibrant club lighting, smoke effects, 8k."},
    {"name": "winter_scarf_kitten", "prompt": "A fluffy white kitten wrapped in a thick red knitted scarf, sitting in the snow, snowflakes landing on its nose, cozy winter lighting."},
    {"name": "superhero_cape_cat", "prompt": "A heroic kitten wearing a tiny red cape blowing in the wind, standing on a high-rise ledge overlooking a city, epic heroic pose."},
    {"name": "strawberry_hat_kitten", "prompt": "A round, fluffy kitten wearing a tiny hat that looks like a giant strawberry, sitting in a basket of real strawberries, soft aesthetic, 8k."}
]

def generate_bulk():
    print(f"🚀 [HF Cat Gen Batch 3] Starting generation of {len(CAT_JOBS)} high-quality cat assets...")
    
    for i, job in enumerate(CAT_JOBS):
        idx = i + 21 # Continuing from 1-20
        print(f"📸 [{idx}/40] Generating: {job['name']}...")
        try:
            image = client.text_to_image(
                job['prompt'],
                model="black-forest-labs/FLUX.1-schnell" 
            )
            
            # Save Image
            img_filename = f"cat_{idx:02d}_{job['name']}.png"
            img_path = os.path.join(INPUT_DIR, img_filename)
            image.save(img_path)
            
            # Save Prompt for Grok (Image-to-Video)
            prompt_path = img_path + ".prompt.txt"
            with open(prompt_path, "w", encoding="utf-8") as f:
                f.write(f"Animate this cute cat {job['name']} with a 6-second cinematic flow: subtle ear twitch, slow meaningful blink, and gentle fur movement in the wind.")
            
            print(f"   -> Saved: {img_filename}")
            
        except Exception as e:
            print(f"   -> ❌ Failed {job['name']}: {e}")
            
    print("\n✅ [HF Cat Gen Batch 3] 20 cat assets pushed to Grok!")

if __name__ == "__main__":
    generate_bulk()

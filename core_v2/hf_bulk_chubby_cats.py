import os
import sys
import json
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

CHUBBY_CAT_JOBS = [
    {"name": "chubby_bread_cat", "prompt": "An extremely chubby, round ginger cat shaped like a loaf of bread, sitting on a wooden bakery counter, soft flour dust in the air, warm lighting, 8k."},
    {"name": "fat_calico_cushion", "prompt": "A very fat calico cat lying flat like a fluffy pancake on a luxury sofa, belly spilling over, soft silk textures, elegant living room, 8k."},
    {"name": "round_blue_british_shorthair", "prompt": "A perfectly round, chubby Blue British Shorthair cat sitting and looking at the camera, thick dense fur, soft studio lighting, bokeh background."},
    {"name": "chubby_cat_in_box", "prompt": "A huge, fluffy chubby cat squeezed into a tiny cardboard box, belly bulging out from the sides, hilarious and cute, high detail, 8k."},
    {"name": "fat_cat_eating_sundae", "prompt": "A chubby cat sitting at a tiny table, wearing a bib, staring happily at a giant ice cream sundae, vibrant colors, cinematic lighting."},
    {"name": "round_fluffy_kitten_ball", "prompt": "A tiny but impossibly round and chubby white kitten that looks like a ball of cotton, sitting in a field of sunflowers, golden hour."},
    {"name": "chubby_cat_on_hammock", "prompt": "A very fat cat struggling to balance on a tiny mesh hammock, belly sagging through the holes, tropical beach background, sunny day, 8k."},
    {"name": "fat_tuxedo_cat_suit", "prompt": "A chubby tuxedo cat wearing a tiny tight bow tie that emphasizes its round neck, sitting on a library desk, soft lamp light, cozy atmosphere."},
    {"name": "round_cat_floating_balloon", "prompt": "A chubby, round cat being lifted off the ground by a single red balloon tied to its harness, dreamlike sky background, soft clouds, 8k."},
    {"name": "fat_cat_sleeping_laptop", "prompt": "A chubby cat completely covering a laptop keyboard while sleeping, its fat paws hanging off the edge, cozy home office lighting, 8k."},
    {"name": "chubby_scottish_fold_pot", "prompt": "A round Scottish Fold cat with ears folded, sitting inside a ceramic flower pot, overflow of fluff, garden background, high detail."},
    {"name": "fat_cat_winter_coat", "prompt": "An extremely chubby cat wearing a tiny, puffy winter jacket that looks like it might burst, standing in the snow, soft winter lighting."},
    {"name": "round_cat_yarn_mess", "prompt": "A chubby cat tangled in a mess of colorful yarn, looking confused, round belly exposed, soft wool textures, high detail, 8k."},
    {"name": "fat_cat_chef_hat", "prompt": "A very chubby, round cat wearing a chef hat, sitting behind a rolling pin and dough, looking like a master baker, warm kitchen light."},
    {"name": "chubby_cat_on_bookshelf", "prompt": "A fat cat squeezed between books on a shelf, its round body taking up the space of three books, dusty library aesthetic, warm rim light."},
    {"name": "round_cat_bubble_bath", "prompt": "A chubby cat sitting in a tiny tub filled with bubbles, bubble on its head, round face poking through, soft bathroom lighting, cute."},
    {"name": "fat_cat_superhero_cape", "prompt": "A chubby cat with a red cape, trying to pose heroically on a stool, its round belly making it look like a friendly hero, epic lighting."},
    {"name": "round_cat_drinking_milk", "prompt": "A very chubby cat with a milk mustache, sitting next to a spilled saucer, round fluffy body, soft morning light, 8k."},
    {"name": "fat_cat_in_pajamas", "prompt": "A chubby cat wearing tiny striped pajamas, yawning on a soft bed with many pillows, cozy bedtime atmosphere, high detail."},
    {"name": "chubby_cat_rainbow_fur", "prompt": "A round, chubby cat with soft iridescent rainbow-colored fur, sitting on a cloud, dreamlike fantasy aesthetic, soft sparkles, 8k."}
]

def generate_bulk():
    print(f"🚀 [HF Chubby Cat Gen Batch 4] Starting generation of {len(CHUBBY_CAT_JOBS)} 'Ddung-Nyang' assets...")
    
    for i, job in enumerate(CHUBBY_CAT_JOBS):
        idx = i + 41 # Continuing from 1-40
        print(f"📸 [{idx}/60] Generating: {job['name']}...")
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
                f.write(f"Animate this incredibly chubby cat {job['name']} with slow, heavy, and cute movements: a deep slow blink, a wobbly jiggle of its round belly, and a subtle tail flick.")
            
            print(f"   -> Saved: {img_filename}")
            
        except Exception as e:
            print(f"   -> ❌ Failed {job['name']}: {e}")
            
    print("\n✅ [HF Chubby Cat Gen Batch 4] 20 Ddung-Nyang assets pushed to Grok!")

if __name__ == "__main__":
    generate_bulk()

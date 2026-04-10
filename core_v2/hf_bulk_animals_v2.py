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

ANIMAL_JOBS = [
    {"name": "marshmallow_mantis", "prompt": "A tiny, cute praying mantis made of soft rainbow marshmallow, sitting on a chocolate branch, fantasy food world, 8k, macro photography."},
    {"name": "crystal_capybara", "prompt": "A fluffy baby capybara with a shell made of glowing amethyst crystals, soaking in a steaming hot spring at night, bokeh lanterns background."},
    {"name": "jelly_jellyfish_cat", "prompt": "A hybrid between a kitten and a jellyfish, translucent glowing body, swimming through a deep blue ocean with bioluminescent sparkles, cute large eyes."},
    {"name": "moss_mole", "prompt": "A tiny, round mole with fur made of soft green moss and tiny flowers blooming on its back, emerging from a hole in an enchanted forest floor, golden light."},
    {"name": "cookie_chipmunk", "prompt": "A chubby chipmunk with fur patterned like a chocolate chip cookie, holding a giant almond, sitting on a kitchen counter, soft warm lighting."},
    {"name": "pixel_penguin", "prompt": "A cute baby penguin made of glowing 3D pixels (voxels), sliding on a digital ice rink, vaporwave color palette, neon pink and blue lighting."},
    {"name": "yarn_yeti", "prompt": "A tiny, friendly baby yeti made entirely of white knitted yarn, wearing a small red scarf, sitting in a snowy mailbox, cozy atmosphere."},
    {"name": "donut_duckling", "prompt": "A fuzzy yellow duckling floating in a pond that looks like liquid frosting, with a strawberry donut as a lifebuoy, colorful sprinkles everywhere."},
    {"name": "origami_otter", "prompt": "A cute otter made of folded holographic paper, floating on a river of liquid silver, reflecting a futuristic city at night, sharp edges, 8k."},
    {"name": "pancake_platypus", "prompt": "A baby platypus that looks like a stack of mini pancakes, with a pat of butter on its head, swimming in a sea of maple syrup, extremely cute."}
]

def generate_bulk():
    print(f"🚀 [HF Image Gen Batch 2] Starting generation of {len(ANIMAL_JOBS)} new assets...")
    
    for i, job in enumerate(ANIMAL_JOBS):
        idx = i + 11 # Continuing from 1-10
        print(f"📸 [{idx}/20] Generating: {job['name']}...")
        try:
            image = client.text_to_image(
                job['prompt'],
                model="black-forest-labs/FLUX.1-schnell" 
            )
            
            # Save Image
            img_filename = f"animal_{idx:02d}_{job['name']}.png"
            img_path = os.path.join(INPUT_DIR, img_filename)
            image.save(img_path)
            
            # Save Prompt for Grok (Image-to-Video)
            prompt_path = img_path + ".prompt.txt"
            with open(prompt_path, "w", encoding="utf-8") as f:
                f.write(f"Animate this {job['name']} with charming movements: a slow blink, a curious head tilt, and subtle ambient motion in the background.")
            
            print(f"   -> Saved: {img_filename}")
            
        except Exception as e:
            print(f"   -> ❌ Failed {job['name']}: {e}")
            
    print("\n✅ [HF Image Gen Batch 2] 10 more assets pushed to Grok!")

if __name__ == "__main__":
    generate_bulk()

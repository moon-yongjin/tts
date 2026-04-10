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
    {"name": "galactic_goldfish", "prompt": "A tiny, transparent goldfish with nebula patterns inside its body, swimming through a void of stardust, cinematic lighting, 8k, highly detailed."},
    {"name": "cloud_corgi", "prompt": "A fluffy corgi puppy made of soft white clouds, hopping between golden-lined sunset clouds, dreamlike atmosphere, 8k."},
    {"name": "stardust_sloth", "prompt": "A fuzzy baby sloth hanging from a crescent moon made of crystal, glittering stardust fur, deep space background, bokeh stars."},
    {"name": "neon_narwhal", "prompt": "A cute narwhal with a glowing neon horn, swimming through a bioluminescent underwater cave, vibrant pink and teal lighting, 8k."},
    {"name": "petal_panther", "prompt": "A small panther cub with fur made of soft cherry blossom petals, walking through a Zen garden at golden hour, hyper-realistic."},
    {"name": "bubble_bunny", "prompt": "A round, fluffy bunny floating inside a giant soap bubble, reflecting a rainbow garden, soft rim lighting, cute aesthetic."},
    {"name": "aurora_axolotl", "prompt": "A pink axolotl with glowing aurora borealis patterns on its gills, floating in a dark pond reflecting the Northern Lights, magical."},
    {"name": "clockwork_chameleon", "prompt": "A cute baby chameleon made of polished gold and brass gears, sitting on a glowing emerald leaf, steam-punk aesthetic, 8k."},
    {"name": "sweetpea_turtle", "prompt": "A tiny turtle with a shell made of a blooming sweetpea flower, crawling on a dew-covered leaf, macro photography, 8k."},
    {"name": "whisker_wonder", "prompt": "A cross between a cat and a mouse with impossibly long, glowing whiskers, tinkering with a tiny clockwork music box, warm lantern light."}
]

def generate_bulk():
    print(f"🚀 [HF Image Gen] Starting generation of {len(ANIMAL_JOBS)} high-quality assets...")
    
    for i, job in enumerate(ANIMAL_JOBS):
        print(f"📸 [{i+1}/10] Generating: {job['name']}...")
        try:
            # Using FLUX.1-schnell or similar fast but high-quality model
            image = client.text_to_image(
                job['prompt'],
                model="black-forest-labs/FLUX.1-schnell" 
            )
            
            # Save Image
            img_filename = f"animal_{i+1:02d}_{job['name']}.png"
            img_path = os.path.join(INPUT_DIR, img_filename)
            image.save(img_path)
            
            # Save Prompt for Grok (Image-to-Video)
            # We want Grok to animate these, so we give it a simple animation prompt
            prompt_path = img_path + ".prompt.txt"
            with open(prompt_path, "w", encoding="utf-8") as f:
                f.write(f"Animate this {job['name']} with subtle movement: blinking eyes, slow breathing, and gentle background particles flowing.")
            
            print(f"   -> Saved: {img_filename}")
            
        except Exception as e:
            print(f"   -> ❌ Failed {job['name']}: {e}")
            
    print("\n✅ [HF Image Gen] All assets pushed to Grok Input folder!")

if __name__ == "__main__":
    generate_bulk()

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
OUTPUT_DIR = DOWNLOADS_DIR / "drama_scenes_natural_hd"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Natural HD Character consistency snippets (Authentic Korean TV drama look)
OKSUN_DESC = "A typical 60s Korean elderly woman, short broccoli permed hair, modest practical blouse, authentic Korean auntie facial features, 2010s Korean TV drama aesthetic, soft film grain, 720p HD quality."
HYERIM_DESC = "A 30s Korean drama villainess, elegant but sharp Korean features, natural looking TV makeup, long black straight hair, classic red dress. 2010s Korean TV drama aesthetic, soft 720p HD."

PROMPTS = [
    f"(Vertical 9:16) 2010s Korean TV drama still. {OKSUN_DESC} is kneeling on a typical Korean luxury apartment floor. {HYERIM_DESC} stands over her mockingly. Soft broadcast television lighting, 720p.",
    f"(Vertical 9:16) Close-up shot. {HYERIM_DESC}'s annoyed and arrogant expression, typical K-Drama antagonist look. Natural TV makeup, soft focus, 720p.",
    f"(Vertical 9:16) Close-up shot. {OKSUN_DESC}'s determined and sharp elderly face, showing hidden strength. Realistic Korean 60s woman features, 720p HD.",
    f"(Vertical 9:16) Mid-shot. {HYERIM_DESC} throwing legal papers at Oksun's face mockingly. Warm living room interior lighting, 2010s TV drama style.",
    f"(Vertical 9:16) Tight close-up. {HYERIM_DESC} forcefully grabbing {OKSUN_DESC}'s hand toward a red ink pad (In-gam). Authentic Korean setting, soft HD.",
    f"(Vertical 9:16) Action shot. {OKSUN_DESC}'s hand suddenly gripping Hyerim's wrist firmly. {HYERIM_DESC} looks shocked. Balanced TV lighting, 720p.",
    f"(Vertical 9:16) Close-up of {HYERIM_DESC}'s face in dramatic shock, slightly motion-blurred TV drama shot. Realistic skin texture, no AI shine, 720p.",
    f"(Vertical 9:16) {OKSUN_DESC} standing up slowly with dignity, tidying her hair. Cold and powerful Korean drama aura, natural lighting, HD.",
    f"(Vertical 9:16) Dynamic side-view action shot. {OKSUN_DESC} delivering a powerful slap to {HYERIM_DESC}'s face. Classic K-drama scene, soft focus background, 720p.",
    f"(Vertical 9:16) {OKSUN_DESC} standing tall, pointing a finger at a large TV screen in the living room. Natural apartment interior, soft shadows, HD.",
    f"(Vertical 9:16) Close-up of CCTV footage playing on the TV screen (low quality black and white footage). Dramatic TV drama still, 720p.",
    f"(Vertical 9:16) {HYERIM_DESC} crying on the floor in pure shock, messy long black hair. Emotional K-drama performance, soft HD resolution.",
    f"(Vertical 9:16) Two security guards in black suits moving luxury boxes and bags out of the apartment. Warm morning light, 2010s TV drama aesthetic.",
    f"(Vertical 9:16) {OKSUN_DESC} holding a gasoline jug with a cold face. Dim evening lighting in the living room, realistic shadows, 720p.",
    f"(Vertical 9:16) Extreme close-up of an old-style lighter's small orange flame ignited. Soft film grain, authentic texture, HD.",
    f"(Vertical 9:16) Realistic fire starting in the corner of the living room, consuming items. Soft orange glow on surroundings, 720p broadcast quality.",
    f"(Vertical 9:16) {HYERIM_DESC} screaming in the smoke, cinematic drama shot. Authentic despair expression, soft focus, natural skin, 720p.",
    f"(Vertical 9:16) Police officers in standard Korean police uniforms arriving at the apartment entrance. High tension incident, soft HD.",
    f"(Vertical 9:16) Dark cinematic shot. {OKSUN_DESC} whispering into the ear of {HYERIM_DESC} who is in handcuffs. Intense and calm, soft drama lighting.",
    f"(Vertical 9:16) Final shot. {OKSUN_DESC} sipping a glass of wine gracefully, fire glowing in the background. Epic 2010s Korean drama finale look, soft 720p."
]

def generate_image(prompt, index):
    filename = f"drama-natural-{index+1:02d}.png"
    output_path = OUTPUT_DIR / filename
    
    for token in HF_TOKENS:
        headers = {"Authorization": f"Bearer {token}"}
        print(f"🎨 Generating {filename} (Natural HD) using token starting with {token[:8]}...")
        
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
                    break
            except Exception as e:
                print(f"❌ Exception: {e}")
                time.sleep(2)
    return False

if __name__ == "__main__":
    print(f"🚀 Starting Natural HD Batch Generation ({len(PROMPTS)} images)")
    start_time = time.time()
    success_count = 0
    for i, prompt in enumerate(PROMPTS):
        if generate_image(prompt, i):
            success_count += 1
        time.sleep(1)
        
    elapsed = time.time() - start_time
    print(f"\n✨ Completed: {success_count}/{len(PROMPTS)} images.")
    print(f"⏱️ Total time: {elapsed:.2f} seconds.")
    print(f"📂 Location: {OUTPUT_DIR}")

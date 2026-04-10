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
OUTPUT_DIR = DOWNLOADS_DIR / "drama_scenes_hd_20"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# HD-grade Character consistency snippets (Typical Korean facial features, softer aesthetic)
OKSUN_DESC = "A typical 60s Korean mother-in-law, short permed gray-black hair, sharp but elegant Korean facial features, wearing a modest beige silk blouse and pearl necklace. Soft cinematic lighting, HD quality, natural skin texture."
HYERIM_DESC = "A glamorous 30s Korean woman, long black wavy hair, sophisticated but villainous Korean facial features, wearing a flashy designer red dress and heavy makeup. HD quality, natural skin texture."

PROMPTS = [
    f"(Vertical 9:16) Korean drama still. {OKSUN_DESC} is kneeling on a cold white marble floor in a penthouse. {HYERIM_DESC} stands over her, holding a luxury handbag. HD quality, natural lighting.",
    f"(Vertical 9:16) Close-up of {HYERIM_DESC}'s face looking down with a cruel sneer. Low angle shot, Korean drama aesthetic, HD.",
    f"(Vertical 9:16) Close-up of {OKSUN_DESC}'s eyes, filled with hidden strength and sharp intelligence. Soft cinematic lighting, HD.",
    f"(Vertical 9:16) {HYERIM_DESC} waving a legal document in front of Oksun's face mockingly. Luxury living room background, HD.",
    f"(Vertical 9:16) {HYERIM_DESC} forcefully grabbing {OKSUN_DESC}'s hand to press a red ink seal on a contract. Close-up on hands and faces, HD.",
    f"(Vertical 9:16) Dramatic reversal. {OKSUN_DESC}'s hand suddenly gripping Hyerim's wrist with incredible force. {HYERIM_DESC} looks shocked, HD.",
    f"(Vertical 9:16) {HYERIM_DESC}'s face showing intense pain and disbelief as her wrist is held. HD drama still.",
    f"(Vertical 9:16) {OKSUN_DESC} standing up with regal dignity, her wet hair slicked back elegantly. She towers over Hyerim. HD.",
    f"(Vertical 9:16) Dynamic action shot. {OKSUN_DESC} delivering a powerful slap to {HYERIM_DESC}'s face. Hair flying, movement blur, HD.",
    f"(Vertical 9:16) {OKSUN_DESC} standing tall, pointing a finger at a massive wall-mounted high-definition TV. Grand penthouse living room, HD.",
    f"(Vertical 9:16) Close-up of a giant TV screen showing evidence of infidelity and debt. Detailed surveillance footage on screen, HD.",
    f"(Vertical 9:16) {HYERIM_DESC} collapsing to the marble floor in pure horror while looking at the screen. HD quality.",
    f"(Vertical 9:16) Two security guards in black suits dumping dozens of expensive designer bags and dresses onto the floor. HD drama still.",
    f"(Vertical 9:16) {OKSUN_DESC} pouring gasoline from a red canister over the pile of luxury items. Cold, calm expression, HD.",
    f"(Vertical 9:16) Close-up of {OKSUN_DESC}'s hand flicking a silver lighter open, the small flame flickering. HD.",
    f"(Vertical 9:16) Intenes orange fire starting to consume the designer bags and dresses. Luxury penthouse background, HD.",
    f"(Vertical 9:16) {HYERIM_DESC} crying and screaming on the floor, trying to reach for a burning luxury bag. Chaotic scene, HD.",
    f"(Vertical 9:16) Security guards lifting {HYERIM_DESC} off the ground and dragging her toward the exit of the penthouse. Action shot, HD.",
    f"(Vertical 9:16) Police officers putting handcuffs on {HYERIM_DESC}. {OKSUN_DESC} leaning in close to whisper in her ear with a calm smile. HD.",
    f"(Vertical 9:16) Final shot. {OKSUN_DESC} sipping red wine from a glass, her back to the rising flames in the grand living room. Epic HD cinematic still."
]

def generate_image(prompt, index):
    filename = f"drama-hd-{index+1:02d}.png"
    output_path = OUTPUT_DIR / filename
    
    for token in HF_TOKENS:
        headers = {"Authorization": f"Bearer {token}"}
        print(f"🎨 Generating {filename} (HD) using token starting with {token[:8]}...")
        
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
    print(f"🚀 Starting HD Batch Generation ({len(PROMPTS)} images)")
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

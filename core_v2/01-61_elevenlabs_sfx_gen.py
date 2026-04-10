import os
import json
import requests
from pathlib import Path

# [Paths]
PROJ_ROOT = Path("/Users/a12/projects/tts")
CORE_V2 = PROJ_ROOT / "core_v2"
LIB_SFX_DIR = CORE_V2 / "Library" / "sfx"
CONFIG_PATH = PROJ_ROOT / "config.json"

def load_config():
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def generate_sfx(prompt, filename, duration_seconds=None):
    config = load_config()
    keys = [config.get("ElevenLabs_API_KEY"), config.get("ElevenLabs_API_KEY_2")]
    keys = [k for k in keys if k] # Filter out None
    
    if not keys:
        print("❌ No ElevenLabs API Key found in config.json")
        return False

    success = False
    for i, api_key in enumerate(keys):
        print(f"🎤 Generating SFX (Key {i+1}): '{prompt}' -> {filename}...")
        
        url = "https://api.elevenlabs.io/v1/sound-generation"
        headers = {
            "xi-api-key": api_key,
            "Content-Type": "application/json"
        }
        data = {
            "text": prompt
        }
        if duration_seconds:
            data["duration_seconds"] = duration_seconds

        try:
            response = requests.post(url, headers=headers, json=data)
            if response.status_code == 200:
                LIB_SFX_DIR.mkdir(parents=True, exist_ok=True)
                output_path = LIB_SFX_DIR / filename
                with open(output_path, "wb") as f:
                    f.write(response.content)
                print(f"✅ Successfully saved to: {output_path}")
                success = True
                break
            elif "quota_exceeded" in response.text:
                print(f"⚠️ Key {i+1} quota exceeded. Trying next key...")
                continue
            else:
                print(f"❌ API Error ({response.status_code}): {response.text}")
                continue
        except Exception as e:
            print(f"❌ Error with Key {i+1}: {e}")
            continue
            
    return success

if __name__ == "__main__":
    # Batch generation for current script
    sfx_to_generate = [
        ("A sharp, painful scream of a water deer (Gorani) in a snowy forest", "deer_scream_distress.mp3"),
        ("A loud, sharp metallic snap of a steel animal trap", "metal_trap_snap.mp3"),
        ("A mournful, wailing sound of an elderly Korean woman crying in deep sorrow", "old_woman_wailing.mp3"),
        ("A mean, greedy middle-aged man chuckling and laughing wickedly", "villain_laugh_mean.mp3"),
        ("The sound of rough hands digging in soil and pulling out thick plant roots", "dirt_digging_roots.mp3")
    ]
    
    for prompt, filename in sfx_to_generate:
        generate_sfx(prompt, filename)

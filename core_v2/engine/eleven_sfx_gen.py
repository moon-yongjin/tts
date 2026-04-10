import os
import requests
import json
import shutil
import time

# [설정]
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")
SFX_LIB_DIR = os.path.join(BASE_DIR, "Library", "sfx")
DOWNLOADS_DIR = os.path.join(os.path.expanduser("~"), "Downloads")
os.makedirs(SFX_LIB_DIR, exist_ok=True)

with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    config = json.load(f)
    API_KEY = config.get("ElevenLabs_API_KEY")

# 사용자 제공 리스트
samples = [
  { "filename": "impact_cinematic_boom.mp3", "text": "Deep, low-frequency cinematic sub-bass explosion", "duration_seconds": 3.0, "prompt_influence": 0.8 },
  { "filename": "impact_metal_hit.mp3", "text": "Heavy metal pipe hitting a concrete floor with reverb", "duration_seconds": 2.0, "prompt_influence": 0.9 },
  { "filename": "trans_fast_whoosh.mp3", "text": "Fast, high-pitched air whoosh for quick scene transition", "duration_seconds": 0.8, "prompt_influence": 0.7 },
  { "filename": "trans_glitch_static.mp3", "text": "Digital glitch and static noise for a tech-style transition", "duration_seconds": 1.5, "prompt_influence": 0.6 },
  { "filename": "impact_glass_shatter.mp3", "text": "Dramatic sound of a large window pane breaking", "duration_seconds": 3.0, "prompt_influence": 0.8 },
  { "filename": "impact_heartbeat_single.mp3", "text": "A single, isolated heavy heartbeat thud", "duration_seconds": 1.0, "prompt_influence": 0.9 },
  { "filename": "trans_magical_sparkle.mp3", "text": "Ascending magical harp and sparkle for a reveal", "duration_seconds": 2.5, "prompt_influence": 0.5 },
  { "filename": "impact_thunder_clapped.mp3", "text": "Sudden, loud crack of thunder with no rain", "duration_seconds": 4.0, "prompt_influence": 0.7 },
  { "filename": "impact_drum_roll.mp3", "text": "Suspenseful snare drum roll ending with a cymbal hit", "duration_seconds": 3.5, "prompt_influence": 0.6 },
  { "filename": "trans_paper_rip.mp3", "text": "Quick, aggressive sound of paper being torn in half", "duration_seconds": 1.0, "prompt_influence": 0.8 }
]

def generate():
    url = "https://api.elevenlabs.io/v1/sound-generation"
    headers = {
        "xi-api-key": API_KEY,
        "Content-Type": "application/json"
    }

    for item in samples:
        filename = item["filename"]
        text = item["text"]
        duration = item["duration_seconds"]
        influence = item["prompt_influence"]
        
        target_path = os.path.join(SFX_LIB_DIR, filename)
        
        # 중복 방지 체크
        if os.path.exists(target_path):
            # print(f"⏩ Skipping: {filename} (Already exists)")
            continue

        print(f"🚀 [ElevenLabs] Generating: {filename} ({duration}s)...")
        
        payload = {
            "text": text,
            "duration_seconds": duration,
            "prompt_influence": influence
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers)
            if response.status_code == 200:
                with open(target_path, "wb") as f:
                    f.write(response.content)
                
                # Copy to Downloads
                shutil.copy(target_path, os.path.join(DOWNLOADS_DIR, filename))
                print(f"✅ Created: {filename}")
                time.sleep(1) # 부하 방지
            elif response.status_code == 429:
                print(f"⚠️ Rate limited. Sleeping for 10s...")
                time.sleep(10)
                # 재시도는 다음 루프에서 (이번 턴은 실패 처리하거나 수동 재실행)
            else:
                print(f"❌ Error: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"❌ Exception: {e}")

if __name__ == "__main__":
    if not API_KEY:
        print("❌ Error: ElevenLabs API Key not found in config.json")
    else:
        generate()

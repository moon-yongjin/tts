import os
import shutil
import time
import json
from gradio_client import Client
from bgm_director import BGMusicProducer # Import our new Producer

# [Settings]
# SPACE_ID = "ACE-Step/Ace-Step-v1.5" # HF Space ID
SPACE_ID = "http://localhost:7860" # 로컬 서버 사용 (포트 7860)
HF_TOKEN = None
OUTPUT_DIR = "/Users/a12/Downloads/Toffee_AI_Producer_BGM"

def run_production(context, mood="Addictive & Rhythmic"):
    producer = BGMusicProducer()
    
    print(f"🧐 AI Producer analyze context: '{context}'...")
    composition = producer.compose_prompt(context, mood)
    
    if not composition:
        print("❌ Producer failed to compose.")
        return

    print(f"✨ Composition ready: {composition['explanation']}")
    
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    # Local connection setup
    try:
        client = Client(SPACE_ID)
        
        print(f"🎵 Generating music with ACE-Step...")
        result = client.predict(
            audio_duration=30,
            prompt=composition['tags'],
            lyrics=composition['xml_lyrics'],
            infer_step=60,
            guidance_scale=15.0,
            # ... other defaults ...
            api_name="/__call__"
        )
        
        audio_temp_path, parameters = result
        timestamp = int(time.time())
        final_path = os.path.join(OUTPUT_DIR, f"Producer_BGM_{timestamp}.mp3")
        
        shutil.move(audio_temp_path, final_path)
        print(f"✅ Production Complete! File: {final_path}")
        return final_path

    except Exception as e:
        print(f"❌ Generation Error: {e}")

if __name__ == "__main__":
    test_context = "A cheerful daily life short about cats playing with a yarn ball. Bright and energetic."
    run_production(test_context)

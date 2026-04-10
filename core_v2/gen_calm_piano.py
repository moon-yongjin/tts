import os
import shutil
import time
from gradio_client import Client

# [Settings] Tencent SongGeneration Hugging Face Space
SPACE_ID = "tencent/SongGeneration"
HF_TOKEN = "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"
OUTPUT_DIR = "/Users/a12/Downloads/ACE_Music_Results"

def generate_piano_music():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    
    print(f"🚀 [Tencent SongGen] Connecting to HF Space... ({SPACE_ID})")
    try:
        client = Client(SPACE_ID, token=HF_TOKEN)
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return

    # [Prompt] Calm Piano Solo
    description = "Calm, peaceful, emotional piano solo, slow tempo, high quality, soft touch, relaxing, melancholy yet beautiful."
    lyric = "[instrumental]"
    
    print(f"🎵 Generating 'Calm Piano Solo'...")
    print(f"   - Style: {description}")
    
    try:
        # API: predict(lyric, description, prompt_audio, genre, cfg_coef, temperature, api_name="/generate_song")
        result = client.predict(
            lyric=lyric,
            description=description,
            prompt_audio=None,
            genre="Soundtrack",
            cfg_coef=1.5,
            temperature=0.7,
            api_name="/generate_song"
        )
        
        if result is None or (isinstance(result, (list, tuple)) and result[0] is None):
            print("❌ Generation failed: Result is None. Server might be busy.")
            return

        # result: (generated_song_path, generated_info)
        audio_temp_path, info = result
        
        timestamp = int(time.time())
        final_filename = f"Calm_Piano_{timestamp}.mp3"
        final_path = os.path.join(OUTPUT_DIR, final_filename)
        
        shutil.move(audio_temp_path, final_path)
        print(f"✅ Success! File saved at: {final_path}")
        return final_path
        
    except Exception as e:
        print(f"❌ Error during generation: {e}")
        return None

if __name__ == "__main__":
    generate_piano_music()

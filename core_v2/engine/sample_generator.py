import os
import sys
import torch
import time
from audiocraft.models import AudioGen
from audiocraft.data.audio import audio_write
from pydub import AudioSegment

# [경로 설정]
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DOWNLOADS_DIR = os.path.join(os.path.expanduser("~"), "Downloads")
SFX_LIB_DIR = os.path.join(BASE_DIR, "Library", "sfx")
os.makedirs(SFX_LIB_DIR, exist_ok=True)

samples = [
    ("footsteps", "footsteps_1word"),
    ("clock", "clock_1word"),
    ("thunder", "thunder_1word"),
    ("sword", "sword_1word"),
    ("monster", "monster_1word"),
    ("leaves", "leaves_1word"),
    ("door", "door_1word"),
    ("magic", "magic_1word"),
    ("sizzle", "sizzle_1word"),
    ("breathing", "breathing_1word")
]

def generate():
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    print(f"📡 Loading AudioGen on {device}...")
    
    try:
        model = AudioGen.get_pretrained('facebook/audiogen-medium')
        model.set_generation_params(duration=5)
    except Exception as e:
        print(f"❌ Model loading failed: {e}")
        return

    for prompt, filename in samples:
        print(f"🚀 Generating: {prompt} -> {filename}.mp3")
        start = time.time()
        
        with torch.inference_mode():
            wav = model.generate([prompt])
            sample_rate = model.sample_rate
            
            temp_wav = os.path.join(SFX_LIB_DIR, f"{filename}_temp")
            audio_write(temp_wav, wav[0].cpu(), sample_rate, strategy="loudness", loudness_compressor=True)
            
            wav_path = f"{temp_wav}.wav"
            mp3_path = os.path.join(SFX_LIB_DIR, f"{filename}.mp3")
            
            # Convert to MP3
            audio = AudioSegment.from_wav(wav_path)
            audio.export(mp3_path, format="mp3", bitrate="192k")
            
            # Copy to Downloads
            import shutil
            shutil.copy(mp3_path, os.path.join(DOWNLOADS_DIR, f"{filename}.mp3"))
            
            if os.path.exists(wav_path):
                os.remove(wav_path)
                
        print(f"✅ Created: {filename}.mp3 (Took {time.time()-start:.1f}s)")

if __name__ == "__main__":
    generate()

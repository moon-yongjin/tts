import os
import shutil

base_path = os.path.expanduser("~/Downloads/Voice_Assets")
separated_path = os.path.join(base_path, "separated/htdemucs/voice_sample")

if os.path.exists(separated_path):
    # Move vocals
    old_vocals = os.path.join(separated_path, "vocals.wav")
    new_vocals = os.path.join(base_path, "voice_sample_clean.wav")
    if os.path.exists(old_vocals):
        shutil.move(old_vocals, new_vocals)
        print(f"Moved vocals to: {new_vocals}")
    
    # Move BGM
    old_bgm = os.path.join(separated_path, "no_vocals.wav")
    new_bgm = os.path.join(base_path, "bgm_only.wav")
    if os.path.exists(old_bgm):
        shutil.move(old_bgm, new_bgm)
        print(f"Moved BGM to: {new_bgm}")

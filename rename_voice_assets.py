import os
import shutil

dir_path = os.path.expanduser("~/Downloads/Voice_Assets")
for f in os.listdir(dir_path):
    if "정형석 성우" in f:
        old_path = os.path.join(dir_path, f)
        if f.endswith(".m4a"):
            new_path = os.path.join(dir_path, "voice_sample.m4a")
            shutil.move(old_path, new_path)
            print(f"Renamed to: {new_path}")
        elif f.endswith(".txt"):
            new_path = os.path.join(dir_path, "voice_sample.txt")
            shutil.move(old_path, new_path)
            print(f"Renamed to: {new_path}")

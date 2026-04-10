import os
import re

root = os.path.expanduser("~/projects/tts/core_v2")
for dirpath, _, filenames in os.walk(root):
    for f in filenames:
        if f.endswith(".py"):
            path = os.path.join(dirpath, f)
            try:
                with open(path, "r", encoding="utf-8") as file:
                    content = file.read()
                
                # Replace FFMPEG_EXE, FFPROBE_EXE, AudioSegment.converter assignments
                new_content = re.sub(r'FFMPEG_EXE\s*=\s*os\.path\.join\(.*?\)', 'FFMPEG_EXE = "ffmpeg"', content)
                new_content = re.sub(r'FFPROBE_EXE\s*=\s*os\.path\.join\(.*?\)', 'FFPROBE_EXE = "ffprobe"', new_content)
                new_content = re.sub(r'AudioSegment\.converter\s*=\s*os\.path\.join\(.*?\)', 'AudioSegment.converter = "ffmpeg"', new_content)
                
                if new_content != content:
                    with open(path, "w", encoding="utf-8") as file:
                        file.write(new_content)
                    print(f"Patched {path}")
            except Exception as e:
                print(f"Failed to patch {path}: {e}")

import os
import re
from pydub import AudioSegment

DOWNLOADS_DIR = os.path.join(os.path.expanduser("~"), "Downloads")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FFMPEG_EXE = "ffmpeg"
AudioSegment.converter = FFMPEG_EXE

def srt_time_to_ms(time_str):
    h, m, s_ms = time_str.split(':')
    s, ms = s_ms.split(',')
    return (int(h) * 3600 + int(m) * 60 + int(s)) * 1000 + int(ms)

def format_time_ms(ms):
    total_seconds = ms / 1000
    h = int(total_seconds // 3600)
    m = int((total_seconds % 3600) // 60)
    s = int(total_seconds % 60)
    ms_part = int(ms % 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms_part:03d}"

def final_merge():
    # Targets
    mp3s = [
        os.path.join(DOWNLOADS_DIR, "대본_0128_2101_Full_Merged.mp3"),
        os.path.join(DOWNLOADS_DIR, "대본_0128_2102_Full_Merged.mp3")
    ]
    srts = [
        os.path.join(DOWNLOADS_DIR, "대본_0128_2101_Full_Merged.srt"),
        os.path.join(DOWNLOADS_DIR, "대본_0128_2102_Full_Merged.srt")
    ]

    print("Merging Audio...")
    combined_audio = AudioSegment.empty()
    durations = []
    for m in mp3s:
        if os.path.exists(m):
            seg = AudioSegment.from_mp3(m)
            combined_audio += seg
            durations.append(len(seg))
        else:
            print(f"Missing: {m}")
            durations.append(0)

    output_base = "대본_0128_최종_통합"
    combined_audio.export(os.path.join(DOWNLOADS_DIR, f"{output_base}.mp3"), format="mp3", bitrate="192k")
    print(f"Saved: {output_base}.mp3")

    print("Merging Subtitles...")
    merged_srt = []
    srt_idx = 1
    offset = 0
    for i, s in enumerate(srts):
        if os.path.exists(s):
            with open(s, "r", encoding="utf-8-sig") as f:
                content = f.read().strip()
                blocks = re.split(r'\n\s*\n', content)
                for block in blocks:
                    lines = block.splitlines()
                    if len(lines) >= 3:
                        times = re.findall(r'(\d{2}:\d{2}:\d{2},\d{3})', lines[1])
                        if len(times) >= 2:
                            start_ms = srt_time_to_ms(times[0]) + offset
                            end_ms = srt_time_to_ms(times[1]) + offset
                            text = "\n".join(lines[2:])
                            merged_srt.append(f"{srt_idx}\n{format_time_ms(start_ms)} --> {format_time_ms(end_ms)}\n{text}\n\n")
                            srt_idx += 1
        
        offset += durations[i]

    with open(os.path.join(DOWNLOADS_DIR, f"{output_base}.srt"), "w", encoding="utf-8-sig") as f:
        f.writelines(merged_srt)
    print(f"Saved: {output_base}.srt")

if __name__ == "__main__":
    final_merge()

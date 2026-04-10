import os
import re
import datetime
from pydub import AudioSegment

DOWNLOADS_DIR = os.path.join(os.path.expanduser("~"), "Downloads")
FFMPEG_EXE = r"c:\Users\moori\.gemini\antigravity\scratch\tts\ffmpeg\ffmpeg-2026-01-07-git-af6a1dd0b2-essentials_build\bin\ffmpeg"
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

def force_merge():
    all_files = os.listdir(DOWNLOADS_DIR)
    # Find all part files from today (0128)
    part_files = [f for f in all_files if "_part" in f and "0128" in f]
    
    if not part_files:
        print("No part files found for 0128.")
        return

    # Sort by part number across all timestamps
    def get_part_num(name):
        match = re.search(r'part(\d+)', name)
        return int(match.group(1)) if match else 999

    mp3_files = sorted([f for f in part_files if f.endswith(".mp3")], key=get_part_num)
    srt_files = sorted([f for f in part_files if f.endswith(".srt")], key=get_part_num)

    print(f"Found {len(mp3_files)} MP3s and {len(srt_files)} SRTs to merge.")

    # Merge MP3
    combined_audio = AudioSegment.empty()
    part_durations = {}
    
    for f in mp3_files:
        print(f"Adding audio: {f}")
        seg = AudioSegment.from_mp3(os.path.join(DOWNLOADS_DIR, f))
        combined_audio += seg
        part_durations[get_part_num(f)] = len(seg)

    output_base = "대본_0128_Merged_Emergency"
    combined_audio.export(os.path.join(DOWNLOADS_DIR, f"{output_base}.mp3"), format="mp3", bitrate="192k")
    print(f"Saved: {output_base}.mp3")

    # Merge SRT
    merged_srt = []
    srt_idx = 1
    current_offset = 0
    
    # Track which parts we have SRT for
    srt_part_nums = [get_part_num(f) for f in srt_files]
    max_part = max(get_part_num(f) for f in mp3_files)

    for p in range(1, max_part + 1):
        # We need to know the duration of previous parts to set offset
        # Even if we don't have the SRT for a part, we must add its duration
        
        # Find if we have an srt for this part
        matching_srt = [f for f in srt_files if get_part_num(f) == p]
        
        if matching_srt:
            srt_file = matching_srt[0]
            print(f"Adding subtitles: {srt_file} at offset {current_offset/1000:.1f}s")
            with open(os.path.join(DOWNLOADS_DIR, srt_file), "r", encoding="utf-8-sig") as f:
                content = f.read().strip()
                blocks = re.split(r'\n\s*\n', content)
                for block in blocks:
                    lines = block.splitlines()
                    if len(lines) >= 3:
                        times = re.findall(r'(\d{2}:\d{2}:\d{2},\d{3})', lines[1])
                        if len(times) >= 2:
                            start_ms = srt_time_to_ms(times[0]) + current_offset
                            end_ms = srt_time_to_ms(times[1]) + current_offset
                            text = "\n".join(lines[2:])
                            merged_srt.append(f"{srt_idx}\n{format_time_ms(start_ms)} --> {format_time_ms(end_ms)}\n{text}\n\n")
                            srt_idx += 1
        else:
            print(f"Missing SRT for Part {p}, skipping text but keeping time.")

        # Increase offset by duration of part P
        if p in part_durations:
            current_offset += part_durations[p]
        else:
            print(f"Warning: Duration for part {p} unknown!")

    with open(os.path.join(DOWNLOADS_DIR, f"{output_base}.srt"), "w", encoding="utf-8-sig") as f:
        f.writelines(merged_srt)
    print(f"Saved: {output_base}.srt")

if __name__ == "__main__":
    force_merge()

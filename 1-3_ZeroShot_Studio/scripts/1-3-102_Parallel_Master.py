import os
import sys
import subprocess
import time
import math
from pathlib import Path

# [📂 Parallel Zero-Shot Master Controller]

대본_파일 = "/Users/a12/projects/tts/대본.txt"
출력_폴더 = Path("/Users/a12/Downloads")
VENV_PYTHON = "/Users/a12/projects/tts/qwen3-tts-apple-silicon/.venv/bin/python3"
SUB_GEN_SCRIPT = "/Users/a12/projects/tts/1-3-102_Sub_Generator.py"

VOICE_REF = "/Users/a12/projects/tts/reference_audio_3.wav"
VOICE_TEXT = "술 더 떠서 주민회 회장까지 한다는 것이었다. 또다시 전화와 인터폰을 왕래하느라 입맛이 떨어져 아침에 설친 그는 주민회 회장까지 한다는 것이었다."

LINES_PER_CHUNK = 8 # 8줄씩 끊어서 약 1분 내외 유지

def split_text_into_chunks(filepath, lines_limit):
    with open(filepath, "r", encoding="utf-8") as f:
        lines = [l.strip() for l in f.readlines() if l.strip()]

    chunks = []
    for i in range(0, len(lines), lines_limit):
        chunk = lines[i:i + lines_limit]
        chunks.append("\n".join(chunk))
    
    return chunks

from pydub import AudioSegment

def merge_results(chunk_files, final_wav, final_srt):
    combined = AudioSegment.empty()
    
    cumulative_offset = 0.0
    final_srt_content = []
    global_index = 1

    for i, wav in enumerate(chunk_files):
        if not os.path.exists(wav): continue
        
        chunk_seg = AudioSegment.from_wav(wav)
        duration = len(chunk_seg) / 1000.0
        combined += chunk_seg

        srt = wav.replace(".wav", ".srt")
        if os.path.exists(srt):
            with open(srt, "r", encoding="utf-8") as f:
                lines = f.readlines()
                
            for line in lines:
                if " --> " in line:
                    start, end = line.strip().split(" --> ")
                    # Shift time
                    s_h, s_m, s_s = start.replace(",", ".").split(":")
                    e_h, e_m, e_s = end.replace(",", ".").split(":")
                    
                    s_sec = float(s_h)*3600 + float(s_m)*60 + float(s_s) + cumulative_offset
                    e_sec = float(e_h)*3600 + float(e_m)*60 + float(e_s) + cumulative_offset
                    
                    def fmt(s):
                        h = int(s // 3600)
                        m = int((s % 3600) // 60)
                        sec = s % 60
                        return f"{h:02d}:{m:02d}:{sec:06.3f}".replace(".", ",")

                    line = f"{fmt(s_sec)} --> {fmt(e_sec)}\n"
                
                elif line.strip().isdigit():
                    line = f"{global_index}\n"
                    global_index += 1
                
                final_srt_content.append(line)
            
            final_srt_content.append("\n")

        cumulative_offset += duration

    combined.export(final_wav, format="wav")
    with open(final_srt, "w", encoding="utf-8") as f:
        f.writelines(final_srt_content)

def main():
    print("🔥 [Master] Sequential Chunked Generation (8-Line Mode)")
    chunks = split_text_into_chunks(대본_파일, LINES_PER_CHUNK)
    print(f"📦 Total Chunks: {len(chunks)}")

    temp_chunk_dir = Path("/tmp/tts_chunks")
    temp_chunk_dir.mkdir(exist_ok=True)

    chunk_wavs = []

    for i, chunk_text in enumerate(chunks):
        t_file = temp_chunk_dir / f"chunk_{i}.txt"
        w_file = temp_chunk_dir / f"chunk_{i}.wav"
        with open(t_file, "w", encoding="utf-8") as f:
            f.write(chunk_text)
        
        chunk_wavs.append(str(w_file))
        
        # Sequential Execution: One by one for stability
        cmd = [VENV_PYTHON, SUB_GEN_SCRIPT, str(t_file), VOICE_REF, VOICE_TEXT, str(w_file)]
        print(f"\n🔄 Processing Chunk {i+1}/{len(chunks)}...")
        subprocess.run(cmd)

    print("\n🔗 Merging all chunks...")
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    final_wav = 출력_폴더 / f"Parallel_Result_{timestamp}.wav"
    final_srt = 출력_폴더 / f"Parallel_Result_{timestamp}.srt"
    
    merge_results(chunk_wavs, str(final_wav), str(final_srt))

    print(f"\n✨ ALL DONE!")
    print(f"🔊 Audio: {final_wav}")
    print(f"📄 Subtitles: {final_srt}")

if __name__ == "__main__":
    main()

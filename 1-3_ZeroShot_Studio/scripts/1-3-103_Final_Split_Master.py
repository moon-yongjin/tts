import os
import sys
import subprocess
import time
from pathlib import Path
from pydub import AudioSegment

# [📂 Final Split Master V2: Dynamic Chunking & Full Engine Resets]

SOURCE_SCRIPT = "/Users/a12/projects/tts/대본.txt"
VENV_PYTHON = "/Users/a12/projects/tts/qwen3-tts-apple-silicon/.venv/bin/python3"
SUB_GEN_SCRIPT = "/Users/a12/projects/tts/1-3-102_Sub_Generator.py"
VOICE_REF = "/Users/a12/projects/tts/reference_audio_3.wav"
VOICE_TEXT = "술 더 떠서 주민회 회장까지 한다는 것이었다. 또다시 전화와 인터폰을 왕래하느라 입맛이 떨어져 아침에 설친 그는 주민회 회장까지 한다는 것이었다."
OUTPUT_FOLDER = Path("/Users/a12/Downloads")

CHUNK_SIZE = 7 # 🚀 사용자 지침: 7줄마다 엔진 리셋

def main():
    if not os.path.exists(SOURCE_SCRIPT):
        print(f"❌ Error: {SOURCE_SCRIPT} not found")
        return

    print(f"🔥 [Master] Dynamic Sequential Generation Started (Chunk Size: {CHUNK_SIZE})")
    
    with open(SOURCE_SCRIPT, "r", encoding="utf-8") as f:
        all_lines = [l.strip() for l in f.readlines() if l.strip()]

    chunks = [all_lines[i : i + CHUNK_SIZE] for i in range(0, len(all_lines), CHUNK_SIZE)]
    print(f"📦 Total sentences: {len(all_lines)} -> Total chunks: {len(chunks)}")

    temp_wavs = []
    
    for i, chunk_lines in enumerate(chunks):
        # 1. Create temporary script for this chunk
        temp_script = f"/tmp/chunk_{i}.txt"
        with open(temp_script, "w", encoding="utf-8") as f:
            f.write("\n".join(chunk_lines))
        
        out_wav = f"/tmp/final_chunk_{i}.wav"
        temp_wavs.append(out_wav)
        
        # 2. [🚀 CRITICAL] Run SEPARATE PROCESS for 100% Engine Initialization
        cmd = [VENV_PYTHON, SUB_GEN_SCRIPT, temp_script, VOICE_REF, VOICE_TEXT, out_wav]
        print(f"\n🔄 [Reset {i+1}/{len(chunks)}] Processing {len(chunk_lines)} lines...")
        subprocess.run(cmd)

    # 3. Merging results
    combined_audio = AudioSegment.empty()
    final_srt_content = []
    cumulative_offset = 0.0
    global_index = 1

    print("\n🔗 [Merging] Combining results...")
    for wav in temp_wavs:
        if not os.path.exists(wav): continue
        
        seg = AudioSegment.from_wav(wav)
        duration = len(seg) / 1000.0
        combined_audio += seg

        srt = wav.replace(".wav", ".srt")
        if os.path.exists(srt):
            with open(srt, "r", encoding="utf-8") as f:
                lines = f.readlines()
            for line in lines:
                if " --> " in line:
                    start, end = line.strip().split(" --> ")
                    s_h, s_m, s_s = start.replace(",", ".").split(":")
                    e_h, e_m, e_s = end.replace(",", ".").split(":")
                    s_sec = float(s_h)*3600 + float(s_m)*60 + float(s_s) + cumulative_offset
                    e_sec = float(e_h)*3600 + float(e_m)*60 + float(e_s) + cumulative_offset
                    
                    def fmt(s):
                        h = int(s // 3600)
                        m = int((s % 3600) // 60)
                        return f"{h:02d}:{m:02d}:{s%60:06.3f}".replace(".", ",")
                        
                    line = f"{fmt(s_sec)} --> {fmt(e_sec)}\n"
                elif line.strip().isdigit():
                    line = f"{global_index}\n"
                    global_index += 1
                final_srt_content.append(line)
            final_srt_content.append("\n")
        cumulative_offset += duration

    timestamp = time.strftime("%Y%m%d_%G%M%S")
    res_wav = OUTPUT_FOLDER / f"Dynamic_Result_{timestamp}.wav"
    res_srt = OUTPUT_FOLDER / f"Dynamic_Result_{timestamp}.srt"
    
    combined_audio.export(res_wav, format="wav")
    with open(res_srt, "w", encoding="utf-8") as f:
        f.writelines(final_srt_content)

    print(f"\n✨ DONE! Final production output saved to Downloads:")
    print(f"   🔈 Audio: {res_wav.name}")
    print(f"   📜 Subtitles: {res_srt.name}")

if __name__ == "__main__":
    main()

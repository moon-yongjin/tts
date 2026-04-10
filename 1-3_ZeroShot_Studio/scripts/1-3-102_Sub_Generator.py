import os
import sys
import re
import json
import time
import datetime
from pathlib import Path
import mlx.core as mx
from mlx_audio.tts import load
import numpy as np
import soundfile as sf
import librosa
from pydub import AudioSegment
from pydub.silence import detect_leading_silence

# [📂 Parallel Sub-Generator: Individual Chunk Worker]

# Defaults (Can be overridden by Master)
PROJECT_ROOT = Path("/Users/a12/projects/tts/qwen3-tts-apple-silicon")
MODEL_PATH = PROJECT_ROOT / "models/Qwen3-TTS-12Hz-1.7B-Base-8bit"
sys.path.append(str(PROJECT_ROOT))

def trim_silence(audio, threshold=-50.0, padding_ms=150):
    start_trim = detect_leading_silence(audio, silence_threshold=threshold)
    end_trim = detect_leading_silence(audio.reverse(), silence_threshold=threshold)
    duration = len(audio)
    trimmed = audio[start_trim:max(start_trim+1, duration-end_trim)]
    silence = AudioSegment.silent(duration=padding_ms)
    return silence + trimmed.fade_out(100) + silence

def normalize_text(text):
    text = text.replace('“', '"').replace('”', '"').replace('‘', "'").replace('’', "'")
    text = text.replace('"', '').replace("'", "")
    text = text.replace('. ', '.').replace('.', '.. ') 
    text = text.replace("외양간", "외양깐").replace("땅바닥", "땅빠닥").replace("임명장", "임명짱").replace("코방귀", "콧방귀")
    
    # Sino-Korean
    sino_map = {'1':'일','2':'이','3':'삼','4':'사','5':'오','6':'육','7':'칠','8':'팔','9':'구','10':'십','20':'이십'}
    text = re.sub(r'(\d+)(년|위|일|부|편|달러|원|분)', 
                  lambda m: sino_map.get(m.group(1), m.group(1)) + m.group(2), text)
    
    # Native Korean
    native_map = {'1':'한','2':'두','3':'세','4':'네','5':'다섯','6':'여섯','7':'일곱','8':'여덟','9':'아홉','10':'열',
                  '11':'열한','12':'열두','20':'스무'}
    text = re.sub(r'(\d+)(시|살|번|명|개)', 
                  lambda m: native_map.get(m.group(1), m.group(1)) + m.group(2), text)
    
    text = text.replace(" 10 ", " 열 ").replace(" 20 ", " 스무 ").replace(" 10.", " 열.").replace(" 20.", " 스무.")
    return text

def format_srt_time(seconds):
    td = datetime.timedelta(seconds=seconds)
    hours = int(td.total_seconds()) // 3600
    minutes = (int(td.total_seconds()) % 3600) // 60
    secs = int(td.total_seconds()) % 60
    millis = int(td.microseconds / 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

def main():
    if len(sys.argv) < 5:
        print("Usage: python 1-3-102_Sub_Generator.py [chunk_text_path] [ref_audio_path] [ref_text] [output_wav_path]")
        return

    chunk_file = sys.argv[1]
    ref_audio = sys.argv[2]
    ref_text = sys.argv[3]
    output_wav = sys.argv[4]
    output_srt = output_wav.replace(".wav", ".srt")

    print(f"🚀 [Sub-Gen] Starting chunk: {chunk_file}")
    
    model = load(str(MODEL_PATH))

    with open(chunk_file, "r", encoding="utf-8") as f:
        lines = [l.strip() for l in f.readlines() if l.strip()]

    combined_audio = AudioSegment.empty()
    srt_entries = []
    current_time = 0.0

    for i, line in enumerate(lines):
        orig_line = line
        norm_line = normalize_text(line)
        print(f"🎙️ Generating [{i+1}/{len(lines)}]: {norm_line[:30]}...")

        # Generation
        audio_out = model.generate(norm_line, ref_audio=ref_audio, ref_text=ref_text, speed=1.1)
        
        # Handle Output
        if hasattr(audio_out, '__iter__') and not hasattr(audio_out, '__len__'):
             parts = [np.array(a.audio if hasattr(a, 'audio') else a) for a in audio_out]
             audio_array = np.concatenate([p.reshape(1) if p.ndim == 0 else p for p in parts])
        elif hasattr(audio_out, 'audio'):
             audio_array = np.array(audio_out.audio)
        else:
             audio_array = np.array(audio_out)

        temp_wav = f"{output_wav}_temp_{i}.wav"
        sf.write(temp_wav, audio_array.astype(np.float32).flatten(), 24000)
        
        segment = trim_silence(AudioSegment.from_wav(temp_wav))
        duration = len(segment) / 1000.0

        # SRT Entry
        start_time = format_srt_time(current_time)
        end_time = format_srt_time(current_time + duration)
        srt_entries.append(f"{i+1}\n{start_time} --> {end_time}\n{orig_line}\n")

        combined_audio += segment
        current_time += duration
        
        if os.path.exists(temp_wav): os.remove(temp_wav)

    # Export Results
    combined_audio.export(output_wav, format="wav")
    with open(output_srt, "w", encoding="utf-8") as f:
        f.write("\n".join(srt_entries))

    print(f"✅ Chunk Completed: {output_wav}")

if __name__ == "__main__":
    main()

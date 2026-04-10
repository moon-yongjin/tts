import os
import sys
import re
import json
import datetime
import tempfile
from pathlib import Path

import mlx.core as mx
import numpy as np
import soundfile as sf
import librosa
from pydub import AudioSegment
from pydub.silence import detect_leading_silence

# Force load from sys path
PROJ_ROOT = Path("/Users/a12/projects/tts")
MLX_DIR = PROJ_ROOT / "qwen3-tts-apple-silicon"
sys.path.append(str(MLX_DIR))
sys.path.append(str(MLX_DIR / ".venv/lib/python3.14/site-packages"))

import mlx.core as mx
import numpy as np
import soundfile as sf
import librosa
from pydub import AudioSegment
from pydub.silence import detect_leading_silence

from mlx_audio.tts import load

# Settings
CATALOG_PATH = PROJ_ROOT / "core_v2/voice_catalog.json"
MODEL_PATH = MLX_DIR / "models/Qwen3-TTS-12Hz-1.7B-Base-8bit"
TARGET_SCRIPT_PATH = PROJ_ROOT / "대본.txt"
OUTPUT_DIR = Path.home() / "Downloads"

def trim_silence(audio, threshold=-50.0, padding_ms=150):
    start_trim = detect_leading_silence(audio, silence_threshold=threshold)
    end_trim = detect_leading_silence(audio.reverse(), silence_threshold=threshold)
    duration = len(audio)
    trimmed = audio[start_trim:max(start_trim+1, duration-end_trim)]
    silence = AudioSegment.silent(duration=padding_ms)
    return silence + trimmed.fade_out(100) + silence

def normalize_text(text):
    text = text.replace('“', '"').replace('”', '"').replace('‘', "'").replace('’', "'")
    text = text.replace('"', '').replace("'", "").replace('.', ',')
    return text

def format_srt_time(seconds):
    td = datetime.timedelta(seconds=seconds)
    total_seconds = int(td.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60
    millis = int(td.microseconds / 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

def split_chunks(text, max_chars=120):
    lines = text.splitlines()
    final_chunks = []
    for line in lines:
        line = line.strip()
        if not line: continue
        sentences = re.findall(r'[^,!?\s][^,!?\n]*[,!?\n]*', line)
        current_chunk = ""
        for s in sentences:
            if len(current_chunk) + len(s) + 1 <= max_chars:
                current_chunk = (current_chunk + " " + s).strip()
            else:
                if current_chunk: final_chunks.append(current_chunk)
                current_chunk = s
        if current_chunk: final_chunks.append(current_chunk)
    return [c.strip() for c in final_chunks if c.strip()]

def generate_voice(character_id):
    print(f"🎙️ [Universal TTS] Character: {character_id}")
    
    with open(CATALOG_PATH, "r", encoding="utf-8") as f:
        catalog = json.load(f)
    
    if character_id not in catalog:
        print(f"❌ '{character_id}' is not in voice_catalog.json")
        return

    char_data = catalog[character_id]
    ref_audio_path = char_data["ref_audio"]
    ref_text = char_data["ref_text"]

    print(f"🚀 Loading Model...")
    model = load(str(MODEL_PATH))

    with open(TARGET_SCRIPT_PATH, "r", encoding="utf-8") as f:
        script_text = f.read().strip()
    
    script_text = normalize_text(script_text)
    chunks = split_chunks(script_text)

    # Load Ref
    ref_wav, sr = librosa.load(ref_audio_path, sr=24000)
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        sf.write(tmp.name, ref_wav, sr)
        temp_ref_path = tmp.name

    combined_audio = AudioSegment.empty()
    srt_entries = []
    current_time_sec = 0.0
    PAUSE_MS = 600

    for i, chunk in enumerate(chunks):
        print(f"🎙️  [{i+1}/{len(chunks)}] {chunk[:30]}...")
        results = model.generate(text=chunk, ref_audio=temp_ref_path, ref_text=ref_text, language="Korean")
        segment_audio_mx = None
        for res in results:
            segment_audio_mx = res.audio if segment_audio_mx is None else mx.concatenate([segment_audio_mx, res.audio])
        
        if segment_audio_mx is not None:
            audio_np = np.array(segment_audio_mx)
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as stmp:
                sf.write(stmp.name, audio_np, 24000)
                stmp_path = stmp.name
            
            segment_pydub = trim_silence(AudioSegment.from_wav(stmp_path))
            os.unlink(stmp_path)
            
            duration_sec = len(segment_pydub) / 1000.0
            srt_entries.append(f"{i+1}\n{format_srt_time(current_time_sec)} --> {format_srt_time(current_time_sec + duration_sec)}\n{chunk}\n\n")
            combined_audio += segment_pydub + AudioSegment.silent(duration=PAUSE_MS)
            current_time_sec += duration_sec + (PAUSE_MS / 1000.0)

    if len(combined_audio) > 0:
        output_filename = f"Universal_{character_id}_{datetime.datetime.now().strftime('%H%M%S')}"
        output_path = OUTPUT_DIR / f"{output_filename}.wav"
        combined_audio.export(str(output_path), format="wav")
        with open(str(output_path).replace(".wav", ".srt"), "w", encoding="utf-8-sig") as f:
            f.writelines(srt_entries)
        print(f"✅ Created: {output_path}")

    os.unlink(temp_ref_path)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--character", type=str, required=True, help="Character ID from voice_catalog.json")
    args = parser.parse_args()
    generate_voice(args.character)

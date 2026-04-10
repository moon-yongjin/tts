import os
import sys
import re
from pathlib import Path
import datetime

# 1. 경로 설정
PROJECT_ROOT = Path("/Users/a12/projects/tts/qwen3-tts-apple-silicon")
sys.path.append(str(PROJECT_ROOT)) 
sys.path.append("/Users/a12/projects/tts/qwen3-tts-apple-silicon/.venv/lib/python3.14/site-packages")

import mlx.core as mx
from mlx_audio.tts import load
import numpy as np
import soundfile as sf
import librosa
import tempfile
from pydub import AudioSegment
from pydub.silence import detect_leading_silence

# 1. 모델 경로
MODEL_PATH = PROJECT_ROOT / "models/Qwen3-TTS-12Hz-1.7B-Base-8bit"

# 2. 데이터 설정 (사용자 확정 동생 보이스 레퍼런스)
REF_AUDIO = "/Users/a12/projects/tts/references/Sister_Fixed_Ref.wav"
REF_TEXT = "에구구... 소리가 절로 납니다. 굽은 허리를 펴기도 전에 무릎에서 우드득 소리가 납니다."

# [대상] 생성할 대본
TARGET_SCRIPT_PATH = Path("/Users/a12/projects/tts/대본.txt")
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
    text = text.replace('"', '').replace("'", "")
    
    # 발음 교정
    text = text.replace("푼돈", "푼똔")
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
        sentences = re.findall(r'[^.!?,\s][^.!?,\n]*[.!?,\n]*', line)
        current_chunk = ""
        for s in sentences:
            s = s.strip()
            if not s: continue
            if len(current_chunk) + len(s) + 1 <= max_chars:
                current_chunk = (current_chunk + " " + s) if current_chunk else s
            else:
                if current_chunk: final_chunks.append(current_chunk)
                current_chunk = s
        if current_chunk: final_chunks.append(current_chunk)
    return [c.strip() for c in final_chunks if c.strip()]

def main():
    print("🎙️ Zero-Shot Voice Clone [FIXED SISTER MODE]")
    model = load(str(MODEL_PATH))
    with open(TARGET_SCRIPT_PATH, "r", encoding="utf-8") as f:
        target_text = f.read().strip()
    
    target_text = normalize_text(target_text)
    chunks = split_chunks(target_text)
    
    # 레퍼런스 로딩 (앞부분 8초 활용)
    ref_wav, sr = librosa.load(REF_AUDIO, sr=24000, duration=8.0)
    
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        sf.write(tmp.name, ref_wav, sr)
        temp_ref_path = tmp.name

    combined_audio = AudioSegment.empty()
    srt_entries = []
    current_time_sec = 0.0
    PAUSE_MS = 500 

    for i, chunk in enumerate(chunks):
        print(f"🎙️  [{i+1}/{len(chunks)}] {chunk[:30]}...")
        results = model.generate(text=chunk, ref_audio=temp_ref_path, ref_text=REF_TEXT, language="Korean")
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
        output_name = f"ZeroShot_FixedSister_{datetime.datetime.now().strftime('%H%M%S')}"
        output_path = OUTPUT_DIR / f"{output_name}.wav"
        combined_audio.export(str(output_path), format="wav")
        with open(str(output_path).replace(".wav", ".srt"), "w", encoding="utf-8-sig") as f:
            f.writelines(srt_entries)
        print(f"✅ 완료: {output_path}")
    os.unlink(temp_ref_path)

if __name__ == "__main__":
    main()

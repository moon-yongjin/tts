import os
import sys
import re
from pathlib import Path
import mlx.core as mx
from mlx_audio.tts import load
import numpy as np
import soundfile as sf
import librosa
import tempfile
from pydub import AudioSegment
from pydub.silence import detect_leading_silence
import datetime

# 1. 경로 설정
PROJECT_ROOT = Path("/Users/a12/projects/tts/qwen3-tts-apple-silicon")
MODEL_PATH = PROJECT_ROOT / "models/Qwen3-TTS-12Hz-1.7B-Base-8bit"
sys.path.append(str(PROJECT_ROOT))

# 2. 데이터 설정 (사용자 확정: 장영란 시어머니 보이스 레퍼런스)
REF_AUDIO = "/Users/a12/projects/tts/references/MIL_Real_Ref.wav"
REF_TEXT = "와, 근데 진짜 요즘 경기가 너무 안 좋다. 가게 장사 진짜 안 되네."

# [대상] 생성할 대본
TARGET_SCRIPT_PATH = Path("/Users/a12/projects/tts/대본.txt")
OUTPUT_DIR = Path.home() / "Downloads"

def trim_silence(audio, threshold=-50.0, padding_ms=150):
    """음성 앞뒤 침묵 제거 및 끝부분 페이드 아웃 처리"""
    start_trim = detect_leading_silence(audio, silence_threshold=threshold)
    end_trim = detect_leading_silence(audio.reverse(), silence_threshold=threshold)
    duration = len(audio)
    trimmed = audio[start_trim:max(start_trim+1, duration-end_trim)]
    
    silence = AudioSegment.silent(duration=padding_ms)
    return silence + trimmed.fade_out(100) + silence

def normalize_text(text):
    """TTS 발음 교정"""
    text = text.replace('“', '"').replace('”', '"').replace('‘', "'").replace('’', "'")
    text = text.replace('"', '').replace("'", "")
    
    # 발음 교정
    text = text.replace("푼돈", "푼똔")
    text = text.replace("목돈", "목똔")
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
    print("🎙️ Zero-Shot Voice Clone [REAL MIL MODE]")
    if not os.path.exists(REF_AUDIO):
        print(f"❌ 레퍼런스 오디오 없음: {REF_AUDIO}")
        return

    model = load(str(MODEL_PATH))
    with open(TARGET_SCRIPT_PATH, "r", encoding="utf-8") as f:
        target_text = f.read().strip()
    
    target_text = normalize_text(target_text)
    chunks = split_chunks(target_text)
    
    ref_wav, sr = librosa.load(REF_AUDIO, sr=24000)
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
        output_name = f"ZeroShot_RealMIL_{datetime.datetime.now().strftime('%H%M%S')}"
        output_path = OUTPUT_DIR / f"{output_name}.wav"
        combined_audio.export(str(output_path), format="wav")
        with open(str(output_path).replace(".wav", ".srt"), "w", encoding="utf-8-sig") as f:
            f.writelines(srt_entries)
        print(f"✅ 완료: {output_path}")
    os.unlink(temp_ref_path)

if __name__ == "__main__":
    main()

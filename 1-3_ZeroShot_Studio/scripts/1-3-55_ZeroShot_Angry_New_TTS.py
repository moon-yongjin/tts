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

# 2. 데이터 설정 (분노 목소리 레퍼런스)
REF_AUDIO = "/Users/a12/Downloads/extracted_assets/Speaking_angrily_in_korean_22b571a676/Speaking_angrily_in_korean_22b571a676_vocals.wav"
REF_TEXT = "뭐 계약을 끝내 어디 깩촌해서 전화 사기라도 치는 거야 웃기시네. 웃기시네 경찰에 신고하기 전에 얼른."

# [대상] 생성할 대본
TARGET_SCRIPT_PATH = Path("/Users/a12/projects/tts/대본.txt")
OUTPUT_DIR = Path.home() / "Downloads"

def trim_silence(audio, threshold=-50.0):
    start_trim = detect_leading_silence(audio, silence_threshold=threshold)
    end_trim = detect_leading_silence(audio.reverse(), silence_threshold=threshold)
    duration = len(audio)
    return audio[start_trim:duration-end_trim]

def format_srt_time(seconds):
    td = datetime.timedelta(seconds=seconds)
    total_seconds = int(td.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60
    millis = int(td.microseconds / 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

def split_chunks(text, max_chars=120):
    sentences = re.split(r'([.!?,\n]\s*)', text)
    chunks = []
    current = ""
    for p in sentences:
        if len(current) + len(p) <= max_chars:
            current += p
        else:
            if current: chunks.append(current.strip())
            current = p
    if current: chunks.append(current.strip())
    return [c for c in chunks if c]

def main():
    print("==========================================")
    print("🎙️ Qwen3-TTS [MLX] Zero-Shot Angry Voice (1-3-55)")
    print("==========================================")

    if not MODEL_PATH.exists():
        print(f"❌ 모델을 찾을 수 없습니다: {MODEL_PATH}")
        return
    
    with open(TARGET_SCRIPT_PATH, "r", encoding="utf-8") as f:
        target_text = f.read().strip()
    
    chunks = split_chunks(target_text)
    print(f"📄 총 {len(chunks)}개의 파트로 대본 처리 시작...")

    print(f"🚀 MLX 베이스 모델 로딩 중: {MODEL_PATH.name}...")
    model = load(str(MODEL_PATH))

    print("🎧 레퍼런스 오디오 로딩 중 (6초 설정)...")
    ref_wav, sr = librosa.load(REF_AUDIO, sr=24000, duration=6.0)
    
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        sf.write(tmp.name, ref_wav, sr)
        temp_ref_path = tmp.name

    combined_audio = AudioSegment.empty()
    srt_entries = []
    current_time_sec = 0.0
    PAUSE_MS = 400 

    for i, chunk in enumerate(chunks):
        print(f"🎙️  [{i+1}/{len(chunks)}] 생성 중: {chunk[:30]}...")
        
        results = model.generate(
            text=chunk,
            ref_audio=temp_ref_path,
            ref_text=REF_TEXT[:80], 
            language="Korean",
            temperature=0.75,
            top_p=0.85
        )

        segment_audio_mx = None
        for res in results:
            if segment_audio_mx is None:
                segment_audio_mx = res.audio
            else:
                segment_audio_mx = mx.concatenate([segment_audio_mx, res.audio])
        
        if segment_audio_mx is not None:
            audio_np = np.array(segment_audio_mx)
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as stmp:
                sf.write(stmp.name, audio_np, 24000)
                stmp_path = stmp.name
            
            segment_pydub = AudioSegment.from_wav(stmp_path)
            os.unlink(stmp_path)
            segment_pydub = trim_silence(segment_pydub)
            
            duration_sec = len(segment_pydub) / 1000.0
            srt_entries.append(f"{i+1}\n{format_srt_time(current_time_sec)} --> {format_srt_time(current_time_sec + duration_sec)}\n{chunk}\n\n")
            
            combined_audio += segment_pydub + AudioSegment.silent(duration=PAUSE_MS)
            current_time_sec += duration_sec + (PAUSE_MS / 1000.0)

    if len(combined_audio) > 0:
        timestamp = os.popen("date +%H%M%S").read().strip()
        output_path = OUTPUT_DIR / f"AngryVoice_ZeroShot_1-3-55_{timestamp}.wav"
        combined_audio.export(str(output_path), format="wav")
        
        srt_path = str(output_path).replace(".wav", ".srt")
        with open(srt_path, "w", encoding="utf-8-sig") as f:
            f.writelines(srt_entries)
        
        print(f"\n✅ 생성 완료! {output_path}")
        os.unlink(temp_ref_path)
    else:
        print("⚠️ 음성 생성 실패")

if __name__ == "__main__":
    main()

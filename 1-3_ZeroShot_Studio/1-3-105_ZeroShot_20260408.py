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
import subprocess

# 1. 경로 설정
PROJECT_ROOT = Path("/Users/a12/projects/tts/qwen3-tts-apple-silicon")
MODEL_PATH = PROJECT_ROOT / "models/Qwen3-TTS-12Hz-1.7B-Base-8bit"
sys.path.append(str(PROJECT_ROOT))

TARGET_SCRIPT_PATH = Path("/Users/a12/projects/tts/대본.txt")
OUTPUT_DIR = Path.home() / "Downloads"

# 2. 음성 설정 (260408_084840_신규)
SELECTED_VOICE = {
    "name": "260408_084840_신규",
    "file": "/Users/a12/projects/tts/1-3_ZeroShot_Studio/voices/Reference/260408_084840_ref.wav",
    "text": "안녕하세요 요즘에 오토이스크 안 돼서 곤란해하시는 분들 많으시죠?",
    "speed": 1.0
}

def trim_silence(audio, threshold=-50.0, padding_ms=200):
    start_trim = detect_leading_silence(audio, silence_threshold=threshold)
    duration = len(audio)
    trimmed = audio[start_trim:duration] 
    silence = AudioSegment.silent(duration=padding_ms)
    return silence + trimmed.fade_out(80) + silence

def normalize_text(text):
    text = text.replace('“', '"').replace('”', '"').replace('‘', "'").replace('’', "'")
    text = text.replace('"', '').replace("'", "")
    text = text.replace('. ', '.').replace('.', '.. ')
    return text

def format_srt_time(seconds):
    td = datetime.timedelta(seconds=seconds)
    hours = int(td.total_seconds()) // 3600
    minutes = (int(td.total_seconds()) % 3600) // 60
    secs = int(td.total_seconds()) % 60
    millis = int(td.microseconds / 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

def split_chunks(text, max_chars=200):
    text = text.replace('\r\n', '\n').replace('\n\n', ' _DOUBLE_BREAK_ ')
    text = text.replace('\n', ' ')
    blocks = text.split(' _DOUBLE_BREAK_ ')
    final_chunks = []
    for block in blocks:
        block = block.strip()
        if not block: continue
        sentences = re.findall(r'[^,!?\s][^,!?\n]*[,!?\n]*', block)
        native_units = r'(살|명|개(?!월)|시|마리|권|쪽|장)'
        current_chunk = ""
        for s in sentences:
            s = s.strip()
            if not s: continue
            if len(current_chunk) + len(s) + 1 <= max_chars:
                current_chunk = (current_chunk + " " + s).strip()
            else:
                if current_chunk: final_chunks.append(current_chunk)
                current_chunk = s
        if current_chunk: final_chunks.append(current_chunk)
    return [c.strip() for c in final_chunks if c.strip()]

def main():
    print("\n==========================================")
    print(f"🎙️ Qwen3-TTS [단독 생성 모드: {SELECTED_VOICE['name']}]")
    print("==========================================")

    if not TARGET_SCRIPT_PATH.exists():
        print(f"❌ 대본 파일이 없습니다: {TARGET_SCRIPT_PATH}")
        return

    with open(TARGET_SCRIPT_PATH, "r", encoding="utf-8") as f:
        target_text = f.read().strip()

    print(f"\n📄 대본 전처리 중... (총 {len(target_text)}자)")
    target_text = normalize_text(target_text)
    chunks = split_chunks(target_text)
    print(f"📄 총 {len(chunks)}개의 파트로 대본 처리 시작...")

    print(f"\n🚀 모델 로딩 중...")
    model = load(str(MODEL_PATH))

    combined_audio = AudioSegment.empty()
    srt_entries = []
    current_time_sec = 0.0
    PAUSE_MS = 500 

    try:
        for i, chunk in enumerate(chunks):
            print(f"🎙️  [{i+1}/{len(chunks)}] 생성 중: {chunk[:40]}...")
            
            results = model.generate(
                text=chunk,
                ref_audio=SELECTED_VOICE["file"],
                ref_text=SELECTED_VOICE["text"], 
                language="Korean",
                temperature=0.8,
                top_p=0.9,
                speed=SELECTED_VOICE["speed"]
            )

            segment_audio_mx = None
            for res in results:
                if segment_audio_mx is None: segment_audio_mx = res.audio
                else: segment_audio_mx = mx.concatenate([segment_audio_mx, res.audio])
            
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
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            output_name = f"ZeroShot_20260408_결과물_{timestamp}.wav"
            output_path = OUTPUT_DIR / output_name
            combined_audio.export(str(output_path), format="wav")
            
            srt_path = str(output_path).replace(".wav", ".srt")
            with open(srt_path, "w", encoding="utf-8-sig") as f: f.writelines(srt_entries)
            
            print(f"\n✅ 음성 생성 완료: {output_path}")

            # 자막 분할 후작업
            sub_split_script = "/Users/a12/projects/tts/core_v2/04_srt_subsplitter.py"
            if os.path.exists(sub_split_script):
                 print("\n✂️ 자막 분할 후작업 진행 중...")
                 subprocess.run([sys.executable, sub_split_script])

    except Exception as e:
        print(f"❌ 에러 발생: {str(e)}")

if __name__ == "__main__":
    main()

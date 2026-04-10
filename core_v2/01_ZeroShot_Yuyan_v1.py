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
TARGET_SCRIPT_PATH = Path("/Users/a12/projects/tts/대본.txt")
OUTPUT_DIR = Path.home() / "Downloads"

# 2. 데이터 설정 (Yuyan 레퍼런스)
REF_AUDIO = "/Users/a12/projects/tts/voices/Reference_Audios/vo_CYCOP001_1902501_yuyan_09.wav"
REF_TEXT = "응, 하지만 동생을 잘 돌봐줘야 해, 엄마는 할 일이 남았으니까 이따가 올게"

def trim_silence(audio, threshold=-50.0, padding_ms=150):
    if len(audio) < 10: return audio
    try:
        start_trim = detect_leading_silence(audio, silence_threshold=threshold)
        end_trim = detect_leading_silence(audio.reverse(), silence_threshold=threshold)
        duration = len(audio)
        trimmed = audio[start_trim:max(start_trim+1, duration-end_trim)]
        silence = AudioSegment.silent(duration=padding_ms)
        return silence + trimmed.fade_out(100) + silence
    except: return audio

def number_to_korean(num_str):
    num_str = num_str.replace(',', '')
    if not num_str.isdigit(): return num_str
    try: num = int(num_str)
    except: return num_str
    if num == 0: return "영"
    units = ["", "십", "백", "천"]
    large_units = ["", "만", "억", "조", "경"]
    digits = ["", "일", "이", "삼", "사", "오", "육", "칠", "팔", "구"]
    result = ""
    str_num = str(num)
    for i, d in enumerate(str_num):
        digit = int(d)
        if digit != 0:
            pos = len(str_num) - 1 - i
            result += digits[digit] + units[pos % 4]
        if (len(str_num)-1-i) > 0 and (len(str_num)-1-i) % 4 == 0:
            large_pos = (len(str_num)-1-i) // 4
            if any(int(x) > 0 for x in str_num[max(0, i-3):i+1]):
                if not result.endswith(large_units[large_pos]): result += large_units[large_pos]
    if result.startswith("일십"): result = result[1:]
    return result

def normalize_text(text):
    # 인용부호 통일 및 마침표를 쉼표로 치환 (MLX 피치 드롭 잡음 방지)
    text = text.replace('“', '"').replace('”', '"').replace('‘', "'").replace('’', "'")
    text = text.replace('.', ',')
    return text

def normalize_numbers(text):
    return re.sub(r'\d+(?:,\d+)*', lambda m: number_to_korean(m.group(0)), text)

def format_srt_time(seconds):
    td = datetime.timedelta(seconds=seconds)
    return f"{int(td.total_seconds())//3600:02d}:{(int(td.total_seconds())%3600)//60:02d}:{int(td.total_seconds())%60:02d},{int(td.microseconds / 1000):03d}"

def split_chunks(text, max_chars=110):
    lines = text.splitlines()
    final_chunks = []
    for line in lines:
        line = line.strip()
        if not line: continue
        sentences = re.findall(r'[^.!?,\s][^.!?,\n]*[.!?,\n]*', line)
        current_chunk = ""
        for s in sentences:
            if len(current_chunk) + len(s.strip()) + 1 <= max_chars: current_chunk = (current_chunk + " " + s.strip()).strip()
            else:
                if current_chunk: final_chunks.append(current_chunk)
                current_chunk = s.strip()
        if current_chunk: final_chunks.append(current_chunk)
    return [c.strip() for c in final_chunks if c.strip()]

def main():
    print("==========================================")
    print("🎙️ Qwen3-TTS [MLX] Zero-Shot Yuyan V1")
    print("==========================================")

    if not TARGET_SCRIPT_PATH.exists():
        print(f"❌ 대본 파일 없음: {TARGET_SCRIPT_PATH}"); return

    with open(TARGET_SCRIPT_PATH, "r", encoding="utf-8") as f:
        target_text = f.read().strip()
    
    target_text = normalize_text(target_text)
    target_text = normalize_numbers(target_text)
    chunks = split_chunks(target_text)
    print(f"📄 총 {len(chunks)}개의 파트로 대본 처리 시작...")

    print(f"\n🚀 모델 로딩 중...")
    model = load(str(MODEL_PATH))

    if not os.path.exists(REF_AUDIO):
        print(f"⚠️ 레퍼런스 오디오 없음: {REF_AUDIO}"); return

    print(f"🎧 레퍼런스 로드 중: {REF_AUDIO}")
    ref_wav, sr = librosa.load(REF_AUDIO, sr=24000)
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        sf.write(tmp.name, ref_wav, sr)
        temp_ref_path = tmp.name

    combined_audio = AudioSegment.empty()
    srt_entries = []
    current_time_sec = 0.0
    PAUSE_MS = 400 

    for i, chunk in enumerate(chunks):
        tts_chunk = chunk.replace('"', '').replace("'", "")
        print(f"🎙️  [{i+1}/{len(chunks)}] 생성 중: {tts_chunk[:40]}...")
        
        try:
            results = model.generate(text=tts_chunk, ref_audio=temp_ref_path, ref_text=REF_TEXT[:100], language="Korean")
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
        except Exception as e: print(f"❌ 생성 에러: {str(e)}")

    if len(combined_audio) > 0:
        timestamp = datetime.datetime.now().strftime("%H%M%S")
        output_path = OUTPUT_DIR / f"Yuyan_ZeroShot_{timestamp}.wav"
        combined_audio.export(str(output_path), format="wav")
        with open(str(output_path).replace(".wav", ".srt"), "w", encoding="utf-8-sig") as f: f.writelines(srt_entries)
        print(f"\n✅ 작업 완료: {output_path}")
        os.unlink(temp_ref_path)
    else: print("\n⚠️ 생성 실패")

if __name__ == "__main__": main()

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

# 2. 데이터 설정 (유라/Eula 새로운 레퍼런스)
REF_AUDIO = "/Users/a12/Downloads/레퍼3/vo_YQEQ206_6_eula_04.wav"
REF_TEXT = "괜찮아, 가면서 보면 되지. 언니들이 도와줄게"

# Eula 캐릭터 스타일 지침 (Elegant, Noble, Slightly Cold)
STYLE_INSTRUCT = "Elegant, noble, and slightly cold aristocratic female tone."

# [대상] 생성할 대본
TARGET_SCRIPT_PATH = Path("/Users/a12/projects/tts/대본.txt")
OUTPUT_DIR = Path.home() / "Downloads"

def number_to_korean(num_str):
    num_str = num_str.replace(',', '')
    if not num_str.isdigit(): return num_str
    try: num = int(num_str)
    except ValueError: return num_str
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
            unit_pos = pos % 4
            large_unit_pos = pos // 4
            digit_str = digits[digit]
            if unit_pos > 0 and digit == 1: digit_str = ""
            result += digit_str + units[unit_pos]
        if (len(str_num) - 1 - i) > 0 and (len(str_num) - 1 - i) % 4 == 0:
            if large_unit_pos > 0 and any(int(x) > 0 for x in str_num[max(0, i-3):i+1]):
                 if not result.endswith(large_units[large_unit_pos]): result += large_units[large_unit_pos]
    if result.startswith("일십"): result = result[1:]
    # 사용자의 요청에 의해 '일백', '일천' 이 유지되기를 원할 수 있으므로 탈락 구문을 주석처리 하거나 제거합니다.
    # if result.startswith("일백"): result = result[1:]
    # if result.startswith("일천"): result = result[1:]
    return result

def normalize_numbers(text):
    pattern = r'\d+(?:,\d+)*'
    return re.sub(pattern, lambda m: number_to_korean(m.group(0)), text)

def trim_silence(audio, threshold=-50.0, padding_ms=250):
    """음성 앞뒤 침묵 제거 및 끝부분 여유분 확보"""
    start_trim = detect_leading_silence(audio, silence_threshold=threshold)
    end_trim = max(0, detect_leading_silence(audio.reverse(), silence_threshold=threshold) - 100)
    
    duration = len(audio)
    trimmed = audio[start_trim:max(start_trim+1, duration-end_trim)]
    
    silence = AudioSegment.silent(duration=padding_ms)
    return silence + trimmed.fade_out(50) + silence

def normalize_text(text):
    text = text.replace('%', ' 퍼센트')
    text = text.replace('“', '"').replace('”', '"').replace('‘', "'").replace('’', "'")
    text = text.replace('"', '').replace("'", "")
    return text.strip()

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
    print("🎙️ Qwen3-TTS [MLX] Eula Zero-Shot (v2 - New Ref)")
    print("   Character: Eula (유라)")
    print("   Reference Text: " + REF_TEXT)
    print("==========================================")

    if not os.path.exists(REF_AUDIO):
        print(f"❌ 레퍼런스 오디오가 없습니다: {REF_AUDIO}")
        return

    if not TARGET_SCRIPT_PATH.exists():
        print(f"❌ 대본 파일이 없습니다: {TARGET_SCRIPT_PATH}")
        return

    with open(TARGET_SCRIPT_PATH, "r", encoding="utf-8") as f:
        full_text = f.read()

    # 숫자 및 특수문자 정규화 피어 연동
    full_text = full_text.replace('%', ' 퍼센트')
    full_text = normalize_numbers(full_text)

    print("⏳ 모델 로드 중...")
    model = load(str(MODEL_PATH))
    print("✅ 모델 로드 완료")

    print("🎧 레퍼런스 오디오 가공 중...")
    ref_wav, sr = librosa.load(REF_AUDIO, sr=24000)
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        sf.write(tmp.name, ref_wav, sr)
        temp_ref_path = tmp.name

    chunks = split_chunks(full_text)
    print(f"📦 총 {len(chunks)}개의 단락으로 분할됨")

    combined_audio = AudioSegment.empty()
    srt_entries = []
    current_time_sec = 0.0
    PAUSE_MS = 300

    for i, chunk in enumerate(chunks):
        cleaned_text = normalize_text(chunk)
        if not cleaned_text.endswith(('.', '!', '?', ',')):
            cleaned_text += "."

        print(f"[{i+1}/{len(chunks)}] 생성 중: {cleaned_text[:50]}...")
        
        results = model.generate(
            text=cleaned_text,
            ref_audio=temp_ref_path,
            ref_text=REF_TEXT,
            language="Korean",
            instruct=STYLE_INSTRUCT,
            temperature=0.7,
            top_p=0.8,
            repetition_penalty=1.1
        )

        segment_wavs = []
        for res in results:
            segment_wavs.append(res.audio)
        
        if not segment_wavs:
            print(f"⚠️ [{i+1}/{len(chunks)}] 생성 실패")
            continue

        audio_np = np.concatenate(segment_wavs)

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as stmp:
            sf.write(stmp.name, audio_np, 24000)
            segment_pydub = AudioSegment.from_wav(stmp.name)
            os.unlink(stmp.name)

        segment_pydub = trim_silence(segment_pydub)
        duration_sec = len(segment_pydub) / 1000.0

        # 단순 자막 엔트리 생성
        start_t = format_srt_time(current_time_sec)
        end_t = format_srt_time(current_time_sec + duration_sec)
        srt_entries.append(f"{len(srt_entries)+1}\n{start_t} --> {end_t}\n{chunk}\n\n")

        combined_audio += segment_pydub + AudioSegment.silent(duration=PAUSE_MS)
        current_time_sec += duration_sec + (PAUSE_MS / 1000.0)

    timestamp = datetime.datetime.now().strftime("%y%m%d_%H%M")
    base_name = f"Eula_v2_{timestamp}"
    wav_path = OUTPUT_DIR / f"{base_name}.wav"
    srt_path = OUTPUT_DIR / f"{base_name}.srt"

    combined_audio.export(wav_path, format="wav")
    with open(srt_path, "w", encoding="utf-8-sig") as f:
        f.writelines(srt_entries)

    print("\n" + "="*40)
    print(f"🎉 'Eula v2' 생성 완료!")
    print(f"🔊 음성: {wav_path}")
    print(f"📝 자막: {srt_path}")
    print("="*40)
    
    os.unlink(temp_ref_path)

if __name__ == "__main__":
    main()

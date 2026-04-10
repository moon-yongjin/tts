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

# 2. 데이터 설정 (**스크린 녹화** 목소리 레퍼런스 적용)
REF_AUDIO = "/Users/a12/projects/tts/voices/Reference_Audios/extracted_ref.wav"

# Whisper로 자동 추출된 해당 영상의 실제 대사 대본입니다.
REF_TEXT = "아하는 거 아니야 이거잖아 이거 이거 이거 이거 최소 이렇게 주문할게 우리 라인 비워나 우리 라인의 다른 손이 봐지마 아 이렇게 내가 못 팔면 내가 책임지게 무조건 이 일었기를 만들주미만 해놔 두 총 9000개 만들주미만 해놔 아니 그거는 우리 길에 나눠 먹고 안 된대"

# [대상] 생성할 대본
TARGET_SCRIPT_PATH = Path("/Users/a12/projects/tts/대본.txt")
OUTPUT_DIR = Path.home() / "Downloads"

# 3. 발음 교정 사전
PRONUNCIATION_DICT = {
    "팔도": "팔또",
}

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
    length = len(str_num)

    for i, d in enumerate(str_num):
        digit = int(d)
        if digit != 0:
            pos = length - 1 - i
            unit_pos = pos % 4
            large_unit_pos = pos // 4
            digit_str = digits[digit]
            if unit_pos > 0 and digit == 1: digit_str = ""
            result += digit_str + units[unit_pos]
        pos = length - 1 - i
        if pos > 0 and pos % 4 == 0:
            if large_unit_pos > 0 and any(int(x) > 0 for x in str_num[max(0, i-3):i+1]):
                 if not result.endswith(large_units[large_unit_pos]): result += large_units[large_unit_pos]

    if result.startswith("일십"): result = result[1:]
    if result.startswith("일백"): result = result[1:]
    if result.startswith("일천"): result = result[1:]
    return result

def normalize_numbers(text):
    pattern = r'\d+(?:,\d+)*'
    def replacer(match): return number_to_korean(match.group(0))
    return re.sub(pattern, replacer, text)

def apply_pronunciation_rules(text):
    text = normalize_numbers(text)
    for old, new in PRONUNCIATION_DICT.items():
        text = text.replace(old, new)
    return text

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
                if current_chunk: current_chunk += " " + s
                else: current_chunk = s
            else:
                if current_chunk: final_chunks.append(current_chunk)
                current_chunk = s
        if current_chunk: final_chunks.append(current_chunk)
    return [c.strip() for c in final_chunks if c.strip()]

def main():
    print("==========================================")
    print("🎙️ Qwen3-TTS [MLX] Zero-Shot ScreenRecording (V3)")
    print("==========================================")

    if not MODEL_PATH.exists():
        print(f"❌ 모델을 찾을 수 없습니다: {MODEL_PATH}")
        return
    
    if not TARGET_SCRIPT_PATH.exists():
        print(f"❌ 대본 파일을 찾을 수 없습니다: {TARGET_SCRIPT_PATH}")
        return

    with open(TARGET_SCRIPT_PATH, "r", encoding="utf-8") as f:
        target_text = f.read().strip()
    
    chunks = split_chunks(target_text)
    print(f"📄 총 {len(chunks)}개의 파트로 대본 처리 시작...")

    print(f"\n🚀 MLX 베이스 모델 로딩 중: {MODEL_PATH.name}...")
    model = load(str(MODEL_PATH))

    print("🎧 레퍼런스 오디오 로딩 중...")
    if not os.path.exists(REF_AUDIO):
        print(f"⚠️ 레퍼런스 오디오가 없습니다: {REF_AUDIO}")
        return

    ref_wav, sr = librosa.load(REF_AUDIO, sr=24000, duration=6.0)
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        sf.write(tmp.name, ref_wav, sr)
        temp_ref_path = tmp.name

    combined_audio = AudioSegment.empty()
    srt_entries = []
    current_time_sec = 0.0
    PAUSE_MS = 400 

    success_count = 0
    fail_count = 0

    for i, chunk in enumerate(chunks):
        print(f"🎙️  [{i+1}/{len(chunks)}] 생성 중: {chunk[:40]}...")
        
        try:
            pronun_chunk = apply_pronunciation_rules(chunk)
            results = model.generate(
                text=pronun_chunk,
                ref_audio=temp_ref_path,
                ref_text=REF_TEXT[:80],  # 레퍼런스 텍스트 주입
                language="Korean",
                temperature=0.75,
                top_p=0.85
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
                srt_entries.append(f"{success_count+1}\n{format_srt_time(current_time_sec)} --> {format_srt_time(current_time_sec + duration_sec)}\n{chunk}\n\n")
                
                combined_audio += segment_pydub + AudioSegment.silent(duration=PAUSE_MS)
                current_time_sec += duration_sec + (PAUSE_MS / 1000.0)
                success_count += 1
            else: fail_count += 1
        except Exception as e:
            print(f"❌ 에러 발생: {str(e)}")
            fail_count += 1

    if len(combined_audio) > 0:
        timestamp = os.popen("date +%H%M%S").read().strip()
        output_path = OUTPUT_DIR / f"ScreenShotVoice_ZeroShot_V3_{timestamp}.wav"
        combined_audio.export(str(output_path), format="wav")
        
        srt_path = str(output_path).replace(".wav", ".srt")
        with open(srt_path, "w", encoding="utf-8-sig") as f: f.writelines(srt_entries)
        print(f"\n✅ 작업 완료! ({success_count}개 성공) -> {output_path}")
        os.unlink(temp_ref_path)
    else:
        print("\n⚠️ 음성 생성 실패")

if __name__ == "__main__":
    main()

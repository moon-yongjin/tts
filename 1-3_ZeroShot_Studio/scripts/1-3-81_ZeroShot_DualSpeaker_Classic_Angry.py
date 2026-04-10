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

# 2. 데이터 설정
# [레퍼런스 1] 클래식언니 (나레이션 전용)
REF_AUDIO_CLASSIC = "/Users/a12/projects/tts/voices/Reference_Videos/ClassicUnni_Ref.mp4"
REF_TEXT_CLASSIC = "안녕하세요, 오늘 전해드릴 소식은 유튜브 화면 녹화 영상을 기반으로 한 인공지능 음성 복제 기술입니다."

# [레퍼런스 2] 분노 목소리 (따옴표 대사 전용)
REF_AUDIO_ANGRY = "/Users/a12/projects/tts/voices/Reference_Audios/Speaking_angrily_in_korean_22b571a676_vocals.wav"
REF_TEXT_ANGRY = "뭐 계약을 끝내 어디 깩촌해서 전화 사기라도 치는 거야 웃기시네. 웃기시네 경찰에 신고하기 전에 얼른."

# 🚀 [추가] 분노 목소리 예비 경로 백업 구조
REF_AUDIO_ANGRY_FALLBACK = "/Users/a12/Downloads/extracted_assets/Speaking_angrily_in_korean_22b571a676/Speaking_angrily_in_korean_22b571a676_vocals.wav"

# [대상] 생성할 대본
TARGET_SCRIPT_PATH = Path("/Users/a12/projects/tts/대본.txt")
OUTPUT_DIR = Path.home() / "Downloads"



# ------------------------------------------------------------------
# [유틸] 숫자 한글 발음 치환기 (Number Normalizer)
# ------------------------------------------------------------------
def number_to_korean(num_str):
    num_str = num_str.replace(',', '')
    if not num_str.isdigit(): return num_str
    try: num = int(num_str)
    except: return num_str
    if num == 0: return "영"
    units = ["", "십", "백", "천"]; large_units = ["", "만", "억", "조", "경"]
    digits = ["", "일", "이", "삼", "사", "오", "육", "칠", "팔", "구"]
    result = ""; str_num = str(num); length = len(str_num)
    for i, d in enumerate(str_num):
        digit = int(d)
        if digit != 0:
            pos = length - 1 - i; unit_pos = pos % 4; large_unit_pos = pos // 4
            digit_str = digits[digit]
            if unit_pos > 0 and digit == 1: digit_str = ""
            result += digit_str + units[unit_pos]
        pos = length - 1 - i
        if pos > 0 and pos % 4 == 0:
            if large_unit_pos > 0 and any(int(x) > 0 for x in str_num[max(0, length - (large_unit_pos+1)*4) : length - large_unit_pos*4]):
                 if not result.endswith(large_units[large_unit_pos]): result += large_units[large_unit_pos]
    if result.startswith("일십"): result = result[1:]
    if result.startswith("일백"): result = result[1:]
    if result.startswith("일천"): result = result[1:]
    return result

def normalize_text(text):
    pattern = r'\d+(?:,\d+)*'
    text = re.sub(pattern, lambda m: number_to_korean(m.group(0)), text)
    text = text.replace('. ', '.').replace('.', '.. ')
    return text

def trim_silence(audio, threshold=-50.0, padding_ms=100):
    start_trim = detect_leading_silence(audio, silence_threshold=threshold)
    end_trim = detect_leading_silence(audio.reverse(), silence_threshold=threshold)
    duration = len(audio)
    trimmed = audio[start_trim:max(start_trim+1, duration-end_trim)]
    silence = AudioSegment.silent(duration=padding_ms)
    return silence + trimmed.fade_out(80) + silence

def format_srt_time(seconds):
    td = datetime.timedelta(seconds=seconds)
    hours = int(td.total_seconds()) // 3600
    minutes = (int(td.total_seconds()) % 3600) // 60
    secs = int(td.total_seconds()) % 60
    millis = int(td.microseconds / 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

# ------------------------------------------------------------------
# [핵심] 듀얼 스피커용 자막/텍스트 분할기
# ------------------------------------------------------------------
def split_by_narrator_and_quotes(text):
    text = text.replace('“', '"').replace('”', '"')
    parts = re.split(r'("[^"]*")', text)
    results = []
    for part in parts:
        part = part.strip()
        if not part: continue
        is_quote = part.startswith('"')
        clean_text = part.replace('"', '').strip()
        if clean_text:
            results.append({
                "text": clean_text,
                "is_quote": is_quote
            })
    return results

def main():
    print("==========================================")
    print("🎙️ 듀얼 스피커 TTS [나레이션(Classic) + 따옴표(Angry)]")
    print("==========================================")

    if not TARGET_SCRIPT_PATH.exists():
        print(f"❌ 대본 파일이 없습니다: {TARGET_SCRIPT_PATH}"); return

    with open(TARGET_SCRIPT_PATH, "r", encoding="utf-8") as f:
        target_text = f.read().strip()
    
    parts = split_by_narrator_and_quotes(target_text)
    print(f"📄 총 {len(parts)}개의 음성 세그먼트 탐지되었습니다.")

    print(f"\n🚀 MLX 베이스 모델 로딩 중...")
    model = load(str(MODEL_PATH))

    # 🚀 레퍼런스 가공 1: 클래식언니
    print("🎧 클래식언니 레퍼런스 오디오 로딩 중...")
    if not os.path.exists(REF_AUDIO_CLASSIC):
        print(f"⚠️ 클래식언니 오디오가 없습니다: {REF_AUDIO_CLASSIC}"); return
    ref_wav_c, sr_c = librosa.load(REF_AUDIO_CLASSIC, sr=24000)
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_c:
        sf.write(tmp_c.name, ref_wav_c, sr_c)
        path_classic = tmp_c.name

    # 🚀 레퍼런스 가공 2: 분노목소리 (백업 경로 포함 기동)
    print("🎧 분노목소리 레퍼런스 오디오 로딩 중...")
    angry_target = REF_AUDIO_ANGRY if os.path.exists(REF_AUDIO_ANGRY) else REF_AUDIO_ANGRY_FALLBACK
    if not os.path.exists(angry_target):
        print(f"⚠️ 분노목소리 오디오가 없습니다."); return
    
    ref_wav_a, sr_a = librosa.load(angry_target, sr=24000, duration=6.0)
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_a:
        sf.write(tmp_a.name, ref_wav_a, sr_a)
        path_angry = tmp_a.name

    combined_audio = AudioSegment.empty()
    srt_entries = []
    current_time_sec = 0.0
    PAUSE_MS = 400 

    success_count = 0

    for i, item in enumerate(parts):
        chunk = item["text"]
        is_quote = item["is_quote"]
        norm_chunk = normalize_text(chunk)

        if is_quote:
            print(f"🎙️  [{i+1}/{len(parts)}] [대사] 생성: {norm_chunk[:30]}...")
            ref_path = path_angry
            ref_txt = REF_TEXT_ANGRY
        else:
            print(f"🎙️  [{i+1}/{len(parts)}] [나레이션] 생성: {norm_chunk[:30]}...")
            ref_path = path_classic
            ref_txt = REF_TEXT_CLASSIC

        try:
            results = model.generate(
                text=norm_chunk,
                ref_audio=ref_path,
                ref_text=ref_txt[:80], 
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
        except Exception as e:
            print(f"❌ 에러 발생: {str(e)}")

    if len(combined_audio) > 0:
        timestamp = datetime.datetime.now().strftime("%H%M%S")
        output_path = OUTPUT_DIR / f"Dual_Classic_Angry_{timestamp}.wav"
        combined_audio.export(str(output_path), format="wav")
        
        srt_path = str(output_path).replace(".wav", ".srt")
        with open(srt_path, "w", encoding="utf-8-sig") as f: f.writelines(srt_entries)
        print(f"\n✅ 듀얼 보이스 생성 완료! -> {output_path}")
    else:
        print("\n⚠️ 음성 생성 실패")

    try: os.unlink(path_classic); os.unlink(path_angry)
    except: pass

if __name__ == "__main__":
    main()

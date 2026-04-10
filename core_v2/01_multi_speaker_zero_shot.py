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

# 2. 스피커 설정
SPEAKERS = {
    "male": {
        "name": "남자목소리(스크린녹화)",
        "ref_audio": "/Users/a12/projects/tts/voices/Reference_Audios/V4_ScreenRecording_20260316_173013.wav",
        "ref_text": "17년을 살았던 집에서 옥가방 하나 들고 쫓겨놨습니다. 남편은 교통사고로 먼저 갔어요. 시아버지마저 지병으로 돌아",
        "speed": 1.0,  # 이미 자연스럽게 빠름
        "temp": 0.75,
        "top_p": 0.85
    },
    "female": {
        "name": "클래식언니",
        "ref_audio": "/Users/a12/projects/tts/voices/Reference_Videos/ClassicUnni_Ref.mp4",
        "ref_text": "안녕하세요, 오늘 전해드릴 소식은 유튜브 화면 녹화 영상을 기반으로 한 인공지능 음성 복제 기술입니다.",
        "speed": 1.0,  # 기본 속도 유지
        "temp": 0.8,
        "top_p": 0.9
    }
}

def trim_silence(audio, threshold=-50.0, padding_ms=150):
    start_trim = detect_leading_silence(audio, silence_threshold=threshold)
    end_trim = detect_leading_silence(audio.reverse(), silence_threshold=threshold)
    duration = len(audio)
    trimmed = audio[start_trim:max(start_trim+1, duration-end_trim)]
    silence = AudioSegment.silent(duration=padding_ms)
    return silence + trimmed.fade_out(100) + silence

def normalize_text(text):
    # 인용부호 통일
    text = text.replace('“', '"').replace('”', '"').replace('‘', "'").replace('’', "'")
    text = text.replace('.', ',')
    text = text.replace("외양간", "외양깐").replace("땅바닥", "땅빠닥").replace("팔도", "팔또")
    return text

# ✅ 한국어 숫자 변환 사전 및 처리함수 (V3 바이블 필수)
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
    if result.startswith("일백"): result = result[1:]
    if result.startswith("일천"): result = result[1:]
    return result

def normalize_numbers(text):
    pattern = r'\d+(?:,\d+)*'
    return re.sub(pattern, lambda m: number_to_korean(m.group(0)), text)

def format_srt_time(seconds):
    td = datetime.timedelta(seconds=seconds)
    total_seconds = int(td.total_seconds())
    return f"{total_seconds//3600:02d}:{(total_seconds%3600)//60:02d}:{total_seconds%60:02d},{int(td.microseconds / 1000):03d}"

def split_chunks_with_speaker(text, max_chars=110):
    # 1. 인용부호 통일 (normalize_text 에서 이미 처리했으나 한 번 더 보급)
    text = text.replace('“', '"').replace('”', '"').replace('‘', "'").replace('’', "'")
    
    # 2. 정규식으로 따옴표 덩어리("\".*?\"") 격리 분할
    raw_parts = re.split(r'(\".*?\")', text)
    
    results = []
    for p in raw_parts:
        if not p: continue
        p = p.strip()
        if not p: continue
        
        # 따옴표 덩어리 -> 클래식언니 (female)
        if p.startswith('"') and p.endswith('"'):
            clean_text = p.strip('"').strip()
            if clean_text:
                results.append((clean_text, "female"))
        else:
            # 일반 지문 -> 남자목소리 (male)
            # 문장 단위( . ! ? )로 분할하여 max_chars에 맞게 묶음
            sentences = re.findall(r'[^.!?,\s][^.!?,\n]*[.!?,\n]*', p)
            current_chunk = ""
            for s in sentences:
                s = s.strip()
                if not s: continue
                if len(current_chunk) + len(s) + 1 <= max_chars:
                    current_chunk = (current_chunk + " " + s).strip()
                else:
                    if current_chunk: results.append((current_chunk, "male"))
                    current_chunk = s
            if current_chunk:
                results.append((current_chunk, "male"))
                
    return results

def main():
    print("==========================================")
    print("🎙️ Qwen3-TTS [MLX] Multi-Speaker (남자/ClassicUnni)")
    print("==========================================")

    if not TARGET_SCRIPT_PATH.exists():
        print(f"❌ 대본 파일이 없습니다: {TARGET_SCRIPT_PATH}")
        return

    with open(TARGET_SCRIPT_PATH, "r", encoding="utf-8") as f:
        target_text = f.read().strip()
    
    target_text = normalize_text(target_text)
    target_text = normalize_numbers(target_text)
    chunks_with_speaker = split_chunks_with_speaker(target_text)
    print(f"📄 총 {len(chunks_with_speaker)}개의 파트 분배 완료.")

    print(f"\n🚀 모델 로딩 중...")
    model = load(str(MODEL_PATH))

    # 레퍼런스 검증 및 사전 가공 (WAV 형식 로드 보급)
    speaker_ref_paths = {}
    for spk_id, config in SPEAKERS.items():
        if not os.path.exists(config["ref_audio"]):
             print(f"⚠️ {config['name']} 레퍼런스 오디오 누락: {config['ref_audio']}")
             return
        print(f"🎧 {config['name']} 오디오 로드 중...")
        ref_wav, sr = librosa.load(config["ref_audio"], sr=24000)
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            sf.write(tmp.name, ref_wav, sr)
            speaker_ref_paths[spk_id] = tmp.name

    combined_audio = AudioSegment.empty()
    srt_entries = []
    current_time_sec = 0.0
    PAUSE_MS = 400 

    for i, (chunk, spk) in enumerate(chunks_with_speaker):
        config = SPEAKERS[spk]
        # 모델 주입 전 따옴표 물리적 제거 (잡음 감소)
        tts_chunk = chunk.replace('"', '').replace("'", "")
        
        print(f"🎙️  [{i+1}/{len(chunks_with_speaker)}] ({config['name']}) 생성 중: {tts_chunk[:40]}...")
        
        try:
            results = model.generate(
                text=tts_chunk,
                ref_audio=speaker_ref_paths[spk],
                ref_text=config["ref_text"][:100], 
                language="Korean",
                temperature=config["temp"],
                top_p=config["top_p"]
            )

            segment_audio_mx = None
            for res in results:
                if segment_audio_mx is None: segment_audio_mx = res.audio
                else: segment_audio_mx = mx.concatenate([segment_audio_mx, res.audio])
            
            if segment_audio_mx is not None:
                audio_np = np.array(segment_audio_mx)
                
                # 🚀 클래식언니의 경우 물리적 1.4배속 가공
                if config["speed"] != 1.0:
                    audio_np = librosa.effects.time_stretch(audio_np, rate=config["speed"])
                
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
        except Exception as e:
            print(f"❌ 생성 에러 ({chunk[:15]}): {str(e)}")

    if len(combined_audio) > 0:
        timestamp = datetime.datetime.now().strftime("%H%M%S")
        output_path = OUTPUT_DIR / f"MultiSpeaker_ZeroShot_{timestamp}.wav"
        combined_audio.export(str(output_path), format="wav")
        
        with open(str(output_path).replace(".wav", ".srt"), "w", encoding="utf-8-sig") as f: 
            f.writelines(srt_entries)
        
        print(f"\n✅ 멀티스피커 생성 완료: {output_path}")
        for path in speaker_ref_paths.values(): os.unlink(path)
    else: print("\n⚠️ 생성 실패")

if __name__ == "__main__":
    main()

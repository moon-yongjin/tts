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

# 2. 데이터 설정 (클래식언니 레퍼런스)
REF_AUDIO = "/Users/a12/projects/tts/voices/Reference_Videos/ClassicUnni_Ref.mp4"
REF_TEXT = "안녕하세요, 오늘 전해드릴 소식은 유튜브 화면 녹화 영상을 기반으로 한 인공지능 음성 복제 기술입니다."

# [대상] 생성할 대본
TARGET_SCRIPT_PATH = Path("/Users/a12/projects/tts/대본.txt")
OUTPUT_DIR = Path.home() / "Downloads"

# 🚀 속도 설정 추가 (+40% 적용)
SPEED = 1.4

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
    text = text.replace('. ', '.').replace('.', '.. ')
    text = text.replace("외양간", "외양깐").replace("땅바닥", "땅빠닥")
    
    num_to_sino = {'1':'일','2':'이','3':'삼','4':'사','5':'오','6':'육','7':'칠','8':'팔','9':'구','10':'십'}
    text = re.sub(r'(\d+)편', lambda m: num_to_sino.get(m.group(1), m.group(1)) + "편", text)
    return text

def format_srt_time(seconds):
    td = datetime.timedelta(seconds=seconds)
    hours = int(td.total_seconds()) // 3600
    minutes = (int(td.total_seconds()) % 3600) // 60
    secs = int(td.total_seconds()) % 60
    millis = int(td.microseconds / 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

def split_chunks(text, max_chars=100):
    lines = text.splitlines()
    final_chunks = []
    for line in lines:
        line = line.strip()
        if not line: continue
        sentences = re.findall(r'[^,!?\s][^,!?\n]*[,!?\n]*', line)
        current_chunk = ""
        for s in sentences:
            s = s.strip()
            if not s: continue
            if len(current_chunk) + len(s) + 1 <= max_chars: current_chunk = (current_chunk + " " + s).strip()
            else:
                if current_chunk: final_chunks.append(current_chunk)
                current_chunk = s
        if current_chunk: final_chunks.append(current_chunk)
    return [c.strip() for c in final_chunks if c.strip()]

def main():
    print("==========================================")
    print("🎙️ Qwen3-TTS [MLX] ClassicUnni SpeedUp (+20%)")
    print("==========================================")

    if not TARGET_SCRIPT_PATH.exists():
        print(f"❌ 대본 파일이 없습니다: {TARGET_SCRIPT_PATH}")
        return

    with open(TARGET_SCRIPT_PATH, "r", encoding="utf-8") as f:
        target_text = f.read().strip()
    
    target_text = normalize_text(target_text)
    chunks = split_chunks(target_text)
    print(f"📄 총 {len(chunks)}개의 파트로 대본 처리 시작...")

    print(f"\n🚀 모델 로딩 중...")
    model = load(str(MODEL_PATH))

    if not os.path.exists(REF_AUDIO):
        print(f"⚠️ 레퍼런스 오디오가 없습니다: {REF_AUDIO}")
        return

    ref_wav, sr = librosa.load(REF_AUDIO, sr=24000)
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        sf.write(tmp.name, ref_wav, sr)
        temp_ref_path = tmp.name

    combined_audio = AudioSegment.empty()
    srt_entries = []
    current_time_sec = 0.0
    PAUSE_MS = 500  # 속도 증가에 맞춰 쉴 공간도 살짝 미세 조정

    for i, chunk in enumerate(chunks):
        print(f"🎙️  [{i+1}/{len(chunks)}] 생성 중: {chunk[:40]}...")
        try:
            results = model.generate(
                text=chunk,
                ref_audio=temp_ref_path,
                ref_text=REF_TEXT, 
                language="Korean",
                temperature=0.8,
                top_p=0.9,
                speed=SPEED    # 🚀 속도 옵션 추가
            )

            segment_audio_mx = None
            for res in results:
                if segment_audio_mx is None: segment_audio_mx = res.audio
                else: segment_audio_mx = mx.concatenate([segment_audio_mx, res.audio])
            
            if segment_audio_mx is not None:
                audio_np = np.array(segment_audio_mx)
                
                # 🚀 모델 파라미터가 무시되는 경우를 대비해 librosa 물리적 타임 스트레치(배속) 적용
                if SPEED != 1.0:
                    audio_np = librosa.effects.time_stretch(audio_np, rate=SPEED)
                
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
            print(f"❌ 에러 발생: {str(e)}")

    if len(combined_audio) > 0:
        timestamp = datetime.datetime.now().strftime("%H%M%S")
        output_prefix = "클래식언니_SpeedUp"
        output_path = OUTPUT_DIR / f"{output_prefix}_{timestamp}.wav"
        combined_audio.export(str(output_path), format="wav")
        
        srt_path = str(output_path).replace(".wav", ".srt")
        with open(srt_path, "w", encoding="utf-8-sig") as f: f.writelines(srt_entries)
        
        print(f"\n✅ 생성 완료: {output_path}")
        os.unlink(temp_ref_path)
    else: print("\n⚠️ 생성 실패")

if __name__ == "__main__":
    main()

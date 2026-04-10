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

# 2. 데이터 설정 (유라/Eula 레퍼런스)
REF_AUDIO = "/Users/a12/Downloads/优菈/vo_eula_teammate_mika_01.wav"
REF_TEXT = "미카가 유격대에 처음 왔을 땐 그전에 있던 몇몇 사람들처럼 얼마 못 버티고 나갈 줄 알았어. 그런데 묵묵히 버티면서 임무를 아주 훌륭하게 완수했지. 게다가 자진해서 심부름 같은 잡일까지 도맡아서 하고 나와 다른 사람들이 소통하는 것도 도와줬어. 흥, 자꾸 날 챙겨주려 하다니… 대체 누굴 보고 배운 건지"

# Eula 캐릭터 스타일 지침 (Elegant, Noble, Slightly Cold)
STYLE_INSTRUCT = "Elegant, noble, and slightly cold aristocratic female tone."

# [대상] 생성할 대본
TARGET_SCRIPT_PATH = Path("/Users/a12/projects/tts/대본.txt")
OUTPUT_DIR = Path.home() / "Downloads"

def trim_silence(audio, threshold=-50.0, padding_ms=250):
    """음성 앞뒤 침묵 제거 및 끝부분 여유분 확보 (말끝 짤림 방지)"""
    start_trim = detect_leading_silence(audio, silence_threshold=threshold)
    end_trim = max(0, detect_leading_silence(audio.reverse(), silence_threshold=threshold) - 100)
    
    duration = len(audio)
    trimmed = audio[start_trim:max(start_trim+1, duration-end_trim)]
    
    silence = AudioSegment.silent(duration=padding_ms)
    return silence + trimmed.fade_out(50) + silence

def normalize_text(text):
    """TTS 발음 교정 및 특수 기호 정규화"""
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
    print("🎙️ Qwen3-TTS [MLX] Eula Zero-Shot (Gold v1)")
    print("   Character: Eula (유라)")
    print("   Style: " + STYLE_INSTRUCT)
    print("==========================================")

    if not TARGET_SCRIPT_PATH.exists():
        print(f"❌ 대본 파일이 없습니다: {TARGET_SCRIPT_PATH}")
        return

    with open(TARGET_SCRIPT_PATH, "r", encoding="utf-8") as f:
        full_text = f.read()

    # 3. 모델 로드
    print("⏳ 모델 로드 중...")
    model = load(str(MODEL_PATH))
    print("✅ 모델 로드 완료")

    # 4. 레퍼런스 오디오 로딩 (안정성을 위해 24kHz 로드)
    print("🎧 레퍼런스 오디오 로딩 중...")
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
        
        # Zero-Shot 생성 (최적화 파라미터 적용)
        results = model.generate(
            text=cleaned_text,
            ref_audio=temp_ref_path,
            ref_text=REF_TEXT[:80],
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

        # 후처리
        segment_pydub = trim_silence(segment_pydub)
        duration_sec = len(segment_pydub) / 1000.0

        # [스마트 자막 분리] 12자 단위
        sub_chunks = []
        parts = re.split(r'([.!?,\n]\s*)', chunk)
        curr = ""
        for p in parts:
            if len(curr) + len(p) <= 12: curr += p
            else:
                if curr: sub_chunks.append(curr.strip())
                curr = p
        if curr: sub_chunks.append(curr.strip())
        
        final_sub_chunks = []
        for sc in sub_chunks:
            if len(sc) > 12:
                words = sc.split()
                t = ""
                for w in words:
                    if len(t) + len(w) + 1 <= 12: t += (w + " ") if t else w
                    else:
                        if t: final_sub_chunks.append(t.strip())
                        t = w
                if t: final_sub_chunks.append(t.strip())
            else:
                final_sub_chunks.append(sc)
        
        total_chars = sum(len(c) for c in final_sub_chunks)
        temp_time = current_time_sec
        for sc_idx, sc in enumerate(final_sub_chunks):
            char_ratio = len(sc) / total_chars if total_chars > 0 else 1.0
            sc_duration = duration_sec * char_ratio
            start_t = format_srt_time(temp_time)
            end_t = format_srt_time(temp_time + sc_duration)
            srt_entries.append(f"{len(srt_entries)+1}\n{start_t} --> {end_t}\n{sc}\n\n")
            temp_time += sc_duration

        combined_audio += segment_pydub + AudioSegment.silent(duration=PAUSE_MS)
        current_time_sec += duration_sec + (PAUSE_MS / 1000.0)

    # 5. 결과 저장
    timestamp = datetime.datetime.now().strftime("%y%m%d_%H%M")
    base_name = f"Eula_Gold_{timestamp}"
    wav_path = OUTPUT_DIR / f"{base_name}.wav"
    srt_path = OUTPUT_DIR / f"{base_name}.srt"

    combined_audio.export(wav_path, format="wav")
    with open(srt_path, "w", encoding="utf-8-sig") as f:
        f.writelines(srt_entries)

    print("\n" + "="*40)
    print(f"🎉 '골드 버전' 생성 완료!")
    print(f"🔊 음성: {wav_path}")
    print(f"📝 자막: {srt_path}")
    print("="*40)
    
    os.unlink(temp_ref_path)

if __name__ == "__main__":
    main()

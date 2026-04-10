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

# 2. 데이터 설정 (분노한 여성 목소리 레퍼런스)
REF_AUDIO = "/Users/a12/Downloads/extracted_assets/Speaking_angrily_in_korean_22b571a676/Speaking_angrily_in_korean_22b571a676_vocals.wav"
REF_TEXT = "뭐 계약을 끝내 어디 깩촌해서 전화 사기라도 치는 거야 웃기시네. 웃기시네 경찰에 신고하기 전에 얼른."

# [대상] 생성할 대본
TARGET_SCRIPT_PATH = Path("/Users/a12/projects/tts/대본.txt")
OUTPUT_DIR = Path.home() / "Downloads"

def trim_silence(audio, threshold=-50.0, padding_ms=150):
    """음성 앞뒤 침묵 제거 및 끝부분 페이드 아웃 처리 (뚝 끊김 방지)"""
    start_trim = detect_leading_silence(audio, silence_threshold=threshold)
    end_trim = detect_leading_silence(audio.reverse(), silence_threshold=threshold)
    duration = len(audio)
    trimmed = audio[start_trim:max(start_trim+1, duration-end_trim)]
    
    silence = AudioSegment.silent(duration=padding_ms)
    # 끝부분 100ms 페이드 아웃으로 부드럽게 종료
    return silence + trimmed.fade_out(100) + silence

def normalize_text(text):
    """TTS 발음 교정 및 특수 기호 정규화"""
    # [1] 스마트 따옴표 및 따옴표 제거
    text = text.replace('“', '"').replace('”', '"').replace('‘', "'").replace('’', "'")
    text = text.replace('"', '').replace("'", "")
    
    # [2] 특정 단어 발음 교정 (대본 특성에 맞춰)
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
        
        # 문장 단위 분리
        sentences = re.findall(r'[^.!?,\s][^.!?,\n]*[.!?,\n]*', line)
        
        current_chunk = ""
        for s in sentences:
            s = s.strip()
            if not s: continue
            
            if len(current_chunk) + len(s) + 1 <= max_chars:
                if current_chunk:
                    current_chunk += " " + s
                else:
                    current_chunk = s
            else:
                if current_chunk:
                    final_chunks.append(current_chunk)
                current_chunk = s
        
        if current_chunk:
            final_chunks.append(current_chunk)
            
    return [c.strip() for c in final_chunks if c.strip()]

def main():
    print("==========================================")
    print("🎙️ Qwen3-TTS [MLX] Zero-Shot Voice Clone (MIL Angry)")
    print("==========================================")

    if not TARGET_SCRIPT_PATH.exists():
        print(f"❌ 대본 파일을 찾을 수 없습니다: {TARGET_SCRIPT_PATH}")
        return
    
    if not os.path.exists(REF_AUDIO):
        print(f"❌ 레퍼런스 오디오를 찾을 수 없습니다: {REF_AUDIO}")
        return

    with open(TARGET_SCRIPT_PATH, "r", encoding="utf-8") as f:
        target_text = f.read().strip()
    
    target_text = normalize_text(target_text)
    chunks = split_chunks(target_text)
    print(f"📄 총 {len(chunks)}개의 파트로 대본 처리 시작...")

    print(f"\n🚀 모델 로딩 중...")
    model = load(str(MODEL_PATH))

    # 레퍼런스 로딩 (MLX 오디오가 요구하는 24kHz 샘플링레이트)
    ref_wav, sr = librosa.load(REF_AUDIO, sr=24000, duration=10.0) 
    
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        sf.write(tmp.name, ref_wav, sr)
        temp_ref_path = tmp.name

    combined_audio = AudioSegment.empty()
    srt_entries = []
    current_time_sec = 0.0
    PAUSE_MS = 500 

    for i, chunk in enumerate(chunks):
        print(f"🎙️  [{i+1}/{len(chunks)}] 생성 중: {chunk[:40]}...")
        
        try:
            results = model.generate(
                text=chunk,
                ref_audio=temp_ref_path,
                ref_text=REF_TEXT, 
                language="Korean",
                temperature=0.7, # 분노 조절을 위해 약간 낮춤
                top_p=0.9
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
        except Exception as e:
            print(f"❌ 에러 발생: {str(e)}")

    if len(combined_audio) > 0:
        timestamp = datetime.datetime.now().strftime("%H%M%S")
        output_prefix = "ZeroShot_MIL_Angry"
        output_path = OUTPUT_DIR / f"{output_prefix}_{timestamp}.wav"
        combined_audio.export(str(output_path), format="wav")
        
        srt_path = str(output_path).replace(".wav", ".srt")
        with open(srt_path, "w", encoding="utf-8-sig") as f:
            f.writelines(srt_entries)
        
        print(f"\n✅ 생성 완료: {output_path}")
        os.unlink(temp_ref_path)
    else:
        print("\n⚠️ 생성 실패")

if __name__ == "__main__":
    main()

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

# 3. 발음 교정 사전 (텍스트를 모델에 넣기 직전에 치환)
PRONUNCIATION_DICT = {
    "팔도": "팔또",
    # 여기에 추가적인 발음 교정 규칙을 넣을 수 있습니다. 예: "효과": "효꽈"
}

def apply_pronunciation_rules(text):
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
    """
    개선된 청킹 로직:
    1. 줄바꿈(\n) 단위로 우선 분리
    2. 마침표, 쉼표 등 문장 부호를 포함하여 문장 단위로 분리
    3. 고립된 문장 부호가 청크 맨 앞에 오지 않도록 병합
    4. max_chars를 최대한 준수하되 문장의 맥락 유지
    """
    lines = text.splitlines()
    final_chunks = []
    
    for line in lines:
        line = line.strip()
        if not line: continue
        
        # 문장 부호를 포함하여 합리적으로 분리 (정규식 개선)
        # . ! ? , 뒤에 공백이 있거나 끝나는 지점을 기준으로 분리
        sentences = re.findall(r'[^.!?,\s][^.!?,\n]*[.!?,\n]*', line)
        
        current_chunk = ""
        for s in sentences:
            s = s.strip()
            if not s: continue
            
            # 현재 청크에 추가했을 때 제한을 넘지 않으면 병합
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
    print("🎙️ Qwen3-TTS [MLX] Zero-Shot Angry Voice (V2 - FIXED)")
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
    for i, c in enumerate(chunks):
        print(f"   [{i+1}] {c[:40]}...")

    print(f"\n🚀 MLX 베이스 모델 로딩 중: {MODEL_PATH.name}...")
    model = load(str(MODEL_PATH))

    print("🎧 레퍼런스 오디오 로딩 중 (6초 설정)...")
    if not os.path.exists(REF_AUDIO):
        print(f"⚠️ 레퍼런스 오디오가 없습니다. 경로를 확인해주세요: {REF_AUDIO}")
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
            # 발음 교정 적용 (실제 음성 생성용 텍스트)
            pronun_chunk = apply_pronunciation_rules(chunk)
            
            results = model.generate(
                text=pronun_chunk,
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
                srt_entries.append(f"{success_count+1}\n{format_srt_time(current_time_sec)} --> {format_srt_time(current_time_sec + duration_sec)}\n{chunk}\n\n")
                
                combined_audio += segment_pydub + AudioSegment.silent(duration=PAUSE_MS)
                current_time_sec += duration_sec + (PAUSE_MS / 1000.0)
                success_count += 1
            else:
                print(f"⚠️  [{i+1}/{len(chunks)}] 생성 실패: 모델이 음성을 반환하지 않았습니다.")
                fail_count += 1
        except Exception as e:
            print(f"❌ [{i+1}/{len(chunks)}] 에러 발생: {str(e)}")
            fail_count += 1

    if len(combined_audio) > 0:
        timestamp = os.popen("date +%H%M%S").read().strip()
        output_path = OUTPUT_DIR / f"AngryVoice_ZeroShot_V2_{timestamp}.wav"
        combined_audio.export(str(output_path), format="wav")
        
        srt_path = str(output_path).replace(".wav", ".srt")
        with open(srt_path, "w", encoding="utf-8-sig") as f:
            f.writelines(srt_entries)
        
        print(f"\n✅ 작업 완료!")
        print(f"   - 성공: {success_count}개 / 실패: {fail_count}개")
        print(f"   - 결과 파일: {output_path}")
        os.unlink(temp_ref_path)
    else:
        print("\n⚠️ 음성 생성 전면 실패 (결과물이 없습니다)")

if __name__ == "__main__":
    main()

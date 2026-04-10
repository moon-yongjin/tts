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

# 2. 고정 프리셋: ClassicUnni
PRESET = {
    "name": "클래식언니 (MP4)",
    "file": "/Users/a12/projects/tts/voices/Reference_Videos/ClassicUnni_Ref.mp4",
    "text": "안녕하세요, 오늘 전해드릴 소식은 유튜브 화면 녹화 영상을 기반으로 한 인공지능 음성 복제 기술입니다."
}

OUTPUT_DIR = Path.home() / "Downloads"
SPEED = 1.4  # 고속 렌더

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
    text = text.replace('. ', '.').replace('.', '.. ') # 🚀 마침표 공백 필수 지침
    
    # 🚀 사용자 지휘: 쉼표 절단 버그 차단을 위해 모든 쉼표 삭제
    text = text.replace(',', '')
    
    num_to_sino = {'1':'일','2':'이','3':'삼','4':'사','5':'오','6':'육','7':'칠','8':'팔','9':'구','10':'십','20':'이십'}
    text = re.sub(r'(\d+)(일|부|편|달러|원)', lambda m: num_to_sino.get(m.group(1), m.group(1)) + m.group(2), text)
    return text

def format_srt_time(seconds):
    td = datetime.timedelta(seconds=seconds)
    hours = int(td.total_seconds()) // 3600
    minutes = (int(td.total_seconds()) % 3600) // 60
    secs = int(td.total_seconds()) % 60
    millis = int(td.microseconds / 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

def main():
    print("\n==========================================")
    print("🎙️ Qwen3-TTS [대본 직접 타이핑 렌더러]")
    print("==========================================")
    print(f"✅ 적용된 보이스: {PRESET['name']}")

    print("\n--- 🤖 대본 입력을 시작합니다 ---")
    print("▶️ 읽을 대본을 그대로 입력하고 [엔터] 를 친 후, [빈 줄에서 엔터]를 한 번 더 누르면 생성이 시작됩니다:")
    
    # 🚀 멀티라인 대본 입력 받기
    lines = []
    while True:
        try:
            line = input()
            if line.strip() == "":
                break
            lines.append(line)
        except EOFError:
            break

    target_text = "\n".join(lines).strip()

    if not target_text:
        print("\n❌ 입력된 대본 내용이 없습니다. 가동을 종료합니다.")
        return

    print(f"\n📄 입력된 대본 전처리 중... (총 {len(target_text)}자)")
    text = normalize_text(target_text)

    print(f"🚀 모델 로딩 중...")
    model = load(str(MODEL_PATH))

    try:
         print(f"🎙️ 음성 생성 시작: {text[:40]}...")

         # 임시 wav 변환 (librosa .mp4 호환 대비)
         ref_wav, sr = librosa.load(PRESET["file"], sr=24000)
         with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
             sf.write(tmp.name, ref_wav, sr)
             temp_ref_path = tmp.name

         results = model.generate(
              text=text,
              ref_audio=temp_ref_path,
              ref_text=PRESET["text"],
              language="Korean",
              temperature=0.8,
              top_p=0.9,
              speed=SPEED
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
              
              timestamp = datetime.datetime.now().strftime("%H%M%S")
              output_path = OUTPUT_DIR / f"직접입력_출력물_{timestamp}.wav"
              segment_pydub.export(str(output_path), format="wav")
              
              print(f"\n✅ 생성 완료: {output_path}")

    except Exception as e:
         print(f"❌ 에러 발생: {str(e)}")
    finally:
         if 'temp_ref_path' in locals() and os.path.exists(temp_ref_path): 
             os.unlink(temp_ref_path)

if __name__ == "__main__":
    main()

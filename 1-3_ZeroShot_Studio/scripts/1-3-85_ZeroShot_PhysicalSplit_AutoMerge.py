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

# 2. 레퍼런스 프리셋 DB
PRESETS = {
    "1": {
        "name": "클래식언니 (MP4)",
        "file": "/Users/a12/projects/tts/voices/Reference_Videos/ClassicUnni_Ref.mp4",
        "text": "안녕하세요, 오늘 전해드릴 소식은 유튜브 화면 녹화 영상을 기반으로 한 인공지능 음성 복제 기술입니다."
    },
    "2": {
        "name": "Woman1 (세탁소_급함)",
        "file": "/Users/a12/projects/tts/voices/Reference_Audios/Clean_Woman_Presets/Woman1_세탁소_급함.wav" if Path("/Users/a12/projects/tts/voices/Reference_Audios/Clean_Woman_Presets/Woman1_세탁소_급함.wav").exists() else "/Users/a12/projects/tts/voices/Reference_Audios/Woman1_세탁소_급함.wav",
        "text": "아줌마 이것 좀 제발 빨리 다려주세요. 중요한 약속이라 당장 입어야 해요."
    },
    "3": {
         "name": "문 회장 (스크린 녹화 050504)",
         "file": "/Users/a12/projects/tts/voices/Reference_Audios/Screen_Recording_20260318_050504_YouTube_extracted.wav",
         "text": "보면 매출 자체는 나쁘지가 않아요. 656억 정도로 매출은 굉장히 잘 나오지만 일단 비용이 너무 높습니다. 영업 비용만 해도 946억이 나와서 영업 손실이 나고 있는 회사예요."
    }
}

TARGET_SCRIPT_PATH = Path("/Users/a12/projects/tts/대본.txt")
OUTPUT_DIR = Path.home() / "Downloads"
SPEED = 1.4   # 🚀 '속도빠름' 지침 준수 (1.1 ➡️ 1.4 상향)

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
    text = text.replace('. ', '.').replace('.', '.. ') # 🚀 마침표 띄어쓰기 가이드 공용 사수
    
    num_to_sino = {'1':'일','2':'이','3':'삼','4':'사','5':'오','6':'육','7':'칠','8':'팔','9':'구','10':'십','20':'이십'}
    text = re.sub(r'(\d+)(일|부|편|달러|원)', lambda m: num_to_sino.get(m.group(1), m.group(1)) + m.group(2), text)
    return text

def split_by_sentences_and_length(text, max_chars=200):
    """
    텍스트를 마침표/물음표 등 문장 단위로 쪼갠 뒤, 
    각 물리 단위가 200자를 넘지 않도록 가동 배치를 묶어 반환합니다.
    """
    # 문장 끝맺음 부호 기준 분할
    sentence_endings = re.compile(r'([^.?!]+[.?!]*)')
    raw_sentences = sentence_endings.findall(text)
    
    batches = []
    current_batch = ""
    
    for s in raw_sentences:
        s = s.strip()
        if not s: continue
        
        # 현 패치에 덧붙였을 때 200자를 넘지 않으면 병합
        if len(current_batch) + len(s) < max_chars:
            current_batch += " " + s if current_batch else s
        else:
            if current_batch:
                batches.append(current_batch)
            current_batch = s
            
    if current_batch:
        batches.append(current_batch)
        
    return batches

def format_srt_time(seconds):
    td = datetime.timedelta(seconds=seconds)
    hours = int(td.total_seconds()) // 3600
    minutes = (int(td.total_seconds()) % 3600) // 60
    secs = int(td.total_seconds()) % 60
    millis = int(td.microseconds / 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

def main():
    print("\n==========================================")
    print("🎙️ Qwen3-TTS [물리적 대본 분할 통합 렌더러]")
    print("==========================================")

    print("\n[ 📂 목소리 프리셋 정보 ]")
    # 🚀 사용자 지휘: 1 2 3 번 고르는 것 폐기하고 ClassicUnni 로 고정
    active_preset = PRESETS["1"]
    print(f"  • 적용된 보이스: {active_preset['name']}")

    if not TARGET_SCRIPT_PATH.exists():
        print(f"❌ 대본 파일이 없습니다: {TARGET_SCRIPT_PATH}")
        return

    with open(TARGET_SCRIPT_PATH, "r", encoding="utf-8") as f:
         target_text = f.read().strip()

    # 🚀 핵심: 200자 물리 분할 수행
    parts = split_by_sentences_and_length(target_text, max_chars=200)
    print(f"\n📄 총 {len(parts)}개의 물리 파트(Part)로 대본 분할 완료. 생성 시작...")
    print(f"🚀 모델 로딩 중...")
    model = load(str(MODEL_PATH))

    combined_audio = AudioSegment.empty()
    srt_entries = []
    current_time_sec = 0.0
    PAUSE_MS = 400 

    for i, text_part in enumerate(parts):
        text = normalize_text(text_part)
        print(f"🎙️  [{i+1}/{len(parts)}] 생성 중: {text[:40]}...")

        ref_wav, sr = librosa.load(active_preset["file"], sr=24000)
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            sf.write(tmp.name, ref_wav, sr)
            temp_ref_path = tmp.name

        try:
             results = model.generate(
                  text=text,
                  ref_audio=temp_ref_path,
                  ref_text=active_preset["text"],
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
                  
                  duration_sec = len(segment_pydub) / 1000.0
                  srt_entries.append(f"{i+1}\n{format_srt_time(current_time_sec)} --> {format_srt_time(current_time_sec + duration_sec)}\n{text_part}\n\n")
                  
                  combined_audio += segment_pydub + AudioSegment.silent(duration=PAUSE_MS)
                  current_time_sec += duration_sec + (PAUSE_MS / 1000.0)

        except Exception as e:
             print(f"❌ 에러 발생: {str(e)}")
        finally:
             if os.path.exists(temp_ref_path): os.unlink(temp_ref_path)

    if len(combined_audio) > 0:
         timestamp = datetime.datetime.now().strftime("%H%M%S")
         output_path = OUTPUT_DIR / f"파트분할_통합출력_{timestamp}.wav"
         combined_audio.export(str(output_path), format="wav")
         
         srt_path = str(output_path).replace(".wav", ".srt")
         with open(srt_path, "w", encoding="utf-8-sig") as f: f.writelines(srt_entries)
         
         print(f"\n✅ 통합 생성 완료: {output_path}")
    else: print("\n⚠️ 생성 실패")

if __name__ == "__main__":
    main()

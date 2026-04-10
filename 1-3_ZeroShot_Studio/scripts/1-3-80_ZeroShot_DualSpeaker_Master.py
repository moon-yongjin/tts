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

# 2. 목소리 프리셋 DB (여성 및 고성능 레퍼런스 모음)
PRESETS = {
    "1": {
        "name": "클래식언니 (MP4)",
        "file": "/Users/a12/projects/tts/voices/Reference_Videos/ClassicUnni_Ref.mp4",
        "text": "안녕하세요, 오늘 전해드릴 소식은 유튜브 화면 녹화 영상을 기반으로 한 인공지능 음성 복제 기술입니다."
    },
    "2": {
        "name": "Woman1 (세탁소_급함)",
        "file": "/Users/a12/projects/tts/voices/Reference_Audios/Woman1_세탁소_급함.wav",
        "text": "아줌마 이것 좀 제발 빨리 다려주세요. 중요한 약속이라 당장 입어야 해요."
    },
    "3": {
        "name": "Woman2 (아트_차분)",
        "file": "/Users/a12/projects/tts/voices/Reference_Audios/Woman2_아트_차분.wav",
        "text": "그리고 분명 똑같은 사진을 보고 그리는데 아무리 수정을 해봐도 그림과 사진이 닮지 않게 그려질 때가 있죠?"
    },
    "4": {
        "name": "Woman3 (엄마_다정)",
        "file": "/Users/a12/projects/tts/voices/Reference_Audios/Woman3_엄마_다정.wav",
        "text": "응, 하지만 동생을 잘 돌봐줘야 해? 엄마는 할 일이 남았으니까 이따가 올게."
    },
    "5": {
        "name": "Woman4 (감성_슬픔)",
        "file": "/Users/a12/projects/tts/voices/Reference_Audios/Woman4_감성_슬픔.wav",
        "text": "아버지가 인팀 전이 많지가 되셔서 돌아오셨고 있는 모든 걸 그냥 다 두신 그런 날만 되면은 저희는 책가방을 싸들고 있다가 새벽 2시쯤 어디론가 다 숨어야 되는..."
    },
    "6": {
        "name": "Woman5 (안내_나긋)",
        "file": "/Users/a12/projects/tts/voices/Reference_Audios/Woman5_안내_나긋.wav",
        "text": "행복은 무엇이라고 생각하세요? 누구에게도 없는 특별한 것이 아니라 누구에게나 있는 일상의 작은 것에서 감사하는 마음이 주는 그거 그것이 행복이 아닐까요?"
    },
    "7": {
         "name": "문 회장 (스크린 녹화 050504)",
         "file": "/Users/a12/projects/tts/voices/Reference_Audios/Screen_Recording_20260318_050504_YouTube_extracted.wav",
         "text": "보면 매출 자체는 나쁘지가 않아요. 656억 정도로 매출은 굉장히 잘 나오지만 일단 비용이 너무 높습니다. 영업 비용만 해도 946억이 나와서 영업 손실이 나고 있는 회사예요."
    }
}

TARGET_SCRIPT_PATH = Path("/Users/a12/projects/tts/대본.txt")
OUTPUT_DIR = Path.home() / "Downloads"
SPEED = 1.1

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
    text = text.replace("외양간", "외양깐").replace("땅바닥", "땅빠닥")
    
    num_to_sino = {'1':'일','2':'이','3':'삼','4':'사','5':'오','6':'육','7':'칠','8':'팔','9':'구','10':'십','20':'이십'}
    text = re.sub(r'(\d+)(일|부|편|달러|원)', lambda m: num_to_sino.get(m.group(1), m.group(1)) + m.group(2), text)
    return text

def split_chunks_dual(text, max_chars=100):
    # 따옴표 분리 정규식: "대사" 또는 일반 텍스트
    # 듀얼 스피커용: {"type": "narration"/"dialogue", "text": "..."}
    lines = text.splitlines()
    final_chunks = []
    
    for line in lines:
        line = line.strip()
        if not line: continue
        
        # 1. 아예 대괄호 태그 처리 (확장용 남겨둠)
        # 2. 표준 정규식으로 따옴표 구별
        # 심플하게: 한 줄이 따옴표로 시작해서 끝나면 그것은 dialogue, 아니면 narration
        if line.startswith('"') and (line.endswith('"') or '"' in line):
             final_chunks.append({"role": "dialogue", "text": line.replace('"', '')})
        else:
             final_chunks.append({"role": "narration", "text": line})
             
    return final_chunks

def format_srt_time(seconds):
    td = datetime.timedelta(seconds=seconds)
    hours = int(td.total_seconds()) // 3600
    minutes = (int(td.total_seconds()) % 3600) // 60
    secs = int(td.total_seconds()) % 60
    millis = int(td.microseconds / 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

def main():
    print("\n==========================================")
    print("🎙️ Qwen3-TTS [선택형 듀얼 마스터 스크립트]")
    print("==========================================")

    # 1. 메뉴 출력
    print("\n[ 📂 사용 가능한 목소리 프리셋 목록 ]")
    for k, v in PRESETS.items():
        print(f"  [{k}] {v['name']}")
        
    print("\n--- 🤖 듀얼 스피커 배분 시작 ---")
    nav_num = input("▶️ 1. [나레이션](따옴표 밖) 목소리 번호를 선택하세요: ").strip()
    dia_num = input("▶️ 2. [따옴표 대사](따옴표 안) 목소리 번호를 선택하세요: ").strip()

    if nav_num not in PRESETS or dia_num not in PRESETS:
        print("❌ 잘못된 번호 입력입니다.")
        return

    nav_preset = PRESETS[nav_num]
    dia_preset = PRESETS[dia_num]
    
    print(f"\n✅ 배정 완료:")
    print(f"  • 나레이터: {nav_preset['name']}")
    print(f"  • 대사 화자: {dia_preset['name']}")

    if not TARGET_SCRIPT_PATH.exists():
        print(f"❌ 대본 파일이 없습니다: {TARGET_SCRIPT_PATH}")
        return

    with open(TARGET_SCRIPT_PATH, "r", encoding="utf-8") as f:
         target_text = f.read().strip()

    # ⚠️ 따옴표 기반 분리를 하기 위해 '대각 정규 따옴표'를 미리 표준 따옴표 '"' 로 치환
    target_text = target_text.replace('“', '"').replace('”', '"')
    chunks = split_chunks_dual(target_text)
    
    print(f"\n📄 총 {len(chunks)}개의 피스(Piece) 분리 완료. 생성 시작...")
    print(f"🚀 모델 로딩 중...")
    model = load(str(MODEL_PATH))

    combined_audio = AudioSegment.empty()
    srt_entries = []
    current_time_sec = 0.0
    PAUSE_MS = 500 

    for i, piece in enumerate(chunks):
        role = piece["role"]
        text = normalize_text(piece["text"])
        
        # 역할에 따른 레퍼런스 선택
        active_preset = nav_preset if role == "narration" else dia_preset
        print(f"🎙️  [{i+1}/{len(chunks)}] [{role}] 생성 중: {text[:30]}...")

        # 임시 wav 변환 (librosa .mp4 에러 복원 대비)
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
                  srt_entries.append(f"{i+1}\n{format_srt_time(current_time_sec)} --> {format_srt_time(current_time_sec + duration_sec)}\n{piece['text']}\n\n")
                  
                  combined_audio += segment_pydub + AudioSegment.silent(duration=PAUSE_MS)
                  current_time_sec += duration_sec + (PAUSE_MS / 1000.0)

        except Exception as e:
             print(f"❌ 에러 발생: {str(e)}")
        finally:
             if os.path.exists(temp_ref_path): os.unlink(temp_ref_path)

    if len(combined_audio) > 0:
         timestamp = datetime.datetime.now().strftime("%H%M%S")
         output_path = OUTPUT_DIR / f"듀얼마스터_결과물_{timestamp}.wav"
         combined_audio.export(str(output_path), format="wav")
         
         srt_path = str(output_path).replace(".wav", ".srt")
         with open(srt_path, "w", encoding="utf-8-sig") as f: f.writelines(srt_entries)
         
         print(f"\n✅ 통합 생성 완료: {output_path}")
    else: print("\n⚠️ 생성 실패")

if __name__ == "__main__":
    main()

import os
import sys
import re
from pathlib import Path
import mlx.core as mx
from mlx_audio.tts import load
import numpy as np
import soundfile as sf
import librosa
from pydub import AudioSegment
from pydub.silence import detect_leading_silence
import datetime

# [📂 형님의 지침 MD 가이드 100% 반영 버전]

# 1. 경로 설정
PROJECT_ROOT = Path("/Users/a12/projects/tts/qwen3-tts-apple-silicon")
MODEL_PATH = PROJECT_ROOT / "models/Qwen3-TTS-12Hz-1.7B-Base-8bit"
sys.path.append(str(PROJECT_ROOT))

# 🎯 [신규 유튜브 녹화 오토런 설정]
REFERENCE_MP4 = "/Users/a12/projects/tts/reference_audio_3.wav"
# 📝 [추출된 레퍼런스 텍스트] - 지침 준수 (ASR 결과물 반영)
REFERENCE_TEXT = "술 더 떠서 주민회 회장까지 한다는 것이었다. 또다시 전화와 인터폰을 왕래하느라 입맛이 떨어져 아침에 설친 그는 주민회 회장까지 한다는 것이었다."

TARGET_SCRIPT_PATH = Path("/Users/a12/projects/tts/대본.txt")
OUTPUT_FOLDER = Path.home() / "Downloads"
SPEED = 1.1  # 🚨 지침: 인코더 자체 speed 파라미터만 사용 (중복 배속 금지)

def trim_silence(audio, threshold=-50.0, padding_ms=150):
    start_trim = detect_leading_silence(audio, silence_threshold=threshold)
    end_trim = detect_leading_silence(audio.reverse(), silence_threshold=threshold)
    duration = len(audio)
    trimmed = audio[start_trim:max(start_trim+1, duration-end_trim)]
    silence = AudioSegment.silent(duration=padding_ms)
    return silence + trimmed.fade_out(100) + silence

# [📝 1. 대본 텍스트 전처리 - 지침서 기반]
def normalize_text(text):
    # 특수 따옴표 제거
    text = text.replace('“', '"').replace('”', '"').replace('‘', "'").replace('’', "'")
    text = text.replace('"', '').replace("'", "")
    
    # 🚀 마침표(.) 뒤 강제 스페이스 (호흡 조절 필수 지침)
    text = text.replace('. ', '.').replace('.', '.. ') 
    
    # 🗣️ 발음 교정 (소리 나는 대로)
    text = text.replace("외양간", "외양깐")
    text = text.replace("땅바닥", "땅빠닥")
    text = text.replace("코방귀", "콧방귀")
    
    # 🔢 [숫자 일괄 한글화 - 지침 보강 버전]
    # 1. 한자어(Sino) 매칭: 년, 위, 일, 부, 편, 달러, 원, 분
    sino_map = {'1':'일','2':'이','3':'삼','4':'사','5':'오','6':'육','7':'칠','8':'팔','9':'구','10':'십','20':'이십'}
    text = re.sub(r'(\d+)(년|위|일|부|편|달러|원|분)', 
                  lambda m: sino_map.get(m.group(1), m.group(1)) + m.group(2), text)
    
    # 2. 고유어(Native) 매칭: 시, 살, 번, 명, 개
    native_map = {'1':'한','2':'두','3':'세','4':'네','5':'다섯','6':'여섯','7':'일곱','8':'여덟','9':'아홉','10':'열',
                  '11':'열한','12':'열두','20':'스무'}
    text = re.sub(r'(\d+)(시|살|번|명|개)', 
                  lambda m: native_map.get(m.group(1), m.group(1)) + m.group(2), text)
    
    # 3. 쌩 숫자 단독 처리 (예: 10, 20)
    text = text.replace(" 10 ", " 열 ").replace(" 20 ", " 스무 ").replace(" 10.", " 열.").replace(" 20.", " 스무.")
    
    return text

def split_chunks(text):
    # 빈 줄 제외하고 문장 단위로 분리
    lines = text.splitlines()
    return [line.strip() for line in lines if line.strip()]

def main():
    print("\n" + "="*55)
    print("🎙️ Qwen3-TTS [지침 준수 유튜브 오토런 통합 모드]")
    print(f"📹 레퍼런스: {REFERENCE_MP4}")
    print(f"📖 대본: {TARGET_SCRIPT_PATH.name}")
    print("="*55 + "\n")

    if not os.path.exists(REFERENCE_MP4):
        print(f"❌ 녹화 파일이 없습니다: {REFERENCE_MP4}")
        return

    if not TARGET_SCRIPT_PATH.exists():
        print(f"❌ 대본 파일이 없습니다: {TARGET_SCRIPT_PATH}")
        return

    print("⏳ 모델 로딩 중 (Apple Silicon MLX)...")
    model = load(str(MODEL_PATH))

    with open(TARGET_SCRIPT_PATH, "r", encoding="utf-8") as f:
        target_text = f.read().strip()
    
    # 전처리 지침 적용
    chunks = split_chunks(target_text)
    print(f"📄 총 {len(chunks)}개의 문장 생성을 시작합니다.")

    combined_audio = AudioSegment.empty()
    
    for i, chunk in enumerate(chunks):
        chunk = normalize_text(chunk)
        if not chunk: continue
        
        print(f"🎙️ [{i+1}/{len(chunks)}] 생성 중: {chunk[:40]}...")
        
        # 🧪 생성 (Generator 대응 및 Dtype/Shape 방어)
        audio_out = model.generate(
            chunk, 
            ref_audio=REFERENCE_MP4, 
            ref_text=REFERENCE_TEXT,
            speed=SPEED
        )
        
        # [🔥 Generator vs Array vs GenerationResult 대응 로직]
        if hasattr(audio_out, '__iter__') and not hasattr(audio_out, '__len__'):
             parts = []
             for a in audio_out:
                 # GenerationResult 인지 확인
                 if hasattr(a, 'audio'): a_data = np.array(a.audio)
                 else: a_data = np.array(a)
                 
                 if a_data.ndim == 0: a_data = a_data.reshape(1)
                 parts.append(a_data)
             audio_array = np.concatenate(parts)
        elif hasattr(audio_out, 'audio'):
             audio_array = np.array(audio_out.audio)
        else:
             audio_array = np.array(audio_out)

        if audio_array.ndim == 0: audio_array = audio_array.reshape(1)

        # [🔥 차원(Shape) & Dtype 에러 방어 로직]
        temp_wav = "/tmp/temp_gen.wav"
        arr = audio_array.astype(np.float32).flatten() 
        sf.write(temp_wav, arr, 24000) 
        
        gen_segment = AudioSegment.from_wav(temp_wav)
        
        # 무음 제거 및 결합 (지침에 따른 호흡 확보)
        combined_audio += trim_silence(gen_segment)

    # 최종 저장
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"YouTube_AutoRun_{timestamp}.wav"
    output_path = OUTPUT_FOLDER / output_filename
    
    combined_audio.export(output_path, format="wav")
    
    print("\n" + "✨"*25)
    print(f"✅ '병신짓 방지 지침'이 완벽 적용된 결과물 생성 완료!")
    print(f"📂 저장 위치: {output_path}")
    print("✨"*25 + "\n")

if __name__ == "__main__":
    main()

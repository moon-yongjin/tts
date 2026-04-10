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

# [📂 9-15줄 테스트 스크립트 - 100% 지침 준수 버전]

PROJECT_ROOT = Path("/Users/a12/projects/tts/qwen3-tts-apple-silicon")
MODEL_PATH = PROJECT_ROOT / "models/Qwen3-TTS-12Hz-1.7B-Base-8bit"
sys.path.append(str(PROJECT_ROOT))

# 🎯 9번 보이스 (오디오1)
REFERENCE_MP4 = "/Users/a12/projects/tts/reference_audio_3.wav"
REFERENCE_TEXT = "술 더 떠서 주민회 회장까지 한다는 것이었다. 또다시 전화와 인터폰을 왕래하느라 입맛이 떨어져 아침에 설친 그는 주민회 회장까지 한다는 것이었다."

TARGET_SCRIPT_PATH = Path("/Users/a12/projects/tts/대본.txt")
OUTPUT_FOLDER = Path("/Users/a12/Downloads")
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
    text = text.replace('.', '. ').replace('.  ', '. ') 
    text = text.replace("외양간", "외양깐").replace("땅바닥", "땅빠닥").replace("임명장", "임명짱").replace("콧방귀", "콧방귀")
    
    sino_map = {'1':'일','2':'이','3':'삼','4':'사','5':'오','6':'육','7':'칠','8':'팔','9':'구','10':'십','20':'이십'}
    text = re.sub(r'(\d+)(년|위|일|부|편|달러|원|분)', 
                  lambda m: sino_map.get(m.group(1), m.group(1)) + m.group(2), text)
    
    native_map = {'1':'한','2':'두','3':'세','4':'네','5':'다섯','6':'여섯','7':'일곱','8':'여덟','9':'아홉','10':'열',
                  '11':'열한','12':'열두','20':'스무'}
    text = re.sub(r'(\d+)(시|살|번|명|개)', 
                  lambda m: native_map.get(m.group(1), m.group(1)) + m.group(2), text)
    
    text = text.replace(" 10 ", " 열 ").replace(" 20 ", " 스무 ").replace(" 10.", " 열.").replace(" 20.", " 스무.")
    return text

def main():
    print("⏳ 모델 로딩 중...")
    model = load(str(MODEL_PATH))

    with open(TARGET_SCRIPT_PATH, "r", encoding="utf-8") as f:
        # 🚨 정확히 9-15줄만 추출 (0-indexed: 8~14)
        all_lines = [l.strip() for l in f.readlines() if l.strip()]
        chunks = all_lines[8:15]

    print(f"📄 총 {len(chunks)}개의 문장(9-15줄) 생성을 시작합니다.")

    combined_audio = AudioSegment.empty()
    
    for i, chunk in enumerate(chunks):
        chunk = normalize_text(chunk)
        if not chunk: continue
        
        print(f"🎙️ [{i+1}/{len(chunks)}] 생성 중: {chunk[:40]}...")
        audio_out = model.generate(chunk, ref_audio=REFERENCE_MP4, ref_text=REFERENCE_TEXT, speed=SPEED)
        
        # Array conversion
        if hasattr(audio_out, '__iter__') and not hasattr(audio_out, '__len__'):
             parts = [np.array(a.audio if hasattr(a, 'audio') else a) for a in audio_out]
             audio_array = np.concatenate([p.reshape(1) if p.ndim == 0 else p for p in parts])
        elif hasattr(audio_out, 'audio'):
             audio_array = np.array(audio_out.audio)
        else:
             audio_array = np.array(audio_out)

        temp_wav = "/tmp/temp_9_15.wav"
        sf.write(temp_wav, audio_array.astype(np.float32).flatten(), 24000)
        
        gen_segment = AudioSegment.from_wav(temp_wav)
        combined_audio += trim_silence(gen_segment)

    output_path = OUTPUT_FOLDER / "Test_Lines_9_15.wav"
    combined_audio.export(output_path, format="wav")
    print(f"✅ 생성 완료: {output_path}")

if __name__ == "__main__":
    main()

import os
import re
import sys
import torch
import soundfile as sf
import numpy as np
# import whisper (Removed for speed)
from qwen_tts import Qwen3TTSModel
from datetime import datetime, UTC
from pydub import AudioSegment

# [경로 설정]
ENGINE_DIR = os.path.dirname(os.path.abspath(__file__))
CORE_DIR = os.path.dirname(ENGINE_DIR)
ROOT_DIR = os.path.dirname(CORE_DIR)
DOWNLOADS_DIR = os.path.join(os.path.expanduser("~"), "Downloads")

# [Qwen-TTS 설정]
MODEL_ID = "Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice"
SPEAKER = "sohee"
INSTRUCT = "An extremely breathy and airy voice of a 40-year-old woman. The tone is solemn, tragic, and grave, as if speaking with a heavy heart."

# [Whisper 설정]
STT_MODEL_NAME = "base"

_tts_model = None
# _stt_model = None (Removed)

def get_tts_model():
    global _tts_model
    if _tts_model is None:
        device = "mps" if torch.backends.mps.is_available() else "cpu"
        print(f"📡 Qwen-TTS 모델 로딩 중 ({device})...")
        _tts_model = Qwen3TTSModel.from_pretrained(MODEL_ID, device_map=device)
    return _tts_model

# def get_stt_model(): (Removed)

def clean_for_output(text):
    text = re.sub(r'\[(BGM|묘사|지문|설명|배경|음악|CHAPTER|챕터|SFX):?.*?\]', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\[(대사|지문|묘사|설명)\]', '', text)
    text = re.sub(r'\(.*?\)', '', text)
    text = re.sub(r'\[SFX\]\s*:.*?(?=\[|$|\n\n)', '', text, flags=re.IGNORECASE)
    symbols = ['*', '-', '#', '@', '+', '=', '>', '<', '|', '/', '\\', '^']
    for s in symbols: text = text.replace(s, '')
    return text.strip()

def fix_initial_law(text):
    text = re.sub(r'(\d)\.(\d)', r'\1 쩜 \2', text)
    corrections = {"녀자": "여자", "래일": "내일", "리용": "이용", "량심": "양심", "력사": "역사", "련합": "연합"}
    for wrong, right in corrections.items(): text = text.replace(wrong, right)
    return text

def format_srt_time(seconds):
    td = datetime.fromtimestamp(seconds, UTC)
    return td.strftime('%H:%M:%S,%f')[:-3]

def generate_voice_qwen(text, output_path):
    tts = get_tts_model()
    clean_text = clean_for_output(text)
    clean_text = fix_initial_law(clean_text)
    if not clean_text.strip(): return False

    print(f"🎙️ Qwen-TTS 생성 시작: {os.path.basename(output_path)} (글자수: {len(clean_text)})")
    wavs, sr = tts.generate_custom_voice(text=clean_text, speaker=SPEAKER, language="Korean", instruct=INSTRUCT)
    
    temp_wav = output_path.replace(".mp3", ".temp.wav")
    sf.write(temp_wav, wavs[0], sr)
    
    final_audio = AudioSegment.from_wav(temp_wav)
    total_duration_ms = len(final_audio)
    
    print(f"✍️ 자막 생성 중 (수학적 추정)...")
    # 대본을 문장 단위로 분할하여 시간 배분
    sentences = re.split(r'(?<=[.!?])\s+', clean_text)
    sentences = [s.strip() for s in sentences if s.strip()]
    
    total_chars = sum(len(s) for s in sentences)
    srt_path = output_path.replace(".mp3", ".srt")
    
    with open(srt_path, "w", encoding="utf-8-sig") as f:
        current_ms = 0
        for i, sent in enumerate(sentences):
            # 글자 수 비례로 시간 배분
            duration_ms = (len(sent) / total_chars) * total_duration_ms
            
            start_sec = current_ms / 1000.0
            end_sec = (current_ms + duration_ms) / 1000.0
            
            f.write(f"{i + 1}\n{format_srt_time(start_sec)} --> {format_srt_time(end_sec)}\n{sent}\n\n")
            current_ms += duration_ms

    print(f"📦 MP3 변환 중...")
    final_audio.export(output_path, format="mp3", bitrate="192k")
    
    if os.path.exists(temp_wav): os.remove(temp_wav)
    print(f"✅ 완료: {os.path.basename(output_path)}")
    return True

def split_text(text, max_chars=500):
    """지정된 글자수에 맞춰 문장 단위로 텍스트를 정교하게 분할"""
    sentences = re.split(r'(?<=[.!?])\s+', text)
    chunks = []
    current_chunk = ""
    
    for sentence in sentences:
        if len(current_chunk) + len(sentence) <= max_chars:
            current_chunk += (" " + sentence if current_chunk else sentence)
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            # 문장 하나가 max_chars보다 길면 강제 분할
            if len(sentence) > max_chars:
                for i in range(0, len(sentence), max_chars):
                    chunks.append(sentence[i:i+max_chars].strip())
                current_chunk = ""
            else:
                current_chunk = sentence
                
    if current_chunk:
        chunks.append(current_chunk.strip())
    return chunks

if __name__ == "__main__":
    target_file = sys.argv[1] if len(sys.argv) > 1 else "대본.txt"
    script_path = os.path.join(ROOT_DIR, target_file)
    if not os.path.exists(script_path): script_path = os.path.abspath(target_file)
    
    if not os.path.exists(script_path):
        print(f"❌ 대본 파일을 찾을 수 없습니다: {target_file}")
        sys.exit(1)

    with open(script_path, "r", encoding="utf-8") as f:
        script_text = f.read().strip()
    
    print(f"📄 총 {len(script_text)}자의 대본을 처리합니다.")
    
    # 사용자 요청에 따라 500자 단위로 정교하게 분할
    chunks = split_text(script_text, max_chars=500)
    print(f"📦 대본을 {len(chunks)}개의 파트로 나누었습니다.")

    timestamp = datetime.now().strftime("%m%d_%H%M")
    for i, chunk in enumerate(chunks):
        print(f"\n🚀 [Part {i+1}/{len(chunks)}] 진행 중...")
        output_file = os.path.join(DOWNLOADS_DIR, f"{os.path.splitext(os.path.basename(target_file))[0]}_Qwen_{timestamp}_part{i+1:03d}.mp3")
        generate_voice_qwen(chunk, output_file)
        
    print(f"\n✨ 모든 작업 완료! (8,000자 대응 모드)")
    print(f"📂 저장 위치: {DOWNLOADS_DIR}")

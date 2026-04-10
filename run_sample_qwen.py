import os
import re
import sys
import torch
import soundfile as sf
import numpy as np
from datetime import datetime
try:
    from pydub import AudioSegment
except ImportError:
    print("⚠️ pydub not found. Please install it with 'pip install pydub'")
    sys.exit(1)

# Add current directory to path so it can find qwen_tts
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from qwen_tts import Qwen3TTSModel

# [경로 설정]
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WORKSPACE_DIR = os.path.dirname(BASE_DIR)
DOWNLOADS_DIR = os.path.join(WORKSPACE_DIR, "Downloads")
os.makedirs(DOWNLOADS_DIR, exist_ok=True)

# [Qwen-TTS 설정]
MODEL_ID = "Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice"
SPEAKER = "sohee"
INSTRUCT = "An extremely breathy and airy voice of a 40-year-old woman. The tone is solemn, tragic, and grave, as if speaking with a heavy heart."

_tts_model = None

def get_tts_model():
    global _tts_model
    if _tts_model is None:
        print("📡 Qwen-TTS 광속 엔진 가동 (bfloat16 + cuda)...")
        try:
            # 부대표님의 검증된 필승 세팅 이식
            _tts_model = Qwen3TTSModel.from_pretrained(
                MODEL_ID,
                torch_dtype=torch.bfloat16,
                device_map="cuda" # 확실하게 GPU 점유
            )
        except Exception as e:
            print(f"⚠️ 최적화 로딩 실패 ({e}), 기본 모드로 재시도합니다...")
            _tts_model = Qwen3TTSModel.from_pretrained(MODEL_ID, device_map="auto")
    return _tts_model

def clean_for_output(text):
    text = re.sub(r'\[(BGM|묘사|지문|설명|배경|음악|CHAPTER|챕터|SFX):?.*?\]', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\[(대사|지문|묘사|설명)\]', '', text)
    text = re.sub(r'\(.*?\)', '', text)
    symbols = ['*', '-', '#', '@', '+', '=', '>', '<', '|', '/', '\\', '^']
    for s in symbols: text = text.replace(s, '')
    return text.strip()

def fix_initial_law(text):
    text = re.sub(r'(\d)\.(\d)', r'\1 쩜 \2', text)
    corrections = {"녀자": "여자", "래일": "내일", "리용": "이용", "량심": "양심", "력사": "역사", "련합": "연합"}
    for wrong, right in corrections.items(): text = text.replace(wrong, right)
    return text

def format_srt_time(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

def save_audio_and_srt(wav, sr, text, output_path):
    try:
        temp_wav = output_path.replace(".mp3", ".temp.wav")
        sf.write(temp_wav, wav, sr)
        
        final_audio = AudioSegment.from_wav(temp_wav)
        total_duration_ms = len(final_audio)
        
        # 자막 생성
        sentences = re.split(r'(?<=[.!?])\s+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        total_chars = sum(len(s) for s in sentences)
        
        srt_path = output_path.replace(".mp3", ".srt")
        with open(srt_path, "w", encoding="utf-8-sig") as f:
            current_ms = 0
            for i, sent in enumerate(sentences):
                duration_ms = (len(sent) / total_chars) * total_duration_ms if total_chars > 0 else 0
                start_sec = current_ms / 1000.0
                end_sec = (current_ms + duration_ms) / 1000.0
                f.write(f"{i + 1}\n{format_srt_time(start_sec)} --> {format_srt_time(end_sec)}\n{sent}\n\n")
                current_ms += duration_ms

        final_audio.export(output_path, format="mp3", bitrate="192k")
        if os.path.exists(temp_wav): os.remove(temp_wav)
        return True
    except Exception as e:
        print(f"❌ 저장 오류: {str(e)}")
        return False

def split_text(text, max_chars=150):
    # 마침표, 물음표, 느낌표 뿐만 아니라 '쉼표'에서도 쪼개도록 수정 (부대표님 대본 맞춤형)
    sentences = re.split(r'(?<=[.!? ,])\s+', text)
    chunks = []
    current_chunk = ""
    for sentence in sentences:
        if len(current_chunk) + len(sentence) <= max_chars:
            current_chunk += (" " + sentence if current_chunk else sentence)
        else:
            if current_chunk: chunks.append(current_chunk.strip())
            current_chunk = sentence
    if current_chunk: chunks.append(current_chunk.strip())
    return chunks

if __name__ == "__main__":
    target_file = sys.argv[1] if len(sys.argv) > 1 else "/workspace/대본.txt"
    if not os.path.exists(target_file):
        print(f"❌ 대본 파일을 찾을 수 없습니다: {target_file}")
        sys.exit(1)

    with open(target_file, "r", encoding="utf-8") as f:
        script_text = f.read().strip()
    
    print(f"📄 총 {len(script_text)}자의 대본을 처리합니다.")
    # [ULTRA TURBO BATCH]
    # 부대표님의 로컬 경험대로 청크를 약 150자 단위로 쪼갭니다.
    # RTX 4000은 수많은 작은 청크를 한 번에(Parallel) 처리하는 데 최적화되어 있습니다.
    chunks = split_text(script_text, max_chars=150)
    print(f"📦 대본을 {len(chunks)}개의 파트로 나누었습니다 (약 150자 단위).")

    tts = get_tts_model()
    timestamp = datetime.now().strftime("%m%d_%H%M")
    
    # [BATCH GENERATION]
    print(f"🚀 {len(chunks)}개 대형 파트 동시 생성 중 (Full GPU Utilization)...")
    try:
        clean_chunks = [fix_initial_law(clean_for_output(c)) for c in chunks]
        wavs, sr = tts.generate_custom_voice(
            text=clean_chunks,
            speaker=SPEAKER,
            language="Korean",
            instruct=INSTRUCT
        )
        
        for i, (wav, text) in enumerate(zip(wavs, clean_chunks)):
            output_file = os.path.join(DOWNLOADS_DIR, f"Turbo_Qwen_{timestamp}_part{i+1:03d}.mp3")
            print(f"💾 저장 중 [{i+1}/{len(chunks)}]: {os.path.basename(output_file)}")
            save_audio_and_srt(wav, sr, text, output_file)
            
    except torch.cuda.OutOfMemoryError:
        print("🚨 CUDA OOM! 배치가 너무 큽니다. 개별 생성(Sequential)으로 전환합니다.")
        torch.cuda.empty_cache()
        for i, chunk in enumerate(chunks):
             clean_chunk = fix_initial_law(clean_for_output(chunk))
             output_file = os.path.join(DOWNLOADS_DIR, f"Fallback_Qwen_{timestamp}_part{i+1:03d}.mp3")
             print(f"🚀 [Fallback {i+1}/{len(chunks)}] 생성 중...")
             wavs, sr = tts.generate_custom_voice(text=clean_chunk, speaker=SPEAKER, language="Korean", instruct=INSTRUCT)
             save_audio_and_srt(wavs[0], sr, clean_chunk, output_file)

    print(f"\n✨ 모든 작업 완료!")
    print(f"📂 저장 위치: {DOWNLOADS_DIR}")

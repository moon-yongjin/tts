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

# Add paths to find qwen_tts (Using the apple-silicon optimized repo)
REPO_DIR = "/Users/a12/projects/tts/qwen3-tts-apple-silicon/Qwen3-TTS"
sys.path.append(REPO_DIR)

# Import local components for registration
from qwen_tts import Qwen3TTSModel
from qwen_tts.core.models import Qwen3TTSConfig, Qwen3TTSForConditionalGeneration, Qwen3TTSProcessor
from transformers import AutoConfig, AutoModel, AutoProcessor

# [Registration] This is critical for transformers to recognize the local model type
AutoConfig.register("qwen3_tts", Qwen3TTSConfig)
AutoModel.register(Qwen3TTSConfig, Qwen3TTSForConditionalGeneration)
AutoProcessor.register(Qwen3TTSConfig, Qwen3TTSProcessor)

# [세팅]
# 이미 로컬 캐시에 있는 MLX-Community 모델 경로를 직접 사용합니다. (다운로드 방지)
MODEL_ID = "/Users/a12/.cache/huggingface/hub/models--mlx-community--Qwen3-TTS-12Hz-1.7B-Base-bf16/snapshots/a6eb4f68e4b056f1215157bb696209bc82a6db48"
REF_AUDIO = os.path.expanduser("~/Downloads/Voice_Assets/voice_sample_clean.wav")
REF_TEXT_FILE = os.path.expanduser("~/Downloads/Voice_Assets/voice_sample.txt")
SCRIPT_FILE = os.path.expanduser("~/projects/tts/대본.txt")
OUTPUT_DIR = os.path.expanduser("~/Downloads")

def get_tts_model():
    print(f"📡 Qwen-TTS Base 엔진 로딩 중 (LOCAL CACHE): {MODEL_ID}")
    try:
        # Mac (M4 Pro) 환경: bfloat16 + local_files_only=True
        model = Qwen3TTSModel.from_pretrained(
            MODEL_ID,
            torch_dtype=torch.bfloat16,
            device_map="auto",
            trust_remote_code=True,
            local_files_only=True
        )
        return model
    except Exception as e:
        print(f"❌ 모델 로딩 실패: {e}")
        return None

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

def main():
    if not os.path.exists(REF_AUDIO):
        print(f"❌ 레퍼런스 오디오가 없습니다: {REF_AUDIO}")
        return
    
    with open(REF_TEXT_FILE, "r", encoding="utf-8") as f:
        ref_text = f.read().strip()
    
    with open(SCRIPT_FILE, "r", encoding="utf-8") as f:
        target_text = f.read().strip()
    
    print(f"🎙️ 레퍼런스 텍스트 읽기 완료: {ref_text[:30]}...")
    print(f"📄 대상 대본 읽기 완료 ({len(target_text)}자)")

    tts = get_tts_model()
    if not tts: return

    timestamp = datetime.now().strftime("%m%d_%H%M")
    output_path = os.path.join(OUTPUT_DIR, f"ZeroShot_Local_Test_{timestamp}.mp3")

    print("🚀 로컬 제로샷 음성 생성 시작...")
    try:
        # 대본이 너무 길면 첫 200자만 테스트로 생성
        test_text = target_text[:200]
        processed_text = fix_initial_law(clean_for_output(test_text))
        
        print(f"📝 생성 텍스트: {processed_text}")
        
        wavs, sr = tts.generate_voice_clone(
            text=processed_text,
            language="Korean",
            ref_audio=REF_AUDIO,
            ref_text=ref_text
        )
        
        temp_wav = output_path.replace(".mp3", ".temp.wav")
        sf.write(temp_wav, wavs[0], sr)
        audio = AudioSegment.from_wav(temp_wav)
        audio.export(output_path, format="mp3", bitrate="192k")
        if os.path.exists(temp_wav): os.remove(temp_wav)
        
        print(f"✅ 생성 완료! 저장 위치: {output_path}")

    except Exception as e:
        print(f"❌ 생성 도중 에러 발생: {e}")

if __name__ == "__main__":
    main()

import torch
import soundfile as sf
import os
import sys

# 프로젝트 경로 추가
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

from qwen_tts import Qwen3TTSModel, Qwen3TTSTokenizer

# Configuration
MODEL_ID = "Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign"
OUTPUT_PATH = "local_voice_design_test.wav"
TEXT = "안녕하세요, 1.7B 보이스 디자인 기능을 로컬에서 테스트하고 있습니다. 60대 여성의 목소리로 생성 중입니다."
INSTRUCT = "A 60-year-old woman with a calm, gentle, and warm voice, speaking clearly in Korean."

def run_local_test():
    print(f"🚀 [LOCAL VOICE DESIGN] 가동 중: {MODEL_ID}")
    
    # Device detection (Mac MPS)
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    print(f"💻 Device: {device}")
    
    # Load model and tokenizer
    # Note: Using float16 for MPS compatibility and speed
    tokenizer = Qwen3TTSTokenizer.from_pretrained(MODEL_ID, trust_remote_code=True)
    model = Qwen3TTSModel.from_pretrained(
        MODEL_ID, 
        torch_dtype=torch.float16,
        device_map=device,
        trust_remote_code=True
    )
    
    # Generate
    print("⏳ 생성 중 (Voice Design)...")
    with torch.no_grad():
        # generate_voice_design API 사용
        wavs, sr = model.generate_voice_design(
            text=TEXT,
            instruct=INSTRUCT,
            language="Korean",
            tokenizer=tokenizer,
            max_new_tokens=2048,
            do_sample=True,
            top_p=0.8,
            temperature=0.8
        )
    
    # Save
    if wavs:
        sf.write(OUTPUT_PATH, wavs[0], sr)
        print(f"✅ 테스트 완료! 저장 위치: {os.path.abspath(OUTPUT_PATH)}")
    else:
        print("❌ 생성 실패: 결과값이 없습니다.")

if __name__ == "__main__":
    try:
        run_local_test()
    except Exception as e:
        print(f"❌ 에러 발생: {e}")
        import traceback
        traceback.print_exc()

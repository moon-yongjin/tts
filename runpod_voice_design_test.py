import torch
import os
import sys
import numpy as np
import soundfile as sf

# 프로젝트 경로 추가 (qwen_tts 패키지 위치)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))
from qwen_tts import Qwen3TTSModel

# Configuration
MODEL_ID = "Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign" 
OUTPUT_PATH = "voice_design_60s_woman.wav"

def run_voice_design_test():
    print(f"🚀 [1.7B VOICE DESIGN] 가동 중: {MODEL_ID}")
    
    try:
        # Qwen3TTSModel.from_pretrained 내부에서 AutoConfig/AutoModel/AutoProcessor를 알아서 등록합니다.
        # transformers v5.1.0에서 AutoProcessor는 인식이 잘 됩니다.
        model = Qwen3TTSModel.from_pretrained(
            MODEL_ID, 
            torch_dtype=torch.bfloat16,
            device_map="cuda",
            trust_remote_code=True
        )
        
        # Text and Instruction
        text = "안녕하세요. 저는 올해로 환갑을 맞이한 60대 여성입니다. 세월의 깊이가 느껴지면서도 따뜻하고 인자한 목소리로 녹음해보고 싶어요. 잘 들리시나요?"
        instruct = "60-year-old female voice, calm, warm, and natural speaking pace, slightly husky tone."
        
        print(f"📝 입력 텍스트: {text}")
        print(f"🎨 디자인 지시어: {instruct}")
        
        # Generate
        wavs, sr = model.generate_voice_design(
            text=text,
            instruct=instruct,
            language="auto"
        )
        
        # Save output
        if wavs:
            sf.write(OUTPUT_PATH, wavs[0], sr)
            print(f"✅ 생성 완료: {OUTPUT_PATH}")
        else:
            print("❌ 오디오 생성 실패 (wavs empty)")
            
    except Exception as e:
        print(f"❌ 에러 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_voice_design_test()

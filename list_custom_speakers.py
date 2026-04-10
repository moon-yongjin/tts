import torch
import os
import sys

# 프로젝트 경로 추가
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

from qwen_tts import Qwen3TTSModel

# Configuration
MODEL_ID = "Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice"

def list_speakers():
    print(f"🚀 [CUSTOM VOICE] 스피커 목록 확인 중: {MODEL_ID}")
    
    # Device detection (Mac MPS)
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    
    # Load model wrapper
    # Using trust_remote_code=True
    model = Qwen3TTSModel.from_pretrained(
        MODEL_ID, 
        torch_dtype=torch.float16,
        device_map=device,
        trust_remote_code=True
    )
    
    # Get speakers
    speakers = model.model.get_supported_speakers()
    print(f"✅ 지원되는 스피커 ({len(speakers)}명):")
    for s in sorted(speakers):
        print(f"- {s}")

if __name__ == "__main__":
    try:
        # OpenMP workaround
        os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
        list_speakers()
    except Exception as e:
        print(f"❌ 에러 발생: {e}")


import sys
import os
import torch
import soundfile as sf
from datetime import datetime

# Add current directory to path to find qwen_tts
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

print("🚀 Testing Qwen3-TTS on RTX 4090...")

try:
    from qwen_tts import Qwen3TTSModel
except ImportError as e:
    print(f"❌ Failed to import qwen_tts: {e}")
    sys.exit(1)

# Configuration
MODEL_ID = "Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice" 
SPEAKER = "sohee"
TEXT = "안녕하세요, 이것은 RTX 4090 서버에서 생성된 테스트 음성입니다."
INSTRUCT = "A clear and professional voice of a female AI assistant."
OUTPUT_FILE = "test_voice_4090.wav"

def test_gen():
    print(f"📡 Loading Model: {MODEL_ID}")
    try:
        model = Qwen3TTSModel.from_pretrained(
            MODEL_ID,
            torch_dtype=torch.bfloat16, # RTX 4090 supports bfloat16
            device_map="cuda"
        )
        print("✅ Model loaded successfully on GPU!")
    except Exception as e:
        print(f"❌ Model load failed: {e}")
        print("Trying auto device map...")
        model = Qwen3TTSModel.from_pretrained(MODEL_ID, device_map="auto")

    print(f"🎤 Generating text: {TEXT}")
    try:
        wavs, sr = model.generate_custom_voice(
            text=[TEXT],
            speaker=SPEAKER,
            language="Korean",
            instruct=INSTRUCT
        )
        
        sf.write(OUTPUT_FILE, wavs[0], sr)
        print(f"💾 Saved to {OUTPUT_FILE}")
        return True
    except Exception as e:
        print(f"❌ Generation failed: {e}")
        return False

if __name__ == "__main__":
    test_gen()

import torch
import time
import soundfile as sf
from qwen_tts import Qwen3TTSModel

MODEL_ID = "Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice"
device = "mps" if torch.backends.mps.is_available() else "cpu"
dtype = torch.bfloat16 if device == "mps" else torch.float32

print(f"🚀 Benchmarking on {device} ({dtype})...")
start_load = time.time()
model = Qwen3TTSModel.from_pretrained(MODEL_ID, device_map=device, torch_dtype=dtype)
print(f"✅ Load time: {time.time() - start_load:.2f}s")

test_text = "안녕하세요. 지금은 맥 미니 M4 프로에서 큐원 티티에스 속도 테스트를 진행하고 있습니다. 얼마나 빠른지 확인해 봅시다."
print(f"🎙️ Generating: '{test_text}'")

start_gen = time.time()
with torch.inference_mode():
    wavs, sr = model.generate_custom_voice(
        text=test_text, 
        speaker="sohee", 
        language="Korean", 
        instruct="A clear and professional voice."
    )
gen_time = time.time() - start_gen
print(f"⚡ Generation time: {gen_time:.2f}s")

audio_len = len(wavs[0]) / sr
print(f"⏱️ Audio length: {audio_len:.2f}s")
print(f"✨ RTF (Real-Time Factor): {gen_time / audio_len:.4f} (Lower is better)")

from huggingface_hub import hf_hub_download
import os

MODEL_DIR = "/Users/a12/projects/tts/ComfyUI/models/checkpoints"
os.makedirs(MODEL_DIR, exist_ok=True)

print("⬇️ Flux1 Dev FP8 다운로드 시작 (약 17GB)...")
model_path = hf_hub_download(
    repo_id="Kijai/flux-fp8",
    filename="flux1-dev-fp8.safetensors",
    local_dir=MODEL_DIR,
    local_dir_use_symlinks=False
)
print(f"✅ 다운로드 완료: {model_path}")

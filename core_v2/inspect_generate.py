import inspect
from mlx_audio.tts import load
from pathlib import Path

PROJECT_ROOT = Path("/Users/a12/projects/tts/qwen3-tts-apple-silicon")
MODEL_PATH = PROJECT_ROOT / "models/Qwen3-TTS-12Hz-1.7B-Base-8bit"

def main():
    if not MODEL_PATH.exists():
        print(f"❌ 모델 없음: {MODEL_PATH}")
        return

    print("🚀 모델 로딩 중...")
    try:
        model = load(str(MODEL_PATH))
        print("\n=== [model.generate Signature] ===")
        sig = inspect.signature(model.generate)
        for name, param in sig.parameters.items():
            print(f" - {name}: {param.default if param.default is not inspect.Parameter.empty else 'Required'}")
        print("==================================\n")
        
        # hasattr 체크
        print(f"Speed 속성 지원 여부: {'speed' in sig.parameters}")
        
    except Exception as e:
        print(f"❌ 에러: {e}")

if __name__ == "__main__":
    main()

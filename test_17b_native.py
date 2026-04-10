import torch
import soundfile as sf
from qwen_tts import Qwen3TTSModel, Qwen3TTSTokenizer, VoiceClonePromptItem

# Configuration
MODEL_ID = "Qwen/Qwen3-TTS-12Hz-1.7B-Base"
VOICE_PATH = "/workspace/Qwen3-TTS/voices/golden_voice_8.wav"
OUTPUT_PATH = "/workspace/Qwen3-TTS/voice_test_1.7b.wav"
TEXT = "안녕하세요, 이 목소리는 1.7B 모델로 런팟 서버에서 직접 생성한 테스트 음성입니다. 품질이 아주 훌륭하네요!"

def run_test():
    print(f"🚀 [1.7B TEST] 가동 중: {MODEL_ID}")
    
    # Load model and tokenizer
    tokenizer = Qwen3TTSTokenizer.from_pretrained(MODEL_ID, trust_remote_code=True)
    model = Qwen3TTSModel.from_pretrained(
        MODEL_ID, 
        torch_dtype=torch.bfloat16,
        device_map="cuda",
        trust_remote_code=True
    )
    model.eval()

    # Prepare voice clone prompt
    prompt = [
        VoiceClonePromptItem(
            audio_path=VOICE_PATH,
            text="레퍼런스 오디오 분석용 텍스트입니다." # Reference text for cloning
        )
    ]

    # Generate
    print("⏳ 생성 중...")
    with torch.no_grad():
        output = model.generate(
            texts=[TEXT],
            prompts=[prompt],
            tokenizer=tokenizer,
            max_new_tokens=2048,
            do_sample=True,
            top_p=0.8,
            temperature=0.8
        )
    
    # Process output
    audio_data = output[0].cpu().numpy()
    sr = 24000 # 12Hz model usually outputs 24kHz or similar, check model config if needed
    
    # Save
    sf.write(OUTPUT_PATH, audio_data, sr)
    print(f"✅ 테스트 완료! 저장 위치: {OUTPUT_PATH}")

if __name__ == "__main__":
    try:
        run_test()
    except Exception as e:
        print(f"❌ 에러 발생: {e}")

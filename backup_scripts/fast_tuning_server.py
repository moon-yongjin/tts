from qwen_tts import Qwen3TTSModel
import torch
import soundfile as sf
import os
import sys

def interactive_tuning():
    model_id = "Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice"
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    
    print(f"\n🚀 [Fast Tuning] Qwen-TTS 모델 로딩 중 ({device})...")
    print("⏳ 최초 1회 로딩은 약 30초~1분 정도 소요됩니다.")
    model = Qwen3TTSModel.from_pretrained(model_id, device_map=device)
    print("✅ 로딩 완료! 이제 즉시 목소리를 만들 수 있습니다.")

    # 기본값 설정
    speaker = "sohee"
    # 최초 요청된 비장함 70% 공기 설정
    instruct = "An extremely breathy and airy voice of a 40-year-old woman. The tone is solemn, tragic, and grave, as if speaking with a heavy heart."
    
    print("\n" + "="*50)
    print("🎤 [Qwen-TTS 실시간 튜닝 모드]")
    print(f"👤 현재 성우: {speaker}")
    print(f"📜 현재 지침: {instruct}")
    print("명령어: '!s 성우이름' (성우변경), '!i 지침내용' (지침변경), 'exit' (종료)")
    print("="*50)

    count = 1
    while True:
        try:
            user_input = input(f"\n[{count}] 대본을 입력하세요 (또는 명령어): ").strip()
        except EOFError:
            break
        
        if not user_input:
            continue
        if user_input.lower() == 'exit':
            break
        
        if user_input.startswith("!s "):
            speaker = user_input[3:].strip()
            print(f"✅ 성우가 '{speaker}'로 변경되었습니다.")
            continue
            
        if user_input.startswith("!i "):
            instruct = user_input[3:].strip()
            print(f"✅ 지침이 '{instruct}'로 변경되었습니다.")
            continue

        print("⚡ 생성 중...")
        try:
            wavs, sr = model.generate_custom_voice(
                text=user_input,
                speaker=speaker,
                language="Korean",
                instruct=instruct
            )
            
            output_path = f"tuning_sample_{count}.wav"
            sf.write(output_path, wavs[0], sr)
            print(f"✅ 생성 완료: {os.path.abspath(output_path)}")
            
            # 맥에서 즉시 들어볼 수 있게 실행
            os.system(f"afplay '{output_path}' &")
            
            count += 1
        except Exception as e:
            print(f"❌ 오류 발생: {e}")

if __name__ == "__main__":
    interactive_tuning()

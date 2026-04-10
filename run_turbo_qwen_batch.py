import os
import sys
import torch
import soundfile as sf
import numpy as np
import time
from qwen_tts import Qwen3TTSModel

def main(script_file):
    device = "cuda" if torch.cuda.is_available() else "cpu"
    ref_audio_path = "/workspace/Qwen3-TTS/golden_voice_8.wav"
    MODEL_ID = "Qwen/Qwen3-TTS-12Hz-1.7B-Base"
    BATCH_SIZE = 4  # [SPEED UP] 1.7B 모델은 4~8개가 적당함
    
    print(f"🚀 [CLEAN & FAST MODE] Qwen3 엔진 가동: {MODEL_ID}")
    print(f"💻 Device: {device}, Precision: bfloat16, Batch Size: {BATCH_SIZE}")
    
    if not os.path.exists(ref_audio_path):
        print(f"❌ 에러: {ref_audio_path} 파일을 찾을 수 없습니다.")
        return

    try:
        # 모델 로딩 (가속기가 잘 잡히는지 확인)
        model = Qwen3TTSModel.from_pretrained(
            MODEL_ID, 
            device_map=device, 
            torch_dtype=torch.bfloat16
        )
    except Exception as e:
        print(f"❌ 모델 로드 실패: {e}")
        return

    print(f"🎙️ 레퍼런스 오디오 분석 중...")
    try:
        prompt = model.create_voice_clone_prompt(
            ref_text="레퍼런스 오디오 분석용 텍스트입니다.", 
            ref_audio=ref_audio_path
        )
    except Exception as e:
        print(f"⚠️ 프롬프트 생성 실패: {e}")
        return

    if not os.path.exists(script_file):
        print(f"❌ 대본 파일이 없다: {script_file}")
        return

    with open(script_file, "r", encoding="utf-8") as f:
        lines = [l.strip() for l in f.readlines() if l.strip()]
    
    if not lines:
        print("⚠️ 대본에 처리할 문장이 없습니다.")
        return

    print(f"📝 총 {len(lines)}개 문장 고속 생성을 시작합니다.")
    
    start_time = time.time()
    
    # [BATCH ENHANCEMENT] 청크 단위로 나누어 병렬 처리
    for i in range(0, len(lines), BATCH_SIZE):
        batch_lines = lines[i : i + BATCH_SIZE]
        current_idxs = list(range(i + 1, i + 1 + len(batch_lines)))
        
        print(f"⏳ [{i+1}-{i+len(batch_lines)}/{len(lines)}] 병렬 생성 중...")
        
        try:
            with torch.no_grad():
                # 리스트 형태로 넘기면 엔진이 알아서 배치 처리함
                wavs, sr = model.generate_voice_clone(
                    text=batch_lines, 
                    voice_clone_prompt=prompt,
                    language="Korean"
                )
            
            if wavs and len(wavs) > 0:
                for j, wav in enumerate(wavs):
                    output_path = f"output_{current_idxs[j]}.wav"
                    if isinstance(wav, torch.Tensor):
                        wav = wav.cpu().numpy()
                    sf.write(output_path, wav, sr)
                    print(f"   ✅ 저장 완료: {output_path}")
            else:
                print(f"   ⚠️ 배치 생성 결과가 비어있습니다.")

        except Exception as e:
            print(f"   ❌ 배치 처리 중 에러 발생: {e}")
            torch.cuda.empty_cache()
            # 에러 발생 시 안전하게 1개씩 재시도 (필요 시)
        
    end_time = time.time()
    print(f"✨ 모든 작업 완료! (소요 시간: {end_time - start_time:.2f}초)")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("사용법: python3 run_turbo_qwen_batch.py 대본.txt")
    else:
        main(sys.argv[1])

import os
import sys
import torch
import numpy as np
import soundfile as sf
from pathlib import Path
from loguru import logger
import datetime

# v1.5.1 경로 대응
sys.path.insert(0, "/Users/a12/projects/tts/fish-speech-s1/repo")
os.environ["PYTHONPATH"] = "/Users/a12/projects/tts/fish-speech-s1/repo"

from fish_speech.models.text2semantic.llama import BaseTransformer
from fish_speech.models.text2semantic.inference import load_model as load_llama
from fish_speech.models.vqgan.inference import load_model as load_firefly

# === 설정 구간 ===
DEVICE = "mps"
CHECKPOINT_DIR = Path("/Users/a12/projects/tts/fish-speech-s1/repo/checkpoints/fish-speech-1.5")
LLAMA_CKPT = CHECKPOINT_DIR  # Directory
FIREFLY_CKPT = CHECKPOINT_DIR / "firefly-gan-vq-fsq-8x1024-21hz-generator.pth"
CONFIG_NAME = "s1_mini_firefly"  # 512차원 최적화 설정
DOWNLOADS_DIR = Path.home() / "Downloads"

@torch.inference_mode()
def run_factory(script_text, output_path):
    # 1. 환경 정리
    precision = torch.float16  # M4 Pro 가속용
    logger.info("🚀 Muhyup Factory 가동: M4 Pro 전용 엔진 로딩 중...")

    # 2. 모델 로드 (1회만 수행)
    logger.info("📡 Llama (Text2Semantic) 로딩...")
    llama_model, decode_one_token = load_llama(
        checkpoint_path=str(LLAMA_CKPT),
        device=DEVICE,
        precision=precision,
        compile=False
    )
    
    logger.info("📡 Firefly (VQGAN) 로딩...")
    firefly_model = load_firefly(CONFIG_NAME, str(FIREFLY_CKPT), device=DEVICE)
    
    # 가중치 이름에 21hz가 있으면 21000, 아니면 44100
    sr = 21000 if "21hz" in str(FIREFLY_CKPT) else 44100
    logger.info(f"✅ 모델 로드 완료. 샘플 레이트: {sr}Hz")

    # 3. 텍스트 처리
    logger.info(f"📝 대본 길이: {len(script_text)} 자")
    
    # fish_speech의 generate_long 사용
    from fish_speech.models.text2semantic.inference import generate_long
    
    try:
        logger.info(f"🔍 입력 텍스트 길이: {len(script_text)}")
        generator = generate_long(
            model=llama_model,
            device=DEVICE,
            decode_one_token=decode_one_token,
            text=script_text,
            num_samples=1,
            max_new_tokens=2048,
            top_p=0.7,
            repetition_penalty=1.2,
            temperature=0.7,
            compile=False,
            iterative_prompt=True,
            chunk_length=200,
            prompt_text=None,
            prompt_tokens=None
        )

        all_audios = []
        chunk_count = 0
        found = False
        logger.info("🎙️ 음성 합성 시작 (RTF 측정 중...)")
        
        for idx, result in enumerate(generator):
            found = True
            
            # [핵심] 루프가 돌 때마다 KV 캐시를 현재 입력 크기에 맞게 리셋한다.
            # 8191과 56의 충돌을 원천 차단하는 '뇌세척' 작업이다.
            with torch.device(DEVICE):
                llama_model.setup_caches(
                    max_batch_size=1,
                    max_seq_len=llama_model.config.max_seq_len,  # 기본 8192
                    dtype=next(llama_model.parameters()).dtype
                )
            
            logger.info(f"🐟 청크 {idx + 1} 처리 중... (result type: {type(result)})")
            
            # result는 GenerationResult 객체
            if hasattr(result, 'codes') and result.codes is not None:
                indices = result.codes  # [num_codebooks, seq_len]
                logger.info(f"   📊 Codes shape: {indices.shape}")
                
                # Stage 2: 코드를 오디오로 즉시 변환
                feature_lengths = torch.tensor([indices.shape[1]], device=DEVICE, dtype=torch.long)
                fake_audios, _ = firefly_model.decode(
                    indices=indices[None].long(), 
                    feature_lengths=feature_lengths
                )
                
                chunk = fake_audios[0, 0].float().cpu().numpy()
                all_audios.append(chunk)
                chunk_count += 1
                
                if hasattr(result, 'text'):
                    logger.info(f"✔️ 청크 {chunk_count} 합성 완료: {result.text[:30]}...")
                else:
                    logger.info(f"✔️ 청크 {chunk_count} 합성 완료")
            else:
                logger.warning(f"⚠️ 청크 {idx + 1}에 codes가 없음 (action: {getattr(result, 'action', 'N/A')})")
        
        if not found:
            logger.error("❌ Generator가 아무런 응답도 생성하지 않았습니다!")
            
    except Exception as e:
        logger.error(f"🔥 치명적 에러 발생: {e}")
        import traceback
        logger.error(f"📋 Traceback:\n{traceback.format_exc()}")
        raise


    # 4. 결과물 병합 및 저장
    if all_audios:
        final_wav = np.concatenate(all_audios)
        sf.write(output_path, final_wav, sr)
        logger.info(f"✨ 작업 종료! 파일 위치: {output_path}")
        logger.info(f"📊 총 {chunk_count}개 청크 생성, 최종 길이: {len(final_wav)/sr:.2f}초")
    else:
        logger.error("❌ 오디오 생성 실패")

if __name__ == "__main__":
    # 대본 읽기
    script_file = Path("/Users/a12/projects/tts/대본.txt")
    if not script_file.exists():
        logger.error(f"❌ 대본 파일 없음: {script_file}")
        sys.exit(1)
    
    with open(script_file, "r", encoding="utf-8") as f:
        script_text = f.read().strip()
    
    if not script_text:
        logger.error("❌ 빈 대본")
        sys.exit(1)
    
    # 출력 파일명
    timestamp = datetime.datetime.now().strftime("%m%d_%H%M")
    output_name = f"대본_Fish_S1_Optimized_{timestamp}.wav"
    output_path = DOWNLOADS_DIR / output_name
    
    logger.info(f"🎯 출력 파일: {output_path}")
    run_factory(script_text, str(output_path))

import os
import sys
import torch
import numpy as np
import soundfile as sf
from pathlib import Path
from loguru import logger
import datetime
import re

# v1.5.1 경로 대응
sys.path.insert(0, "/Users/a12/projects/tts/fish-speech-s1/repo")
os.environ["PYTHONPATH"] = "/Users/a12/projects/tts/fish-speech-s1/repo"

from fish_speech.models.text2semantic.inference import load_model as load_llama, generate
from fish_speech.models.vqgan.inference import load_model as load_firefly

# === 설정 구간 ===
DEVICE = "mps"
CHECKPOINT_DIR = Path("/Users/a12/projects/tts/fish-speech-s1/repo/checkpoints/fish-speech-1.5")
LLAMA_CKPT = CHECKPOINT_DIR  # Directory
FIREFLY_CKPT = CHECKPOINT_DIR / "firefly-gan-vq-fsq-8x1024-21hz-generator.pth"
CONFIG_NAME = "s1_mini_firefly"  # 512차원 최적화 설정
DOWNLOADS_DIR = Path.home() / "Downloads"

def split_into_chunks(text, max_length=200):
    """텍스트를 문장 단위로 청크 분할"""
    # 문장 단위로 분리
    sentences = re.split(r'([.!?]\s+)', text)
    chunks = []
    current_chunk = ""
    
    for i in range(0, len(sentences), 2):
        sentence = sentences[i]
        if i + 1 < len(sentences):
            sentence += sentences[i + 1]  # 구두점 포함
        
        if len(current_chunk) + len(sentence) > max_length and current_chunk:
            chunks.append(current_chunk.strip())
            current_chunk = sentence
        else:
            current_chunk += sentence
    
    if current_chunk.strip():
        chunks.append(current_chunk.strip())
    
    return chunks

@torch.inference_mode()
def run_factory_plan_b(script_text, output_path):
    # 1. 환경 정리
    precision = torch.float16  # M4 Pro 가속용
    logger.info("🚀 Muhyup Factory Plan B 가동: 청크별 루프 방식")

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
    
    sr = 21000 if "21hz" in str(FIREFLY_CKPT) else 44100
    logger.info(f"✅ 모델 로드 완료. 샘플 레이트: {sr}Hz")

    # 3. 텍스트를 청크로 분할
    chunks = split_into_chunks(script_text, max_length=200)
    logger.info(f"📝 총 {len(chunks)}개 청크로 분할 완료")

    all_audios = []
    
    try:
        for idx, chunk_text in enumerate(chunks):
            logger.info(f"🐟 청크 {idx + 1}/{len(chunks)} 처리 중: {chunk_text[:30]}...")
            
            # KV 캐시 리셋 (청크마다 깨끗한 상태로 시작)
            with torch.device(DEVICE):
                llama_model.setup_caches(
                    max_batch_size=1,
                    max_seq_len=llama_model.config.max_seq_len,
                    dtype=precision
                )
            
            # Stage 1: Text to Semantic (기본 generate 사용)
            result = next(generate(
                model=llama_model,
                device=DEVICE,
                decode_one_token=decode_one_token,
                text=chunk_text,
                num_samples=1,
                max_new_tokens=2048,
                top_p=0.7,
                repetition_penalty=1.2,
                temperature=0.7,
                compile=False
            ))
            
            if not hasattr(result, 'codes') or result.codes is None:
                logger.warning(f"⚠️ 청크 {idx + 1} 스킵: codes 없음")
                continue
            
            indices = result.codes
            logger.info(f"   📊 Codes shape: {indices.shape}")
            
            # Stage 2: Semantic to Audio (Firefly)
            feature_lengths = torch.tensor([indices.shape[1]], device=DEVICE, dtype=torch.long)
            fake_audios, _ = firefly_model.decode(
                indices=indices[None].long(), 
                feature_lengths=feature_lengths
            )
            
            chunk_audio = fake_audios[0, 0].float().cpu().numpy()
            all_audios.append(chunk_audio)
            logger.info(f"✔️ 청크 {idx + 1} 합성 완료 ({len(chunk_audio)/sr:.2f}초)")
            
    except Exception as e:
        logger.error(f"🔥 에러 발생: {e}")
        import traceback
        logger.error(f"📋 Traceback:\n{traceback.format_exc()}")
        raise

    # 4. 결과물 병합 및 저장
    if all_audios:
        final_wav = np.concatenate(all_audios)
        sf.write(output_path, final_wav, sr)
        logger.info(f"✨ 작업 종료! 파일 위치: {output_path}")
        logger.info(f"📊 총 {len(all_audios)}개 청크 생성, 최종 길이: {len(final_wav)/sr:.2f}초")
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
    output_name = f"대본_Fish_S1_PlanB_{timestamp}.wav"
    output_path = DOWNLOADS_DIR / output_name
    
    logger.info(f"🎯 출력 파일: {output_path}")
    logger.info(f"⏱️ 예상 소요 시간: 약 5분")
    
    import time
    start_time = time.time()
    run_factory_plan_b(script_text, str(output_path))
    elapsed = time.time() - start_time
    logger.info(f"🏁 총 소요 시간: {elapsed/60:.1f}분")

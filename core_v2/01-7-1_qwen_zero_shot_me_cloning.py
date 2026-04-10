import os
import sys
import time
import re
import datetime
import numpy as np
import soundfile as sf
import tempfile
import mlx.core as mx
from pydub import AudioSegment
from mlx_audio.tts import load
from pathlib import Path

# ==========================================================
# [사용자 설정 구역]
# ==========================================================
PROJ_ROOT = Path("/Users/a12/projects/tts")
DOWNLOADS_DIR = Path.home() / "Downloads"

# 1. 참조 오디오 및 대본 설정
REF_AUDIO_PATH = DOWNLOADS_DIR / "supertone_me_sample_10s.wav"
SCRIPT_PATH = PROJ_ROOT / "대본.txt"

# [핵심] 참조 오디오의 실제 대본 (ref_text)
REF_TEXT = "안녕하세요, 형님 목소리 클로닝 테스트 입니 다. 지금 이 목소리는 슈퍼톤 에이피아이를 통해 생성되고 있으며, 약 10초 정도의 샘플을 만들기 위해 적당한 길이의 문장을 낭독하고 있습니다."

# 2. 모델 설정
MODEL_ID = "/Users/a12/projects/tts/qwen3-tts-apple-silicon/models/Qwen3-TTS-12Hz-1.7B-Base-8bit"

# 3. 음성 스타일 설정
INSTRUCT = "신뢰감 있는 뉴스 아나운서 톤으로 정갈하고 힘 있게 낭독하세요."
SPEED = 1.2      
TEMP = 0.7       
TOP_P = 0.8

# 4. 문장 사이 쉬는 시간 (ms)
PAUSE_MS = 300   
# ==========================================================

class LocalQwenCloner:
    def __init__(self):
        print(f"🚀 [LOCAL] Qwen-Cloning 모델 로딩 중: {MODEL_ID}")
        self.model = load(MODEL_ID)
        print("✅ 모델 로딩 완료!")

    def split_text_into_chunks(self, text, max_chars=120):
        # 쉼표와 문장 부호 기준으로 쪼개기 (안정성 최적화)
        parts = re.split(r'([.!?,]\s*)', text)
        chunks = []
        current = ""
        for p in parts:
            if len(current) + len(p) < max_chars:
                current += p
            else:
                if current: chunks.append(current.strip())
                current = p
        if current: chunks.append(current.strip())
        return [c for c in chunks if c]

    def run(self):
        if not REF_AUDIO_PATH.exists():
            print(f"❌ 참조 오디오를 찾을 수 없습니다: {REF_AUDIO_PATH}")
            return

        if not SCRIPT_PATH.exists():
            print(f"❌ 대본 파일을 찾을 수 없습니다: {SCRIPT_PATH}")
            return

        with open(SCRIPT_PATH, "r", encoding="utf-8") as f:
            full_text = f.read().strip()
        
        # 텍스트 정규화
        full_text = full_text.replace("2편", "이편")
        
        chunks = self.split_text_into_chunks(full_text)
        print(f"📄 대본 분석 완료 -> {len(chunks)}개 파트로 생성 시작")

        combined_audio = AudioSegment.empty()
        
        for i, chunk in enumerate(chunks):
            print(f"🎙️  [{i+1}/{len(chunks)}] 클로닝 중: {chunk[:30]}...")
            
            try:
                results = self.model.generate(
                    text=chunk,
                    ref_audio=str(REF_AUDIO_PATH),
                    ref_text=REF_TEXT,
                    instruct=INSTRUCT,
                    speed=SPEED,
                    temperature=TEMP,
                    top_p=TOP_P
                )
                
                segment_audio_data = []
                for res in results:
                    segment_audio_data.append(res.audio)
                
                if not segment_audio_data: continue
                
                audio_np = np.concatenate(segment_audio_data)
                
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                    sf.write(tmp.name, audio_np, 24000)
                    audio_segment = AudioSegment.from_wav(tmp.name)
                os.unlink(tmp.name)

                # 병합
                pause = AudioSegment.silent(duration=PAUSE_MS)
                combined_audio += audio_segment + pause
                
            except Exception as e:
                print(f"   ❌ 파트 {i+1} 생성 중 오류 발생: {e}")

        # 최종 저장
        timestamp = datetime.datetime.now().strftime("%y%m%d_%H%M")
        output_path = DOWNLOADS_DIR / f"01-7-1제로샷_형님_{timestamp}.wav"
        
        combined_audio.export(output_path, format="wav")
        print(f"\n✨ 제로샷 클로닝 완료: {output_path}")

if __name__ == "__main__":
    cloner = LocalQwenCloner()
    cloner.run()

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
CORE_V2 = PROJ_ROOT / "core_v2"
DOWNLOADS_DIR = Path.home() / "Downloads"

# 1. 참조 오디오 및 대본 설정
REF_AUDIO_PATH = Path("/Users/a12/Downloads/final_promo_refined.wav")
SCRIPT_PATH = PROJ_ROOT / "대본.txt"

# [핵심] 참조 오디오의 실제 대본 (ref_text) - 15~30초 이상의 텍스트가 품질을 결정합니다.
REF_TEXT = (
    "현재 반도체 시장을 관통하는 키워드는 '자원 독점'입니다. 과거의 시장이 수요와 공급의 균형에 의해 움직였다면, 2026년의 시장은 AI라는 포식자가 하위 생택계의 자원을 강탈하는 구조입니다. "
    "삼성전자와 SK하이닉스가 HBM4와 같은 고부가가치 제품 생산에 사활을 걸면서, 여러분이 사용하는 PC용 램과 SSD는 더 이상 제조사의 우선순위가 아닙니다. "
    "이것은 일시적인 현상이 아니라, 2027년 말까지 지속될 구조적 결핍의 시작입니다. "
    "삼성전자가 2026년 2월 세계 최초로 6세대 HBM4 양산을 시작하며 기술적 반격에 나섰지만, 시장의 실질적 지배권은 여전히 엔비디아 물량의 70%를 확보한 SK하이닉스에게 있습니다. "
    "중요한 점은 이들의 전쟁 방식입니다. HBM 한 장을 만들 때 소모되는 웨이퍼는 일반 램의 3배에 달합니다. 이를 '웨이퍼 페널티'라 부릅니다. "
    "제조사들이 수익성 극대화를 위해 HBM에 집중할수록 소비자용 램의 생산량은 물리적으로 삭감될 수밖에 없습니다. "
    "여러분의 PC 사양이 하향 평준화되고 있는 근본 원인이 바로 여기 있습니다. "
    "글로벌 3사가 소비자 시장을 외면한 틈을 타, 중국의 CXMT와 YMTC가 소비자용 PC 시장의 새로운 기반으로 부상했습니다. "
    "델, HP, 에이수스 같은 글로벌 제조사들은 이제 물량 확보를 위해 중국산 메모리를 적극적으로 채택하고 있습니다. "
    "중국 또한 HBM3 양산에 돌입하며 기술 격차를 3년 이내로 좁혔습니다. 하지만 중국산 제품이 시장 가격을 낮춰줄 것이라는 기대는 버리십시오. "
    "이들 역시 수율 문제와 공정 비용 상승으로 인해 한국 제조사의 가격 인상 기조를 그대로 따르고 있습니다. "
    "2026년 현재 시장은 상식을 벗어난 '가격 역전' 상태입니다. 생산이 중단된 구형 DDR4의 현물가가 신형 DDR5보다 172% 이상 비싸게 거래되는 기현상이 발생했습니다. "
    "SSD 시장 또한 심각합니다. 기업용 고용량 SSD 수요가 폭발하면서 8TB 이상의 제품은 무게당 가격이 금값을 추월했습니다. "
    "제조사들이 낸드 플래시 출하량을 의도적으로 조절하고 있어, 소비자용 SSD 가격은 올 한 해에만 최대 100%까지 상승할 가능성이 큽니다. "
    "상황은 명확합니다. 공급자는 시장을 통제하고 있으며, AI 기업들은 향후 2년 치 물량을 이미 선점했습니다. "
    "하락을 기다리는 것은 데이터에 기반하지 않은 막연한 희망 고문일 뿐입니다. "
    "현재 가용한 예산 범위 내에서 DDR5 기반의 시스템을 즉시 구축하고 필요한 저장 장치를 선제적으로 확보하는 것이 기회비용을 최소화하는 유일한 최적의 루트입니다."
)

# 2. 모델 설정
MODEL_ID = "mlx-community/Qwen3-TTS-12Hz-1.7B-CustomVoice-bf16"

# 3. 음성 스타일 설정
INSTRUCT = "반도체 시장의 위기감이 서려 있는 매우 비장하고 묵직한 뉴스 리포터 톤으로 낭독하세요. 시청자에게 경고하듯 서늘하고 진중한 분위기를 유지하세요."
SPEED = 1.4      # 형님 요청: 1.4배속 적용
TEMP = 0.3       # 낮을수록 진중하고 안정적임

# 4. 문장 사이 쉬는 시간 (ms)
PAUSE_MS = 600   # 속도가 빨라졌으므로 쉼표 시간도 단축
# ==========================================================

class LocalQwenCloner:
    def __init__(self):
        print(f"🚀 [LOCAL] Qwen-Cloning 모델 로딩 중: {MODEL_ID}")
        self.model = load(MODEL_ID)
        print("✅ 모델 로딩 완료!")

    def clean_text(self, text):
        # 1. 지문 제거 (괄호 안 내용)
        text = re.sub(r'\(.*?\)', '', text)
        text = re.sub(r'\[.*?\]', '', text)
        # 2. 화자 이름 제거 (선비:, 여인: 등)
        text = re.sub(r'^[가-힣]+:\s*', '', text, flags=re.MULTILINE)
        return text.strip()

    def split_chunks(self, text):
        # [형님 요청] 모든 띄어쓰기마다 한 청크로 분리 (최대한 잘게)
        # re.split 대신 단순히 split()을 사용하여 단어 단위로 쪼갭니다.
        words = text.split()
        return [w.strip() for w in words if w.strip()]

    def run(self):
        if not REF_AUDIO_PATH.exists():
            print(f"❌ 참조 오디오를 찾을 수 없습니다: {REF_AUDIO_PATH}")
            return

        if not SCRIPT_PATH.exists():
            print(f"❌ 대본 파일을 찾을 수 없습니다: {SCRIPT_PATH}")
            return

        with open(SCRIPT_PATH, "r", encoding="utf-8") as f:
            full_text = f.read().strip()
        
        cleaned_text = self.clean_text(full_text)
        chunks = self.split_chunks(cleaned_text)
        print(f"📄 대본 분석 완료 ({len(full_text)}자) -> {len(chunks)}개 파트로 생성 시작")

        combined_audio = AudioSegment.empty()
        
        for i, chunk in enumerate(chunks):
            print(f"🎙️  [{i+1}/{len(chunks)}] 클로닝 중: {chunk[:30]}...")
            
            try:
                # Local MLX Zero-shot 생성 (ref_text 포함 최고 품질 모드)
                results = self.model.generate(
                    text=chunk,
                    voice="ryan",              # 사용 가능한 남성 목소리 'ryan'으로 변경
                    ref_audio=str(REF_AUDIO_PATH), # 로컬 참조 파일 경로
                    ref_text=REF_TEXT,         # [핵심] 참조 오디오의 실제 대본 추가
                    instruct=INSTRUCT,
                    speed=SPEED,
                    temperature=TEMP,
                    lang_code="ko"
                )
                
                segment_audio_mx = None
                for res in results:
                    if segment_audio_mx is None: 
                        segment_audio_mx = res.audio
                    else: 
                        segment_audio_mx = mx.concatenate([segment_audio_mx, res.audio])
                
                if segment_audio_mx is None: continue
                
                # NumPy 변환 및 pydub 변환
                audio_np = np.array(segment_audio_mx)
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                    sf.write(tmp.name, audio_np, 24000)
                    audio_segment = AudioSegment.from_wav(tmp.name)
                os.unlink(tmp.name)

                # 쉼표 추가 및 병합
                pause = AudioSegment.silent(duration=PAUSE_MS)
                combined_audio += audio_segment + pause
                
            except Exception as e:
                print(f"   ❌ 파트 {i+1} 생성 중 오류 발생: {e}")

        # 최종 저장
        timestamp = datetime.datetime.now().strftime("%m%d_%H%M")
        output_path = DOWNLOADS_DIR / f"Qwen_Local_Cloned_{timestamp}.wav"
        
        combined_audio.export(output_path, format="wav")
        print(f"\n✨ 로컬 클로닝 성공! 결과 파일 사수 완료:")
        print(f"📂 {output_path}")

if __name__ == "__main__":
    cloner = LocalQwenCloner()
    cloner.run()

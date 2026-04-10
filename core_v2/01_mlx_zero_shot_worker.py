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
# [설정] 다이내믹 피드 설정
# ==========================================================
PROJ_ROOT = Path("/Users/a12/projects/tts")
CORE_V2 = PROJ_ROOT / "core_v2"
DOWNLOADS_DIR = Path.home() / "Downloads"

REF_AUDIO_PATH = DOWNLOADS_DIR / "extracted_ref.wav"
TRANSCRIPT_PATH = DOWNLOADS_DIR / "extracted_ref_transcript.txt"
SCRIPT_PATH = PROJ_ROOT / "대본.txt"

# 모델 설정 (사용자 요청: 무조건 베이스 모델 사용)
PROJECT_ROOT_LOCAL = Path("/Users/a12/projects/tts/qwen3-tts-apple-silicon")
MODEL_PATH = PROJECT_ROOT_LOCAL / "models/Qwen3-TTS-12Hz-1.7B-Base-8bit"

# 성우 스타일
INSTRUCT = "반도체 시장의 진중하고 묵직한 뉴스 리포터 톤으로 낭독하세요. 차분하고 선명한 톤을 유지하세요."
SPEED = 1.3
TEMP = 0.3

# ------------------------------------------------------------------
# [신규 추가] 숫자 한글 발음 치환기 (Number Normalizer)
# ------------------------------------------------------------------
def number_to_korean(num_str):
    num_str = num_str.replace(',', '')
    if not num_str.isdigit(): return num_str
    try: num = int(num_str)
    except ValueError: return num_str

    if num == 0: return "영"
    units = ["", "십", "백", "천"]
    large_units = ["", "만", "억", "조", "경"]
    digits = ["", "일", "이", "삼", "사", "오", "육", "칠", "팔", "구"]

    result = ""
    str_num = str(num)
    length = len(str_num)

    for i, d in enumerate(str_num):
        digit = int(d)
        if digit != 0:
            pos = length - 1 - i
            unit_pos = pos % 4
            large_unit_pos = pos // 4
            digit_str = digits[digit]
            if unit_pos > 0 and digit == 1: digit_str = ""
            result += digit_str + units[unit_pos]

        pos = length - 1 - i
        if pos > 0 and pos % 4 == 0:
            if large_unit_pos > 0 and any(int(x) > 0 for x in str_num[max(0, i-3):i+1]):
                 if not result.endswith(large_units[large_unit_pos]): result += large_units[large_unit_pos]

    if result.startswith("일십"): result = result[1:]
    if result.startswith("일백"): result = result[1:]
    if result.startswith("일천"): result = result[1:]
    return result

def normalize_numbers(text):
    pattern = r'\d+(?:,\d+)*'
    def replacer(match): return number_to_korean(match.group(0))
    return re.sub(pattern, replacer, text)

# ------------------------------------------------------------------

def clean_text(text):
    text = normalize_numbers(text) # 숫자 치환 적용
    text = re.sub(r'\(.*?\)', '', text)
    text = re.sub(r'\[.*?\]', '', text)
    return text.strip()

def split_chunks(text):
    return [w.strip() for w in text.split() if w.strip()]

def main():
    if not REF_AUDIO_PATH.exists():
        print(f"❌ 참조 오디오 피드를 찾을 수 없습니다: {REF_AUDIO_PATH}")
        return

    if not TRANSCRIPT_PATH.exists():
        print(f"❌ 녹취 텍스트가 없습니다. 녹취를 먼저 진행하세요.")
        return

    # 녹취 파일 로드
    with open(TRANSCRIPT_PATH, "r", encoding="utf-8") as f:
        ref_text = f.read().strip()
    
    if not ref_text:
         print("❌ 녹취 텍스트가 비어 있습니다.")
         return

    print(f"✅ [Reference] 오디오 및 녹취 텍스트 로드 성공")
    print(f"   🎙️ 오디오: {REF_AUDIO_PATH}")
    print(f"   📜 텍스트: {ref_text[:100]}...\n")

    if not SCRIPT_PATH.exists():
        print(f"❌ 대본 파일이 없습니다: {SCRIPT_PATH}")
        return

    with open(SCRIPT_PATH, "r", encoding="utf-8") as f:
        script_content = f.read().strip()

    cleaned_text = clean_text(script_content)
    chunks = split_chunks(cleaned_text)
    
    # 디버그: 너무 자잘하게 쪼개지면 chunk 단위 묶음 시도 가능하지만, 
    # 일단 단어 단위(01-7 로직) 그대로 계승합니다.
    print(f"📄 대본 내용 분석 완료 -> {len(chunks)}개 파트 생성 시작")

    print(f"🚀 [LOCAL] Qwen-Cloning 모델 로딩 중: {MODEL_PATH.name}")
    try:
        model = load(str(MODEL_PATH))
    except Exception as e:
         print(f"❌ 모델 로드 실패: {e}")
         return
         
    combined_audio = AudioSegment.empty()
    print("🎬 본격적인 제로샷 클로닝을 가동합니다...")

    for i, chunk in enumerate(chunks):
        print(f"🎙️  [{i+1}/{len(chunks)}] 클로닝 중: {chunk[:30]}...")
        
        try:
            results = model.generate(
                text=chunk,
                voice="ryan", # Qwen3-TTS zero-shot 구조
                ref_audio=str(REF_AUDIO_PATH),
                ref_text=ref_text,
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
            
            audio_np = np.array(segment_audio_mx)
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                sf.write(tmp.name, audio_np, 24000)
                audio_segment = AudioSegment.from_wav(tmp.name)
            os.unlink(tmp.name)

            pause = AudioSegment.silent(duration=500)
            combined_audio += audio_segment + pause
            
        except Exception as e:
            print(f"   ❌ 파트 {i+1} 생성 중 오류: {e}")

    timestamp = datetime.datetime.now().strftime("%m%d_%H%M")
    output_path = DOWNLOADS_DIR / f"Qwen_Auto_ZeroShot_{timestamp}.wav"
    
    combined_audio.export(output_path, format="wav")
    print(f"\n✨ 제로샷 목소리 복제 성공! 결과 파일 사수:")
    print(f"📂 {output_path}")

if __name__ == "__main__":
    main()

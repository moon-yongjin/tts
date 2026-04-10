import os
import sys
import re
import mlx.core as mx
from mlx_audio.tts import load
import numpy as np
import soundfile as sf
import librosa
import tempfile
from pydub import AudioSegment
from pydub.silence import detect_leading_silence
import datetime
import subprocess
from pathlib import Path

# 🎙️ Qwen3-TTS [통합 듀얼스피커 파이프라인 V1]

# 1. 경로 설정
PROJECT_ROOT = Path("/Users/a12/projects/tts/qwen3-tts-apple-silicon")
MODEL_PATH = PROJECT_ROOT / "models/Qwen3-TTS-12Hz-1.7B-Base-8bit"
sys.path.append(str(PROJECT_ROOT))

TARGET_SCRIPT_PATH = Path("/Users/a12/projects/tts/대본.txt")
OUTPUT_DIR = Path.home() / "Downloads"

# 2. 음성 프리셋 설정 (1-3-92와 동일 세팅)
VOICES = {
    "1": {
        "name": "새 레퍼런스 (금융/비즈니스 차분한 톤)",
        "file": "/Users/a12/projects/tts/voices/Reference_Audios/Screen_Recording_20260318_050504_YouTube_extracted.wav",
        "text": "보면 매출 자체는 나쁘지가 않아요. 656억 정도로 매출은 굉장히 잘 나오지만 일단 비용이 너무 높습니다. 영업 비용만 해도 946억이 나와서 영업 손실이 나고 있는 회사예요.",
        "speed": 1.1
    },
    "2": {
        "name": "인강샘 (비즈니스/강사 또박또박한 톤)",
        "file": "/Users/a12/projects/tts/voices/Reference_Videos/Screen_Recording_20260318_040927_YouTube.mp4",
        "text": "사람들은 20달러가 동일한 가치처럼 느껴지겠지만 실제적으로 우리가 판매를 할 때 크로스보더 셀러, 우리 역직구의 셀러들은 이익을 더 많이 볼 수 있다라고.",
        "speed": 1.1
    },
    "3": {
        "name": "클래식언니 (유튜브 나레이션 톤)",
        "file": "/Users/a12/projects/tts/voices/Reference_Videos/ClassicUnni_Ref.mp4",
        "text": "안녕하세요, 오늘 전해드릴 소식은 유튜브 화면 녹화 영상을 기반으로 한 인공지능 음성 복제 기술입니다.",
        "speed": 1.0
    },
    "4": {
        "name": "강지영3 (아나운서 톤)",
        "file": "/Users/a12/projects/tts/voices/Reference_Videos/KangJiYoung3_Ref.mp4",
        "text": "강지영 아나운서 스타일의 목소리 톤을 참고하기 위한 레퍼런스 데이터입니다.",
        "speed": 1.0
    },
    "5": {
        "name": "감성_슬픔 (드라마/복수 추천 톤)",
        "file": "/Users/a12/projects/tts/voices/Reference_Audios/Woman4_감성_슬픔_Clean.wav",
        "text": "아버지가 인팀 전이 많지가 되셔서 돌아오셨고 있는 모든 걸 그냥 다 두신 그런 날만 되면은 저희는 책가방을 싸들고 있다가 새벽 2시나 새벽 3시쯤 어디론가 다 숨어야되는 옆집의 소리가 들리까봐 아버지가 TV 볼륨을 맥스로 올리고 폭행이 시작되어서 초등학교 3학년 때 엄마가 집을 나가셨어요.",
        "speed": 1.0
    },
    "6": {
        "name": "슬슬이 (틱톡 숏폼 / 대화톤)",
        "file": "/Users/a12/projects/tts/voices/Reference_Videos/Screen_Recording_20260322_013938_TikTok-Lite.mp4",
        "text": "BTS 공연을 간다고요? 그냥 거기를 지나간다고요? 잠시만요. 아래 캡션에 광화문 근처 관련",
        "speed": 1.0
    },
    "7": {
        "name": "교통방송 (차분한 나레이션 톤)",
        "file": "/Users/a12/projects/tts/voices/Reference_Audios/Traffic_Broadcasting.wav",
        "text": "내륙 중심으로 아침 기온은 영하권의 기온을 보이는 곳이 많아서 이맘때와 아침 기온이 비슷하거나 조금은 낮겠습니다.",
        "speed": 1.1
    },
    "8": {
        "name": "오디오북 (픽업트럭 감성 톤)",
        "file": "/Users/a12/projects/tts/voices/Reference_Audios/Audiobook.wav",
        "text": "픽업트럭 한 대가 먼지를 일으키며 사라져갔다. 거친 밥에 목이 메었다. 다리를 심하게",
        "speed": 1.1
    },
    "9": {
        "name": "오디오1 (주민회 회장 톤)",
        "file": "/Users/a12/projects/tts/reference_audio_3.wav",
        "text": "술 더 떠서 주민회 회장까지 한다는 것이었다. 또다시 전화와 인터폰을 왕래하느라 입맛이 떨어져 아침에 설친 그는 주민회 회장까지 한다는 것이었다.",
        "speed": 1.1
    }
}

def trim_silence(audio, threshold=-50.0, padding_ms=200):
    start_trim = detect_leading_silence(audio, silence_threshold=threshold)
    duration = len(audio)
    trimmed = audio[start_trim:duration] 
    silence = AudioSegment.silent(duration=padding_ms)
    return silence + trimmed.fade_out(10) + silence

def normalize_text(text):
    text = text.replace('“', '"').replace('”', '"').replace('‘', "'").replace('’', "'")
    text = text.replace('"', '').replace("'", "")
    text = text.replace('. ', '.').replace('.', '.. ') # 🚀 마침표 3개 연달아 찍기 (호흡 확장)
    text = text.replace("외양간", "외양깐").replace("땅바닥", "땅빠닥").replace("임명장", "임명짱")
    
    # 🔢 [숫자 일괄 한글화 - 지침 보강 버전]
    # 1. 한자어(Sino) 매칭: 년, 위, 일, 부, 편, 달러, 원, 분
    sino_map = {'1':'일','2':'이','3':'삼','4':'사','5':'오','6':'육','7':'칠','8':'팔','9':'구','10':'십','20':'이십'}
    text = re.sub(r'(\d+)(년|위|일|부|편|달러|원|분|개월)', 
                  lambda m: sino_map.get(m.group(1), m.group(1)) + m.group(2), text)
    
    # 2. 고유어(Native) 매칭: 시, 살, 번, 명, 개
    native_map = {'1':'한','2':'두','3':'세','4':'네','5':'다섯','6':'여섯','7':'일곱','8':'여덟','9':'아홉','10':'열',
                  '11':'열한','12':'열두','20':'스무'}
    text = re.sub(r'(\d+)(시|살|번|명|개)', 
                  lambda m: native_map.get(m.group(1), m.group(1)) + m.group(2), text)
    
    # 3. 쌩 숫자 단독 처리 (예: 10, 20)
    text = text.replace(" 10 ", " 열 ").replace(" 20 ", " 스무 ").replace(" 10.", " 열.").replace(" 20.", " 스무.")
    
    return text

def format_srt_time(seconds):
    td = datetime.timedelta(seconds=seconds)
    hours = int(td.total_seconds()) // 3600
    minutes = (int(td.total_seconds()) % 3600) // 60
    secs = int(td.total_seconds()) % 60
    millis = int(td.microseconds / 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

def split_chunks_single_role(text, max_chars=180):
    text = text.replace('\r\n', '\n').replace('\n\n', ' _DOUBLE_BREAK_ ')
    text = text.replace('\n', ' ')
    blocks = text.split(' _DOUBLE_BREAK_ ')
    final_chunks = []
    for block in blocks:
        block = block.strip()
        if not block: continue
        sentences = re.findall(r'[^,!?\s][^,!?\n]*[.!?,\n]*', block)
        current_chunk = ""
        for s in sentences:
            s = s.strip()
            if not s: continue
            if len(s) > max_chars:
                words = s.split(" ")
                for w in words:
                    if not w: continue
                    if len(current_chunk) + len(w) + 1 <= max_chars: current_chunk = (current_chunk + " " + w).strip()
                    else:
                        if current_chunk: final_chunks.append(current_chunk)
                        current_chunk = w
            else:
                if len(current_chunk) + len(s) + 1 <= max_chars: current_chunk = (current_chunk + " " + s).strip()
                else:
                    if current_chunk: final_chunks.append(current_chunk)
                    current_chunk = s
        if current_chunk: final_chunks.append(current_chunk)
    return [c.strip() for c in final_chunks if c.strip()]

def split_chunks_dual_advanced(text, max_chars=180):
    # 🎯 인라인 따옴표 분파 렌더러
    parts = re.split(r'("[^"]*")', text)
    result = []
    for p in parts:
        if not p: continue
        role = "dialogue" if p.startswith('"') else "narration"
        clean_text = p.replace('"', '').strip()
        if not clean_text: continue
        sub_chunks = split_chunks_single_role(clean_text, max_chars)
        for sc in sub_chunks:
            result.append({"role": role, "text": sc.strip()})
    return result

def main():
    print("\n==========================================")
    print("🎙️ Qwen3-TTS [선택형 인라인 듀얼스피커 파이프라인 V1]")
    print("==========================================")

    print("\n[ 📂 사용 가능한 목소리 프리셋 목록 ]")
    for key, info in VOICES.items():
        print(f"  [{key}] {info['name']}")
    
    choice_nav = input("\n▶️ 1. [나레이션](따옴표 밖) 목소리 번호 (1-9): ").strip()
    choice_dia = input("▶️ 2. [따옴표 대사](따옴표 안) 목소리 번호 (1-9): ").strip()

    if choice_nav not in VOICES or choice_dia not in VOICES:
        print("\n❌ 잘못된 선택입니다. 가동을 종료합니다.")
        return

    nav_preset = VOICES[choice_nav]
    dia_preset = VOICES[choice_dia]
    print(f"\n✅ 배정 완료:")
    print(f"  • 나레이터: {nav_preset['name']}")
    print(f"  • 대사 화자: {dia_preset['name']}\n")

    if not TARGET_SCRIPT_PATH.exists():
        print(f"❌ 대본 파일이 없습니다: {TARGET_SCRIPT_PATH}")
        return

    with open(TARGET_SCRIPT_PATH, "r", encoding="utf-8") as f:
        target_text = f.read().strip()

    # 따옴표 규격화
    target_text = target_text.replace('“', '"').replace('”', '"')
    chunks = split_chunks_dual_advanced(target_text)
    
    print(f"📄 총 {len(chunks)}개의 피스(Piece) 분리 완료. 생성 시작...")
    print(f"🚀 모델 로딩 중...")
    model = load(str(MODEL_PATH))

    combined_audio = AudioSegment.empty()
    srt_entries = []
    current_time_sec = 0.0
    PAUSE_MS = 500 

    try:
        for i, piece in enumerate(chunks):
            role = piece["role"]
            text = normalize_text(piece["text"])
            if not text.rstrip().endswith(('.', '!', '?', '..')):
                text = text.rstrip() + ".. "  # 💡 끝음절 잘림 방지용 마침표 강제 보정
            else:
                text = text.rstrip() + " "  # 💡 끝음절 잘림 방지용 여유 공백 추가
            active_preset = nav_preset if role == "narration" else dia_preset
            speed_factor = active_preset.get("speed", 1.0)

            print(f"🎙️  [{i+1}/{len(chunks)}] [{role}] 생성 중: {text[:30]}...")

            ref_wav, sr = librosa.load(active_preset["file"], sr=24000)
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                sf.write(tmp.name, ref_wav, sr)
                temp_ref_path = tmp.name

            try:
                results = model.generate(
                    text=text,
                    ref_audio=temp_ref_path,
                    ref_text=active_preset["text"], 
                    language="Korean",
                    temperature=0.8,
                    top_p=0.9,
                    speed=speed_factor
                )

                segment_audio_mx = None
                for res in results:
                    if segment_audio_mx is None: segment_audio_mx = res.audio
                    else: segment_audio_mx = mx.concatenate([segment_audio_mx, res.audio])
                
                if segment_audio_mx is not None:
                    audio_np = np.array(segment_audio_mx)
                    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as stmp:
                        sf.write(stmp.name, audio_np, 24000)
                        stmp_path = stmp.name
                    
                    segment_pydub = AudioSegment.from_wav(stmp_path)
                    os.unlink(stmp_path)
                    segment_pydub = trim_silence(segment_pydub)
                    
                    duration_sec = len(segment_pydub) / 1000.0
                    srt_entries.append(f"{i+1}\n{format_srt_time(current_time_sec)} --> {format_srt_time(current_time_sec + duration_sec)}\n{piece['text']}\n\n")
                    
                    combined_audio += segment_pydub + AudioSegment.silent(duration=PAUSE_MS)
                    current_time_sec += duration_sec + (PAUSE_MS / 1000.0)
                    
            finally:
                 if os.path.exists(temp_ref_path): os.unlink(temp_ref_path)

        if len(combined_audio) > 0:
            timestamp = datetime.datetime.now().strftime("%H%M%S")
            output_name = f"인라인듀얼_결과물_{timestamp}.wav"
            output_path = OUTPUT_DIR / output_name
            combined_audio.export(str(output_path), format="wav")
            with open(str(output_path).replace(".wav", ".srt"), "w", encoding="utf-8-sig") as f: f.writelines(srt_entries)
            print(f"\n✅ 생성 완료: {output_path}")

            print("\n✂️ [자동화] 자막 분할 후작업 가동 중...")
            sub_split_script = "/Users/a12/projects/tts/core_v2/04_srt_subsplitter.py"
            if os.path.exists(sub_split_script):
                 subprocess.run([sys.executable, sub_split_script])

        else: print("\n⚠️ 생성 실패")

    except Exception as e: print(f"❌ 에러 발생: {str(e)}")

if __name__ == "__main__":
    main()

import os
import sys
import re
from pathlib import Path
import mlx.core as mx
from mlx_audio.tts import load
import numpy as np
import soundfile as sf
import librosa
import tempfile
from pydub import AudioSegment
from pydub.silence import detect_leading_silence
import datetime

# 1. 경로 설정
PROJECT_ROOT = Path("/Users/a12/projects/tts/qwen3-tts-apple-silicon")
MODEL_PATH = PROJECT_ROOT / "models/Qwen3-TTS-12Hz-1.7B-Base-8bit"
sys.path.append(str(PROJECT_ROOT))

TARGET_SCRIPT_PATH = Path("/Users/a12/projects/tts/대본.txt")
OUTPUT_DIR = Path.home() / "Downloads"

# 2. 음성 프리셋 설정
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
        "file": "/Users/a12/projects/tts/voices/Reference_Audios/Woman4_감성_슬픔.wav",
        "text": "아버지가 인팀 전이 많지가 되셔서 돌아오셨고 있는 모든 걸 그냥 다 두신 그런 날만 되면은 저희는 책가방을 싸들고 있다가 새벽 2시나 새벽 3시쯤 어디론가 다 숨어야되는 옆집의 소리가 들리까봐 아버지가 TV 볼륨을 맥스로 올리고 폭행이 시작되어서 초등학교 3학년 때 엄마가 집을 나가셨어요.",
        "speed": 1.0
    },
    "6": {
        "name": "슬슬이 (틱톡 숏폼 / 대화톤)",
        "file": "/Users/a12/projects/tts/voices/Reference_Videos/Screen_Recording_20260322_013938_TikTok-Lite.mp4",
        "text": "BTS 공연을 간다고요? 그냥 거기를 지나간다고요? 잠시만요. 아래 캡션에 광화문 근처 관련",
        "speed": 1.0
    },
    "10": {
        "name": "TikTokLite (0405 - 뉴스/연설)",
        "file": "/Users/a12/projects/tts/1-3_ZeroShot_Studio/voices/Reference/TikTokLite_0405_Ref.wav",
        "text": "결단력 있고 실행력 보이고 있는 이재명 정부와 밀어주시다.",
        "speed": 1.1
    },
    "11": {
        "name": "YouTube (0403 - 생활/대화)",
        "file": "/Users/a12/projects/tts/1-3_ZeroShot_Studio/voices/Reference/YouTube_0403_Ref.wav",
        "text": "그렇지? 그래도 말만 존경하니 뭐니 직접 해봐야 느끼고 아는 거지.",
        "speed": 1.0
    }
}

def trim_silence(audio, threshold=-50.0, padding_ms=200):
    start_trim = detect_leading_silence(audio, silence_threshold=threshold)
    end_trim = max(0, detect_leading_silence(audio.reverse(), silence_threshold=threshold) - 100)
    duration = len(audio)
    trimmed = audio[start_trim:max(start_trim+1, duration-end_trim)]
    silence = AudioSegment.silent(duration=padding_ms)
    return silence + trimmed.fade_out(80) + silence

def normalize_text(text):
    text = text.replace('“', '"').replace('”', '"').replace('‘', "'").replace('’', "'")
    text = text.replace('"', '').replace("'", "")
    text = text.replace('. ', '.').replace('.', '.. ') # 🚀 마침표 뒤 강제 스페이스
    text = text.replace("외양간", "외양깐").replace("땅바닥", "땅빠닥")
    
    num_to_sino = {'1':'일','2':'이','3':'삼','4':'사','5':'오','6':'육','7':'칠','8':'팔','9':'구','10':'십','20':'이십'}
    text = re.sub(r'(\d+)(일|부|편|달러|원)', lambda m: num_to_sino.get(m.group(1), m.group(1)) + m.group(2), text)
    return text

def format_srt_time(seconds):
    td = datetime.timedelta(seconds=seconds)
    hours = int(td.total_seconds()) // 3600
    minutes = (int(td.total_seconds()) % 3600) // 60
    secs = int(td.total_seconds()) % 60
    millis = int(td.microseconds / 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

def split_chunks(text, max_chars=100):
    lines = text.splitlines()
    final_chunks = []
    for line in lines:
        line = line.strip()
        if not line: continue
        sentences = re.findall(r'[^,!?\s][^,!?\n]*[,!?\n]*', line)
        current_chunk = ""
        for s in sentences:
            s = s.strip()
            if not s: continue
            if len(current_chunk) + len(s) + 1 <= max_chars: current_chunk = (current_chunk + " " + s).strip()
            else:
                if current_chunk: final_chunks.append(current_chunk)
                current_chunk = s
        if current_chunk: final_chunks.append(current_chunk)
    return [c.strip() for c in final_chunks if c.strip()]

def main():
    print("\n==========================================")
    print("🎙️ Qwen3-TTS [대화형 음성 선택 렌더러]")
    print("==========================================")

    # 1. 음성 선택 메뉴 출력
    print("\n🔊 사용할 음성을 선택하세요:")
    for key, info in VOICES.items():
        print(f"  [{key}] {info['name']}")
    
    choice = input("\n👉 번호를 입력하세요: ").strip()

    if choice not in VOICES:
        print("\n❌ 잘못된 선택입니다. 가동을 종료합니다.")
        return

    selected_voice = VOICES[choice]
    print(f"\n✅ 선택된 보이스: {selected_voice['name']}")

    # 2. 대본 확인
    if not TARGET_SCRIPT_PATH.exists():
        print(f"❌ 대본 파일이 없습니다: {TARGET_SCRIPT_PATH}")
        return

    with open(TARGET_SCRIPT_PATH, "r", encoding="utf-8") as f:
        target_text = f.read().strip()

    if not target_text:
        print("\n❌ 대본 내용이 없습니다.")
        return

    print(f"\n📄 대본 전처리 중... (총 {len(target_text)}자)")
    target_text = normalize_text(target_text)
    chunks = split_chunks(target_text)
    print(f"📄 총 {len(chunks)}개의 파트로 대본 처리 시작...")

    print(f"\n🚀 모델 로딩 중...")
    model = load(str(MODEL_PATH))

    # 레퍼런스 오디오 검증
    if not os.path.exists(selected_voice["file"]):
        print(f"❌ 레퍼런스 오디오가 없습니다: {selected_voice['file']}")
        return

    ref_wav, sr = librosa.load(selected_voice["file"], sr=24000)
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        sf.write(tmp.name, ref_wav, sr)
        temp_ref_path = tmp.name

    combined_audio = AudioSegment.empty()
    srt_entries = []
    current_time_sec = 0.0
    PAUSE_MS = 500 

    try:
        for i, chunk in enumerate(chunks):
            print(f"🎙️  [{i+1}/{len(chunks)}] 생성 중: {chunk[:40]}...")
            
            results = model.generate(
                text=chunk,
                ref_audio=temp_ref_path,
                ref_text=selected_voice["text"], 
                language="Korean",
                temperature=0.8,
                top_p=0.9,
                speed=selected_voice["speed"]
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
                srt_entries.append(f"{i+1}\n{format_srt_time(current_time_sec)} --> {format_srt_time(current_time_sec + duration_sec)}\n{chunk}\n\n")
                
                combined_audio += segment_pydub + AudioSegment.silent(duration=PAUSE_MS)
                current_time_sec += duration_sec + (PAUSE_MS / 1000.0)

        if len(combined_audio) > 0:
            timestamp = datetime.datetime.now().strftime("%H%M%S")
            output_prefix = selected_voice["name"].split("(")[0].strip().replace(" ", "_")
            output_path = OUTPUT_DIR / f"{output_prefix}_결과물_{timestamp}.wav"
            combined_audio.export(str(output_path), format="wav")
            
            srt_path = str(output_path).replace(".wav", ".srt")
            with open(srt_path, "w", encoding="utf-8-sig") as f: f.writelines(srt_entries)
            
            print(f"\n✅ 생성 완료: {output_path}")
        else:
            print("\n⚠️ 생성 실패")

    except Exception as e:
        print(f"❌ 에러 발생: {str(e)}")
    finally:
        if os.path.exists(temp_ref_path): os.unlink(temp_ref_path)

if __name__ == "__main__":
    main()

import os
import requests
import json
import re
import datetime
from pathlib import Path
from dotenv import load_dotenv
from pydub import AudioSegment
from pydub.silence import detect_leading_silence

# 1. 경로 설정
PROJECT_ROOT = Path("/Users/a12/projects/tts")
CORE_V2_DIR = PROJECT_ROOT / "core_v2"
load_dotenv(os.path.join(CORE_V2_DIR, ".env"))

# 2. SUPERTONE 설정
SUPERTONE_API_KEY = os.getenv("SUPERTONE_API_KEY")
VOICE_ID = "7cJefRzkxbqgbVgT4ZGmAU" # 국장님이 주신 앵그리남자 ID

# 3. 대본 및 출력 설정
TARGET_SCRIPT_PATH = PROJECT_ROOT / "대본.txt"
DOWNLOADS_PATH = Path.home() / "Downloads"

# 발음 사전 (기존 마스터 지침 유지)
PRON_DICTIONARY = {
    "HBM4": "에이치비엠 포",
    "HBM": "에이치비엠",
    "SSD": "에스에스디",
    "복리": "봉니", # 발음 교정 예시
}
def supertone_tts(text, output_path):
    """Supertone API를 사용하여 텍스트를 음성으로 변환 (Angry 고정 설정)"""
    url = f"https://supertoneapi.com/v1/text-to-speech/{VOICE_ID}"
    headers = {
        "x-sup-api-key": SUPERTONE_API_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "text": text,
        "language": "ko",
        "model": "sona_speech_1",
        "voice_settings": {
            "speed": 1.4,        
            "pitch_shift": 1,     
            "pitch_variance": 1.5 
        },
        "style": "Angry"
    }
    try:
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            with open(output_path, "wb") as f:
                f.write(response.content)
            return True
        else:
            print(f"❌ API 에러: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"⚠️ 요청 오류: {e}")
        return False


def trim_silence(audio, threshold=-50.0, padding_ms=150):
    """음성 앞뒤 침묵 제거 및 끝부분 페이드 아웃 처리 (뚝 끊김 방지)"""
    start_trim = detect_leading_silence(audio, silence_threshold=threshold)
    end_trim = detect_leading_silence(audio.reverse(), silence_threshold=threshold)
    duration = len(audio)
    trimmed = audio[start_trim:max(start_trim+1, duration-end_trim)]
    
    silence = AudioSegment.silent(duration=padding_ms)
    # 끝부분 100ms 페이드 아웃으로 부드럽게 종료
    return silence + trimmed.fade_out(100) + silence

def normalize_text(text):
    """TTS 발음 교정 및 특수 기호 정규화"""
    # [1] 스마트 따옴표 및 따옴표 제거 (Supertone이 읽을 때 어색함 방지)
    text = re.sub(r'[\"“]「(.*?)[\"”]」', r'\1', text) # 따옴표 안의 내용만 추출 (복합형)
    text = text.replace('“', '"').replace('”', '"').replace('‘', "'").replace('’', "'")
    
    # [2] '숫자 + 편' 교정 (2편 -> 이편)
    num_to_sino = {
        '1': '일', '2': '이', '3': '삼', '4': '사', '5': '오',
        '6': '육', '7': '칠', '8': '팔', '9': '구', '10': '십'
    }
    def replace_pyeon(match):
        num = match.group(1)
        sino = num_to_sino.get(num, num)
        return f"{sino}편"
    text = re.sub(r'(\d+)편', replace_pyeon, text)
    
    # [3] 기존 발음 사전 적용
    for target, pron in PRON_DICTIONARY.items():
        text = text.replace(target, pron)
        
    return text

def format_srt_time(ms):
    td = datetime.timedelta(milliseconds=ms)
    total_seconds = int(td.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60
    millis = int(td.microseconds / 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

def split_chunks(text, max_chars=120):
    sentences = re.split(r'([.!?,\n]\s*)', text)
    chunks = []
    current = ""
    for p in sentences:
        if len(current) + len(p) <= max_chars:
            current += p
        else:
            if current: chunks.append(current.strip())
            current = p
    if current: chunks.append(current.strip())
    return [c for c in chunks if c]

def main():
    print("==========================================")
    print("🎙️ Supertone AI [Angry Male] Voice (01-3-56)")
    print("==========================================")

    if not SUPERTONE_API_KEY:
        print("❌ 에러: SUPERTONE_API_KEY가 .env에 없습니다.")
        return

    if not TARGET_SCRIPT_PATH.exists():
        print(f"❌ 에러: 대본 파일이 없습니다: {TARGET_SCRIPT_PATH}")
        return

    with open(TARGET_SCRIPT_PATH, "r", encoding="utf-8") as f:
        full_text = f.read().strip()

    full_text = normalize_text(full_text)
    chunks = split_chunks(full_text)
    print(f"📄 총 {len(chunks)}개의 파트로 대본 처리 시작...")

    final_audio = AudioSegment.empty()
    srt_entries = []
    current_time_ms = 0
    PAUSE_MS = 400

    for i, chunk in enumerate(chunks):
        print(f"🎙️  [{i+1}/{len(chunks)}] 생성 중: {chunk[:30]}...")
        temp_wav = f"temp_supertone_{i}.wav"
        
        if supertone_tts(chunk, temp_wav):
            raw_seg = AudioSegment.from_wav(temp_wav)
            # [수정] 침묵 제거 및 페이드 아웃 적용 (01-3-7-1 로직 이식)
            audio_seg = trim_silence(raw_seg)
            
            duration_ms = len(audio_seg)
            
            start_time = format_srt_time(current_time_ms)
            end_time = format_srt_time(current_time_ms + duration_ms)
            srt_entries.append(f"{i+1}\n{start_time} --> {end_time}\n{chunk}\n\n")
            
            final_audio += audio_seg + AudioSegment.silent(duration=PAUSE_MS)
            current_time_ms += duration_ms + PAUSE_MS
            
            os.remove(temp_wav)
        else:
            print(f"⚠️ [{i+1}] 생성 실패. 건너뜁니다.")

    if len(final_audio) > 0:
        now = datetime.datetime.now().strftime("%H%M%S")
        output_audio = DOWNLOADS_PATH / f"Supertone_AngryMale_01-3-56_{now}.wav"
        output_srt = DOWNLOADS_PATH / f"Supertone_AngryMale_01-3-56_{now}.srt"
        
        final_audio.export(str(output_audio), format="wav")
        with open(output_srt, "w", encoding="utf-8-sig") as f:
            f.writelines(srt_entries)
            
        print(f"\n✅ 완료! {output_audio}")
        os.system(f"open {DOWNLOADS_PATH}")
    else:
        print("⚠️ 최종 음성 합성에 실패했습니다.")

if __name__ == "__main__":
    main()

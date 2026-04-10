import os
import requests
import json
import re
import datetime
from pydub import AudioSegment
from pathlib import Path

# 설정 파일에서 API 키 로드
PROJ_ROOT = Path("/Users/a12/projects/tts")
CORE_V2 = PROJ_ROOT / "core_v2"
ENV_PATH = CORE_V2 / ".env"
SUPERTONE_API_KEY = None

if ENV_PATH.exists():
    with open(ENV_PATH, "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("SUPERTONE_API_KEY="):
                SUPERTONE_API_KEY = line.split("=")[1].strip().strip('"').strip("'")

if not SUPERTONE_API_KEY:
    print("❌ SUPERTONE_API_KEY를 .env에서 찾을 수 없습니다.")
    exit(1)
VOICES = {
    "chloe": "6HL8gGg8PYdE8qDpTbF26E", # 클로이 (사용자 클로닝 보이스)
    "taeyang": "12bab70236ce079bb0e4ea" # 태양
}

# 비밀 발음 사전
PRON_DICTIONARY = {
    "HBM4": "에이치비엠 포",
    "HBM3": "에이치비엠 쓰리",
    "DDR5": "디디알 파이브",
    "8TB": "팔 테라바이트",
    "SSD": "에스에스디",
    "H100": "에이치 백",
    "B200": "비 이백",
    "CXMT": "씨엑스엠티",
    "YMTC": "와이엠티씨",
    "HBM": "에이치비엠",
    "PC": "피씨",
    "RAM": "램",
    "DDR4": "디디알 포",
}

def supertone_tts(text, voice_type="chloe", speed=1.0, output_path=None):
    """Supertone API를 사용하여 텍스트를 음성으로 변환"""
    voice_id = VOICES.get(voice_type, VOICES["chloe"])
    url = f"https://supertoneapi.com/v1/text-to-speech/{voice_id}"
    
    headers = {
        "x-sup-api-key": SUPERTONE_API_KEY,
        "Content-Type": "application/json"
    }
    
    # 발음 사전을 적용하여 텍스트 치환
    processed_text = text
    for target, pron in PRON_DICTIONARY.items():
        processed_text = processed_text.replace(target, pron)

    payload = {
        "text": processed_text,
        "language": "ko",
        "model": "sona_speech_1",
        "voice_settings": {
            "speed": speed
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            with open(output_path, "wb") as f:
                f.write(response.content)
            return True
        else:
            print(f"❌ API 에러 [{voice_type}]: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"⚠️ 요청 오류: {e}")
        return False

def format_srt_time(ms):
    """밀리초를 SRT 시간 포맷(HH:MM:SS,mmm)으로 변환"""
    seconds = int((ms / 1000) % 60)
    minutes = int((ms / (1000 * 60)) % 60)
    hours = int((ms / (1000 * 60 * 60)) % 24)
    millis = int(ms % 1000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{millis:03d}"

def split_text_into_chunks(text, max_chars=250):
    """마침표 기준으로 쪼개고, 너무 긴 문장 대응"""
    raw_sentences = re.split(r'(?<=[.?!])\s+', text)
    chunks = []
    
    for sentence in raw_sentences:
        sentence = sentence.strip()
        if not sentence: continue
        
        if len(sentence) <= max_chars:
            chunks.append(sentence)
        else:
            for i in range(0, len(sentence), max_chars):
                chunks.append(sentence[i:i+max_chars])
                
    return chunks

def process_chloe_gen(input_script_path):
    """클로이 보이스로 전체 대본 생성"""
    timestamp = datetime.datetime.now().strftime("%y%m%d_%H%M")
    downloads_path = os.path.expanduser("~/Downloads")
    output_audio_name = os.path.join(downloads_path, f"01-25클로이_엄마의연주_{timestamp}.wav")
    output_srt_name = os.path.join(downloads_path, f"01-25클로이_엄마의연주_{timestamp}.srt")

    if not os.path.exists(input_script_path):
        print(f"❌ 대본 파일을 찾을 수 없습니다: {input_script_path}")
        return

    with open(input_script_path, "r", encoding="utf-8") as f:
        full_text = f.read().strip()

    # 따옴표 제거 및 클린업
    clean_text = full_text.replace('"', '').replace("'", "")
    chunks = split_text_into_chunks(clean_text)
    
    segments = []
    for chunk in chunks:
        segments.append({
            "text": chunk, 
            "voice": "chloe",
            "speed": 1.0 # 감성적인 사연이므로 정속도로 생성
        })

    final_audio = AudioSegment.empty()
    current_time_ms = 0
    srt_content = []

    print(f"🎯 [클로이 전용 생성] 총 {len(segments)}개의 청크 생성 시작")

    for i, seg in enumerate(segments):
        temp_wav = f"temp_chloe_{i}.wav"
        success = supertone_tts(seg["text"], voice_type=seg["voice"], speed=seg["speed"], output_path=temp_wav)
        
        if success:
            audio_seg = AudioSegment.from_wav(temp_wav)
            duration_ms = len(audio_seg)
            
            start_time = format_srt_time(current_time_ms)
            end_time = format_srt_time(current_time_ms + duration_ms)
            srt_content.append(f"{i+1}\n{start_time} --> {end_time}\n{seg['text']}\n")
            
            final_audio += audio_seg
            current_time_ms += duration_ms
            
            if os.path.exists(temp_wav):
                os.remove(temp_wav)
            print(f"✅ [{i+1}/{len(segments)}] 생성 완료 - {duration_ms/1000:.2f}초")
        else:
            print(f"❌ [{i+1}/{len(segments)}] 생성 중단.")
            return

    # 결과물 저장
    final_audio.export(output_audio_name, format="wav")
    with open(output_srt_name, "w", encoding="utf-8") as f:
        f.writelines("\n".join(srt_content))

    print(f"\n✨ 클로이 보이스 생성 완료!")
    print(f"🎬 오디오: {output_audio_name}")
    print(f"📜 자막: {output_srt_name}")

if __name__ == "__main__":
    script_path = "/Users/a12/projects/tts/대본.txt"
    process_chloe_gen(script_path)

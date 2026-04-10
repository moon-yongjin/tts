import os
import requests
import json
import re
from dotenv import load_dotenv
from pydub import AudioSegment

# .env 파일에서 API 키 로드
load_dotenv()

# SUPERTONE 설정
SUPERTONE_API_KEY = os.getenv("SUPERTONE_API_KEY")
VOICES = {
    "chloe": "6HL8gGg8PYdE8qDpTbF26E",    # 클로이 (감성 보이스)
    "taeyang": "12bab70236ce079bb0e4ea"  # 태양 (정통 성우)
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

def supertone_tts(text, voice_type="chloe", speed=1.0, style=None, pitch_shift=0, pitch_variance=1.0, output_path=None):
    """Supertone API를 사용하여 텍스트를 음성으로 변환 (감정/스타일 지원)"""
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
            "speed": speed,
            "pitch_shift": pitch_shift,
            "pitch_variance": pitch_variance
        }
    }
    
    # 스타일(감정)이 지정된 경우 추가
    if style:
        payload["style"] = style
    
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

def split_text_into_chunks(text, max_chars=280):
    """마침표 및 쉼표 기준으로 쪼개고, 너무 긴 문장은 추가로 쪼갬"""
    # 문장 종결 어미 및 쉼표로 분리 (마침표, 물음표, 느낌표, 쉼표)
    raw_sentences = re.split(r'(?<=[.?!,])\s+', text)
    chunks = []
    
    for sentence in raw_sentences:
        sentence = sentence.strip()
        if not sentence: continue
        
        if len(sentence) <= max_chars:
            chunks.append(sentence)
        else:
            # 한 문장이 너무 길면 강제로 자름
            for i in range(0, len(sentence), max_chars):
                chunks.append(sentence[i:i+max_chars])
                
    return chunks

def process_promotion_video(input_script_path, voice_type="taeyang"):
    """대본을 분석하여 목소리별 생성 및 자막 합체 (발음 사전 및 다운로드 폴더 저장)"""
    # 다운로드 폴더 경로 및 타임스탬프 설정
    import datetime
    timestamp = datetime.datetime.now().strftime("%y%m%d_%H%M")
    downloads_path = os.path.expanduser("~/Downloads")
    
    voice_name_kr = "태양" if voice_type == "taeyang" else "클로이"
    output_audio_name = os.path.join(downloads_path, f"01-25슈퍼톤_{voice_name_kr}_{timestamp}.wav")
    output_srt_name = os.path.join(downloads_path, f"01-25슈퍼톤_{voice_name_kr}_{timestamp}.srt")

    with open(input_script_path, "r", encoding="utf-8") as f:
        full_text = f.read().strip()

    segments = []
    # 텍스트 세그먼트 분리 (따옴표 포함 여부와 상관없이 태양으로 처리)
    pattern = r'("[^"]+"|[^{}"]+)'
    raw_matches = re.findall(pattern, full_text)
    
    for match in raw_matches:
        text = match.strip()
        if not text: continue
        
        # 선택된 목소리 배정
        voice = voice_type
        clean_text = text.replace('"', '')
        
        # 1.4배속 적용
        voice_speed = 1.4
        
        # 300자 제한 대응을 위해 텍스트 쪼개기
        chunks = split_text_into_chunks(clean_text)
        for chunk in chunks:
            segments.append({
                "text": chunk, 
                "voice": voice,
                "speed": voice_speed,
                "display_text": chunk 
            })

    final_audio = AudioSegment.empty()
    current_time_ms = 0
    srt_content = []

    print(f"🎯 총 {len(segments)}개의 청크 생성 시작 (발음 교정 및 다운로드 폴더 저장)")

    PAUSE_MS = 500  # 마침표 뒤 휴지기 (500ms)

    for i, seg in enumerate(segments):
        temp_wav = f"temp_seg_{i}.wav"
        
        # [수정] 아주 화난 톤으로 설정 (Angry 스타일 + 피치 변동폭 증가)
        success = supertone_tts(
            seg["text"], 
            voice_type=seg["voice"], 
            speed=seg["speed"], 
            style="Angry",           # 화난 스타일 적용
            pitch_variance=1.5,      # 감정 기복 강화
            pitch_shift=1,           # 약간 날카로운 톤
            output_path=temp_wav
        )
        
        if success:
            audio_seg = AudioSegment.from_wav(temp_wav)
            duration_ms = len(audio_seg)
            
            # 텍스트가 문장 부호로 끝나는 경우 휴지기 추가
            use_pause = seg["text"].strip().endswith(('.', '?', '!'))
            current_seg_duration = duration_ms + (PAUSE_MS if use_pause else 0)
            
            start_time = format_srt_time(current_time_ms)
            end_time = format_srt_time(current_time_ms + current_seg_duration)
            srt_content.append(f"{i+1}\n{start_time} --> {end_time}\n{seg['display_text']}\n")
            
            final_audio += audio_seg
            if use_pause:
                final_audio += AudioSegment.silent(duration=PAUSE_MS)
            
            current_time_ms += current_seg_duration
            
            if os.path.exists(temp_wav):
                os.remove(temp_wav)
            print(f"✅ [{i+1}/{len(segments)}] 생성 완료 ({seg['voice']}, {seg['speed']}x) - {duration_ms/1000:.2f}초 (+{PAUSE_MS/1000 if use_pause else 0}s 휴지기)")
        else:
            print(f"❌ [{i+1}/{len(segments)}] 생성 실패. (텍스트: {seg['text'][:20]}...)")
            return

    # 결과물 저장
    final_audio.export(output_audio_name, format="wav")
    with open(output_srt_name, "w", encoding="utf-8") as f:
        f.writelines("\n".join(srt_content))

    print(f"\n✨ 모든 작업 완료!")
    print(f"🎬 최종 오디오 (다운로드): {output_audio_name}")
    print(f"📜 최종 자막 (다운로드): {output_srt_name}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Supertone TTS Master")
    parser.add_argument("--script", type=str, default="/Users/a12/projects/tts/대본.txt", help="Path to script file")
    parser.add_argument("--voice", type=str, default="taeyang", choices=["taeyang", "chloe"], help="Voice to use")
    
    args = parser.parse_args()
    process_promotion_video(args.script, voice_type=args.voice)

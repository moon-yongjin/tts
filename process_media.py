import os
import subprocess
import whisper
import json
from datetime import datetime

# [설정]
SOURCE_DIR = "/Users/a12/Desktop/작업할것들/youtube_shorts_이해불가/Shorts_Backup/DoranDoran"
OUTPUT_DIR = "/Users/a12/projects/tts/DoranDoran_Scripts"
MODEL_NAME = "turbo" # "base" is faster, "turbo" is higher quality on Mac

os.makedirs(OUTPUT_DIR, exist_ok=True)

def convert_to_mp3(webm_path, mp3_path):
    print(f"🎬 변환 중: {os.path.basename(webm_path)} -> MP3")
    cmd = [
        "ffmpeg", "-i", webm_path,
        "-vn", "-acodec", "libmp3lame", "-y",
        mp3_path
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def transcribe_audio(mp3_path, txt_path):
    print(f"✍️ 대본 추출 중 (STT): {os.path.basename(mp3_path)}")
    model = whisper.load_model(MODEL_NAME)
    result = model.transcribe(mp3_path, language="ko")
    
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(result["text"])
    print(f"✅ 완료: {os.path.basename(txt_path)}")

def process_file(filename):
    if not filename.endswith(".webm"):
        return

    webm_path = os.path.join(SOURCE_DIR, filename)
    base_name = os.path.splitext(filename)[0]
    mp3_path = os.path.join(OUTPUT_DIR, f"{base_name}.mp3")
    txt_path = os.path.join(OUTPUT_DIR, f"{base_name}.txt")

    if not os.path.exists(txt_path):
        try:
            convert_to_mp3(webm_path, mp3_path)
            transcribe_audio(mp3_path, txt_path)
        except Exception as e:
            print(f"❌ 에러 발생 ({filename}): {e}")
    else:
        print(f"⏩ 이미 처리됨: {filename}")

if __name__ == "__main__":
    files = sorted([f for f in os.listdir(SOURCE_DIR) if f.endswith(".webm")])
    print(f"🚀 총 {len(files)}개의 파일을 순차적으로 처리합니다.")
    
    for f in files:
        process_file(f)

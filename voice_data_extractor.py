import os
import yt_dlp
import json
from google import genai
from google.oauth2 import service_account
from google.genai import types

# --- [설정] ---
VIDEO_URL = "https://www.youtube.com/watch?v=B5ffORvjqWU"
OUTPUT_DIR = os.path.expanduser("~/Downloads/Voice_Assets")
CREDENTIALS_PATH = "/Users/a12/projects/tts/core_v2/service_account.json"
PROJECT_ID = "ttss-483505"
LOCATION = "us-central1"

if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

def download_audio(url, output_dir):
    print(f"🎬 유튜브 오디오 다운로드 시작: {url}")
    # 파일명은 제목으로 추출
    ydl_opts = {
        'format': 'm4a/bestaudio/best',
        'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
        'quiet': False,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'm4a',
        }]
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            audio_path = ydl.prepare_filename(info)
            # FFmpeg postprocessor might change extension to m4a if it wasn't already
            if not audio_path.endswith('.m4a'):
                audio_path = os.path.splitext(audio_path)[0] + '.m4a'
            return audio_path
    except Exception as e:
        print(f"❌ 다운로드 실패: {e}")
        return None

def transcribe_with_gemini(audio_path):
    print(f"🤖 Gemini를 통한 고정밀 전사 시작: {os.path.basename(audio_path)}")
    try:
        credentials = service_account.Credentials.from_service_account_file(
            CREDENTIALS_PATH,
            scopes=['https://www.googleapis.com/auth/cloud-platform']
        )
        client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION, credentials=credentials)
        
        with open(audio_path, "rb") as f:
            audio_bytes = f.read()

        prompt = """
        이 오디오는 고품질 라디오 드라마 음원입니다. 
        목소리 학습(LoRA) 데이터셋으로 사용하기 위해, 오디오의 모든 대사를 한국어로 정확하게 받아적어주세요.
        배경음악이나 효과음에 대한 설명은 제외하고, 등장인물들의 대사만 텍스트로 쭉 나열해주세요.
        """
        
        response = client.models.generate_content(
            model="publishers/google/models/gemini-2.0-flash-001",
            contents=[prompt, types.Part.from_bytes(data=audio_bytes, mime_type="audio/mp4")]
        )
        return response.text.strip()
    except Exception as e:
        print(f"❌ 전사 실패: {e}")
        return None

def main():
    audio_path = download_audio(VIDEO_URL, OUTPUT_DIR)
    if audio_path and os.path.exists(audio_path):
        print(f"✅ 오디오 파일 저장 완료: {audio_path}")
        
        # 전체를 한꺼번에 전사하면 토큰 제한에 걸릴 수 있으므로 
        # 실제로는 파일을 잘라서 보내야 할 수도 있으나, 먼저 시도해봅니다.
        transcript = transcribe_with_gemini(audio_path)
        if transcript:
            txt_path = audio_path.replace(".m4a", ".txt")
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(transcript)
            print(f"✅ 전사 텍스트 저장 완료: {txt_path}")
            print("\n--- [추출된 대본 일부] ---")
            print(transcript[:500] + "...")
    else:
        print("❌ 작업 중단.")

if __name__ == "__main__":
    main()

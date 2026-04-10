import os
import yt_dlp
from google import genai
from google.oauth2 import service_account
from google.genai import types

# --- [설정] ---
CHANNEL_URL = "https://www.youtube.com/@야담과개그/shorts"
OUTPUT_FILE = "야담과개그_대본모음_Gemini.txt"
MAX_VIDEOS = 10  # 테스트를 위해 먼저 10개만 추출
AUDIO_DIR = "temp_audio"
CREDENTIALS_PATH = "/Users/a12/projects/tts/core_v2/service_account.json"

if not os.path.exists(AUDIO_DIR):
    os.makedirs(AUDIO_DIR)

# --- [Gemini 클라이언트 설정] ---
try:
    credentials = service_account.Credentials.from_service_account_file(
        CREDENTIALS_PATH,
        scopes=['https://www.googleapis.com/auth/cloud-platform']
    )
    client = genai.Client(
        vertexai=True, 
        project="ttss-483505", 
        location="us-central1", 
        credentials=credentials
    )
    print("✅ Gemini 클라이언트 초기화 성공")
except Exception as e:
    print(f"❌ Gemini Error: {e}")
    exit()

def get_video_urls(channel_url, max_videos):
    print(f"채널에서 쇼츠 URL을 추출합니다: {channel_url}")
    ydl_opts = {
        'extract_flat': True,
        'playlistend': max_videos,
        'quiet': True,
    }
    video_ids = []
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(channel_url, download=False)
            if 'entries' in info:
                for entry in info['entries']:
                    if entry and 'id' in entry:
                        video_ids.append((entry['id'], entry.get('title', '제목 없음')))
        except Exception as e:
            print(f"URL 추출 중 오류 발생: {e}")
    return video_ids

def download_audio(video_id):
    audio_path = os.path.join(AUDIO_DIR, f"{video_id}.m4a")
    if os.path.exists(audio_path):
        return audio_path
        
    url = f"https://www.youtube.com/shorts/{video_id}"
    ydl_opts = {
        'format': 'm4a/bestaudio/best',
        'outtmpl': audio_path,
        'quiet': True,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'm4a',
        }]
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        return audio_path
    except Exception as e:
        print(f"  ❌ 오디오 다운로드 실패: {e}")
        return None

def transcribe_audio_with_gemini(audio_path):
    print(f"  진행 중: Gemini로 오디오 분석 중... ({audio_path})")
    try:
        # 1. 오디오 파일 업로드
        with open(audio_path, "rb") as f:
            audio_bytes = f.read()

        # 2. 프롬프트 생성 (대본만 추출하도록)
        prompt = """
        이 오디오는 한국어로 된 짧은 이야기/개그 유튜브 쇼츠입니다. 
        오디오에 나오는 모든 대사를 그대로 받아적어 대본(Transcript)을 만들어주세요. 
        대사 외에 다른 부가 설명이나 인사말, 마크다운 포맷 등은 일체 넣지 마시고 **오직 오디오에서 들리는 한국어 대사만** 공백으로 이어붙여서 쭉 적어주세요.
        """
        
        # 3. Gemini 호출
        response = client.models.generate_content(
            model="publishers/google/models/gemini-2.0-flash-001",
            contents=[prompt, types.Part.from_bytes(data=audio_bytes, mime_type="audio/mp4")]
        )
        return response.text.strip()
    except Exception as e:
        print(f"  ❌ Gemini 변환 실패: {e}")
        return f"[Gemini 변환 실패]"

def main():
    print("--- 유튜브 쇼츠 오디오 추출 & Gemini 전사 시작 ---")
    videos = get_video_urls(CHANNEL_URL, MAX_VIDEOS)
    print(f"총 {len(videos)}개의 쇼츠 영상을 처리합니다 (최대 {MAX_VIDEOS}개 제한).")
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        for i, (vid, title) in enumerate(videos):
            print(f"\n({i+1}/{len(videos)}) 처리 중...: {title} (ID: {vid})")
            
            # 1. 오디오 다운로드
            audio_path = download_audio(vid)
            if not audio_path:
                continue
                
            # 2. Gemini 대본 변환
            transcript = transcribe_audio_with_gemini(audio_path)
            print(f"  ✅ 대본 추출 완료 (길이: {len(transcript)}자)")
            
            # 3. 결과 저장
            f.write(f"[{i+1}] {title}\n")
            f.write(f"URL: https://www.youtube.com/shorts/{vid}\n")
            f.write(f"대본: {transcript}\n")
            f.write("-" * 50 + "\n\n")
            
            # (선택) 임시 파일 삭제하여 공간 절약
            # if os.path.exists(audio_path):
            #     os.remove(audio_path)
            
    print(f"\n🎉 모든 처리가 완료되었습니다! 결과 저장: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()

import os
import re
from youtube_transcript_api import YouTubeTranscriptApi
import yt_dlp

# 설정
CHANNEL_URL = "https://www.youtube.com/@야담과개그/shorts"
OUTPUT_FILE = "야담과개그_대본모음.txt"
MAX_VIDEOS = 50 # 가져올 최대 영상 수

def get_video_urls(channel_url, max_videos=50):
    print(f"채널에서 쇼츠 URL을 추출합니다: {channel_url}")
    # yt-dlp 옵션: 재생목록(채널)에서 URL만 추출, 최대 개수 제한
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

def extract_transcript(video_id):
    try:
        # 한국어 자막 우선 추출
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['ko'])
        
        # 텍스트만 추출하여 공백으로 연결
        text = " ".join([item['text'] for item in transcript])
        
        # 줄바꿈 등 정리
        text = text.replace('\n', ' ')
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    except Exception as e:
        return f"[자막 추출 실패: {e}]"

def main():
    print("--- 유튜브 채널 자막 추출 시작 ---")
    
    # 1. 채널에서 비디오 아이디 및 제목 가져오기
    videos = get_video_urls(CHANNEL_URL, MAX_VIDEOS)
    print(f"총 {len(videos)}개의 쇼츠 영상을 찾았습니다.")
    
    if not videos:
        print("영상을 찾을 수 없습니다. 채널 URL을 확인해주세요.")
        return

    # 2. 대본 추출 및 파일 저장
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        for i, (vid, title) in enumerate(videos):
            print(f"({i+1}/{len(videos)}) 대본 추출 중: {title} (ID: {vid})")
            transcript_text = extract_transcript(vid)
            
            f.write(f"[{i+1}] {title}\n")
            f.write(f"URL: https://www.youtube.com/shorts/{vid}\n")
            f.write(f"대본: {transcript_text}\n")
            f.write("-" * 50 + "\n\n")
            
    print(f"--- 대본 저장 완료: {OUTPUT_FILE} ---")

if __name__ == "__main__":
    main()

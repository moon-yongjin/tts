import os
import csv
import re
import subprocess
import json

# [설정]
CHANNEL_URL = "https://www.youtube.com/@hexagon-ms/videos"
OUTPUT_DIR = "scrap/hexagon_ms"
MAX_VIDEOS = 50

def clean_filename(title):
    return re.sub(r'[\\/*?:"<>|]', "", title)

def extract_transcript_with_ytdlp(video_url, output_path):
    # yt-dlp를 사용하여 자막을 추출합니다. (vtt 형식으로 다운로드 후 텍스트만 추출)
    temp_prefix = os.path.join(OUTPUT_DIR, "temp_sub")
    
    cmd = [
        "yt-dlp",
        "--skip-download",
        "--write-auto-subs",
        "--sub-lang", "ko",
        "--sub-format", "vtt",
        "-o", temp_prefix,
        video_url
    ]
    
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        # 생성된 .vtt 파일을 찾습니다.
        vtt_files = [f for f in os.listdir(OUTPUT_DIR) if f.startswith("temp_sub") and f.endswith(".vtt")]
        if not vtt_files:
            return None
            
        vtt_path = os.path.join(OUTPUT_DIR, vtt_files[0])
        
        # VTT 파일에서 텍스트만 추출
        with open(vtt_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            
        text_lines = []
        for line in lines:
            line = line.strip()
            if "-->" in line or line.startswith("WEBVTT") or not line or line.isdigit():
                continue
            line = re.sub(r'<[^>]+>', '', line)
            if line not in text_lines:
                text_lines.append(line)
        
        full_text = " ".join(text_lines)
        os.remove(vtt_path)
        return full_text
        
    except Exception as e:
        print(f"⚠️ yt-dlp 오류 ({video_url}): {e}")
        return None

def get_video_list():
    print(f"🔍 채널 정보 가져오는 중: {CHANNEL_URL}")
    # --print 템플릿 형식을 명확하게 지정합니다.
    cmd = [
        "yt-dlp",
        "--flat-playlist",
        "--playlist-end", str(MAX_VIDEOS),
        "--print", "%(title)s|%(id)s|%(webpage_url)s",
        CHANNEL_URL
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ 목록 가져오기 실패: {result.stderr}")
        return []
        
    videos = []
    for line in result.stdout.splitlines():
        if "|" in line:
            parts = line.split("|")
            # yt-dlp가 가끔 헤더나 불필요한 라인을 출력할 수 있으므로 필터링
            if len(parts) == 3 and parts[1] != "id":
                title, vid, url = parts
                videos.append({'title': title, 'id': vid, 'url': url})
    return videos

def main():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    videos = get_video_list()
    if not videos:
        print("❌ 영상을 찾을 수 없습니다.")
        return

    summary_data = []
    
    for i, video in enumerate(videos):
        title = video['title']
        url = video['url']
        print(f"[{i+1}/{len(videos)}] 처리 중: {title}")

        # 자막 추출
        full_text = extract_transcript_with_ytdlp(url, OUTPUT_DIR)
        
        if full_text:
            safe_title = clean_filename(title)
            filename = f"{safe_title}.txt"
            filepath = os.path.join(OUTPUT_DIR, filename)
            
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(f"제목: {title}\n")
                f.write(f"URL: {url}\n")
                f.write("-" * 50 + "\n\n")
                f.write(full_text)

            summary_data.append([title, url, filepath])
            print(f"✅ 저장 완료: {filename}")
        else:
            print(f"⚠️ 자막 추출 실패")

    # 요약 CSV 생성
    csv_path = os.path.join(OUTPUT_DIR, "00_metadata_summary.csv")
    with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["제목", "URL", "파일경로"])
        writer.writerows(summary_data)
    
    print(f"\n✨ 모든 작업 완료! 결과물 위치: {OUTPUT_DIR}")

if __name__ == "__main__":
    main()

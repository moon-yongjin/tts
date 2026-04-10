import os
import subprocess
from pathlib import Path

video_dir = "/Users/a12/Desktop/생성이미지_02021136_203"
output_dir = "/Users/a12/Downloads/Whisk_Scripts"
os.makedirs(output_dir, exist_ok=True)

# Mp4 파일 목록 가져오기
videos = [f for f in os.listdir(video_dir) if f.endswith('.mp4')]
videos.sort()

print(f"Total {len(videos)} videos found. Starting extraction...")

for i, video in enumerate(videos, 1):
    video_path = os.path.join(video_dir, video)
    # 파일명에서 특수문자 제거 또는 안전한 이름 생성 (출력용)
    safe_name = "".join([c for c in video if c.isalnum() or c in (' ', '_', '.')]).rstrip()
    if not safe_name: safe_name = f"script_{i}"
    
    print(f"[{i}/{len(videos)}] Processing: {video}")
    
    # Whisper 명령 실행
    # output_format을 txt로 지정하면 파일명.txt로 저장됨
    try:
        subprocess.run([
            "whisper", 
            video_path, 
            "--model", "small", 
            "--language", "Korean", 
            "--output_dir", output_dir,
            "--output_format", "txt"
        ], check=True)
        print(f"Successfully processed: {video}")
    except subprocess.CalledProcessError as e:
        print(f"Error processing {video}: {e}")

print("All tasks completed.")

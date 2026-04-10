import os
import json
import re
import subprocess
from pathlib import Path

def run_command(cmd, description):
    print(f"🚀 {description} 중...")
    try:
        subprocess.run(cmd, check=True, capture_output=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} 실패: {e.stderr.decode()}")
        return False

def get_video_metadata(url):
    """유튜브 영상 제목 및 타임스탬프 정보 추출"""
    print(f"🔍 영상 메타데이터 분석 중: {url}")
    cmd = ["yt-dlp", "-j", url]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0: 
        print(f"❌ 메타데이터 추출 실패: {result.stderr}")
        return None, None
    
    data = json.loads(result.stdout)
    title = data.get("title", "Unknown_Video")
    description = data.get("description", "")
    
    # 설명란 타임스탬프 추출 시도
    ts_list = []
    lines = description.split('\n')
    for line in lines:
        match = re.search(r'(\d{1,2}:\d{2}(?::\d{2})?)[\s-]+(.*)', line)
        if match:
            ts_list.append((match.group(1), match.group(2).strip()))
    
    return title, ts_list

def download_video(url, output_path):
    """유튜브 영상 다운로드"""
    if output_path.exists():
        print(f"ℹ️ 이미 원본 파일이 존재합니다: {output_path.name}")
        return True
        
    cmd = [
        "yt-dlp",
        "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "-o", str(output_path),
        url
    ]
    return run_command(cmd, "영상 다운로드")

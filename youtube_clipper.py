import os
import sys
import subprocess
import re
import json
from pathlib import Path

# [설정]
PYTHON_EXE = sys.executable
EXTRACTOR_SCRIPT = "extract_assets.py"

def run_command(cmd):
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"❌ 에러 발생: {e.stderr}")
        return None

def get_video_info(url):
    print("🔍 영상 정보를 가져오는 중...")
    # 설명과 타임스탬프 추출
    desc = run_command(["yt-dlp", "--get-description", "--skip-download", url])
    title = run_command(["yt-dlp", "--get-title", "--skip-download", url])
    
    if not desc or not title:
        return None, None
    
    # 타임스탬프(00:00 형) 추출
    timestamps = re.findall(r'(\d{1,2}:\d{2}(?::\d{2})?)\s+(.+)', desc)
    return title.strip(), timestamps

def download_section(url, start_time, end_time, title):
    safe_title = re.sub(r'[^\w\s-]', '', title).strip().replace(' ', '_')
    output_filename = f"clip_{start_time.replace(':', '')}_{end_time.replace(':', '')}_{safe_title}.mp4"
    output_path = Path.home() / "Downloads" / output_filename
    
    print(f"🚀 [{start_time} ~ {end_time}] 구간 다운로드 시작...")
    
    # yt-dlp의 --download-sections 기능 사용
    # 형식: *30:00-35:00
    section_arg = f"*{start_time}-{end_time}"
    cmd = [
        "yt-dlp",
        "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "--download-sections", section_arg,
        "--force-keyframes-at-cuts",
        "-o", str(output_path),
        url
    ]
    
    subprocess.run(cmd)
    return output_path

def main():
    print("==========================================")
    print("🎬 유튜브 스마트 클리퍼 (부분 추출기)")
    print("==========================================")
    
    url = input("🔗 유튜브 URL을 입력하세요: ").strip()
    if not url: return

    title, timestamps = get_video_info(url)
    
    if not title:
        print("❌ 영상 정보를 가져올 수 없습니다.")
        return

    print(f"\n📺 영상 제목: {title}")
    
    if timestamps:
        print("\n📍 발견된 타임스탬프 (목차):")
        for i, (ts, name) in enumerate(timestamps, 1):
            print(f"{i}) {ts} - {name}")
        
        choice = input("\n👉 다운로드할 번호를 입력하거나 직접 시간 범위를 입력하세요 (예: 1 또는 05:00-10:00): ").strip()
        
        if choice.isdigit() and 1 <= int(choice) <= len(timestamps):
            idx = int(choice) - 1
            start_time = timestamps[idx][0]
            # 다음 타임스탬프가 있으면 거기까지, 없으면 끝까지(12:00:00 같이 넉넉히)
            end_time = timestamps[idx+1][0] if idx + 1 < len(timestamps) else "23:59:59"
        elif '-' in choice:
            start_time, end_time = choice.split('-')
        else:
            print("❌ 잘못된 입력입니다.")
            return
    else:
        print("\nℹ️ 타임스탬프를 찾을 수 없습니다.")
        range_input = input("👉 추출할 시간 범위를 직접 입력하세요 (예: 05:00-10:00): ").strip()
        if '-' in range_input:
            start_time, end_time = range_input.split('-')
        else:
            return

    # 클립 다운로드
    clip_path = download_section(url, start_time, end_time, title)
    
    if clip_path and clip_path.exists():
        print(f"\n✅ 클립 제작 완료: {clip_path.name}")
        
        # 자동 추출기(extract_assets.py) 실행 여부 확인
        do_extract = input("🎙️ 이 클립에서 음성/자막을 바로 추출할까요? (Y/n): ").strip().lower()
        if do_extract != 'n':
            print("🚀 자동 추출기 가동 중...")
            subprocess.run([PYTHON_EXE, EXTRACTOR_SCRIPT, str(clip_path)])
    else:
        print("❌ 다운로드에 실패했습니다.")

if __name__ == "__main__":
    main()

import os
import sys
import json
import re
import subprocess
from pathlib import Path

# 모듈 경로 추가 및 임포트
sys.path.append(str(Path(__file__).parent / "utils" / "youtube" / "lib"))
import video_downloader as vd

def analyze_silence(video_path):
    print("🎧 오디오 무음 구간(숨소리, 쉬는 타임) 분석 중...")
    # silencedetect: -30dB 이하 구간이 0.5초 이상 지속되면 무음으로 간주
    cmd = [
        "ffmpeg", "-i", str(video_path), 
        "-af", "silencedetect=noise=-30dB:d=0.5", 
        "-f", "null", "-"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    silence_starts = []
    silence_ends = []
    
    for line in result.stderr.splitlines():
        if "silence_start" in line:
            match = re.search(r"silence_start: ([\d\.]+)", line)
            if match:
                silence_starts.append(float(match.group(1)))
        elif "silence_end" in line:
            match = re.search(r"silence_end: ([\d\.]+)", line)
            if match:
                silence_ends.append(float(match.group(1)))
                
    return silence_starts, silence_ends

def get_video_duration(video_path):
    cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(video_path)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    try:
        return float(result.stdout.strip())
    except:
        return 0.0

def chop_video(video_path, output_dir):
    starts, ends = analyze_silence(video_path)
    total_dur = get_video_duration(video_path)
    
    # 발화(Speaking) 구간 계산
    # 영상 시작 부터 첫 무음 시작점까지 -> 첫 발화
    # 무음 끝점부터 다음 무음 시작점까지 -> 두번째 발화 ...
    
    speaking_segments = []
    current_time = 0.0
    
    # starts와 ends 짝맞추기
    for i in range(min(len(starts), len(ends))):
        s_start = starts[i]
        s_end = ends[i]
        
        if s_start > current_time:
            # 패딩을 살짝 주어 안 잘리게 함 (0.1초)
            sp_start = max(0.0, current_time - 0.1)
            sp_end = s_start + 0.1
            if sp_end - sp_start > 0.5: # 너무 짧은 구간 무시
                speaking_segments.append((sp_start, sp_end))
        current_time = s_end
        
    # 마지막 무음 끝점부터 영상 끝까지
    if current_time < total_dur:
        sp_start = max(0.0, current_time - 0.1)
        sp_end = total_dur
        if sp_end - sp_start > 0.5:
            speaking_segments.append((sp_start, sp_end))
            
    if not speaking_segments:
        print("⚠️ 발화 구간을 찾지 못했습니다. 무음 필터 기준을 조정해야 할 수 있습니다.")
        return
        
    print(f"✂️ 총 {len(speaking_segments)}개의 발화(목소리) 조각을 찾아냈습니다!")
    print(f"🎬 고속 컷팅 작업 시작...")
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    for i, (st, ed) in enumerate(speaking_segments):
        out_file = output_dir / f"clip_{i+1:03d}_{int(st)}s_to_{int(ed)}s.mp4"
        # -c:v libx264 -preset ultrafast 를 사용하여 모든 편집기에서 보이게 함
        cmd = [
            "ffmpeg", "-y", "-ss", str(st), "-to", str(ed),
            "-i", str(video_path),
            "-c:v", "libx264", "-preset", "ultrafast",
            "-c:a", "aac", "-b:a", "128k",
            str(out_file)
        ]
        subprocess.run(cmd, capture_output=True)
        sys.stdout.write(f"\r진행률: {i+1}/{len(speaking_segments)} 조각 완료...")
        sys.stdout.flush()

    print(f"\n✅ {len(speaking_segments)}개의 조각 컷팅이 완료되었습니다!")
    print(f"📂 결과물 폴더: {output_dir}")
    os.system(f"open '{output_dir}'")

def main():
    print("==========================================")
    print("🚀 [V13] Direct Video Slicer (통영상 자동 무음 컷팅기)")
    print("==========================================")
    
    inp = ""
    if len(sys.argv) > 1:
        inp = sys.argv[1]
    else:
        inp = input("🔗 유튜브 URL 또는 로컬 MP4 파일 경로를 드래그 앤 드롭 하세요: ").strip()
        
    if not inp: return
    
    downloads_dir = Path.home() / "Downloads"
    
    is_local = os.path.exists(inp) and inp.lower().endswith(".mp4")
    
    if is_local:
        full_video_path = Path(inp)
        title = full_video_path.stem
    else:
        url = inp
        title, ts_list = vd.get_video_metadata(url)
        if not title: return
        safe_title = re.sub(r'[^\w\s-]', '', title).strip().replace(' ', '_')
        full_video_path = downloads_dir / f"{safe_title}_slicer_source.mp4"
        if not vd.download_video(url, full_video_path): return
        title = safe_title
        
    output_dir = downloads_dir / f"Chopped_{title}"
    chop_video(full_video_path, output_dir)

if __name__ == "__main__":
    main()

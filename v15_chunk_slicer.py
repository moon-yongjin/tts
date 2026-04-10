import os
import sys
import re
import subprocess
from pathlib import Path

def analyze_speech_starts(video_path):
    print("🎧 발화 시작 지점 분석 중...")
    # silencedetect: 소리가 일정 수준 이상으로 커지는 시점(무음이 끝나는 지점)을 찾음
    # noise=-30dB, duration=0.5s 무음 기준
    cmd = [
        "ffmpeg", "-i", str(video_path), 
        "-af", "silencedetect=noise=-30dB:d=0.5", 
        "-f", "null", "-"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    speech_starts = [0.0] # 영상 시작점 포함
    
    for line in result.stderr.splitlines():
        if "silence_end" in line:
            match = re.search(r"silence_end: ([\d\.]+)", line)
            if match:
                # 무음이 끝나는 지점 = 말이 시작되는 지점
                speech_starts.append(float(match.group(1)))
                
    return sorted(list(set(speech_starts)))

def get_video_duration(video_path):
    cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(video_path)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    try:
        return float(result.stdout.strip())
    except:
        return 0.0

def slice_by_chunks(video_path, output_dir):
    starts = analyze_speech_starts(video_path)
    total_dur = get_video_duration(video_path)
    
    if not starts:
        print("⚠️ 발화 지점을 찾지 못했습니다.")
        return
        
    # [현재 시작점] ~ [다음 시작점]으로 구간 생성
    chunks = []
    for i in range(len(starts)):
        st = starts[i]
        ed = starts[i+1] if i + 1 < len(starts) else total_dur
        
        # 너무 짧은 클립은 무시 (최소 0.5초)
        if ed - st > 0.5:
            chunks.append((st, ed))
            
    print(f"✂️ 총 {len(chunks)}개의 청크(문장+무음)를 생성합니다.")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    for i, (st, ed) in enumerate(chunks):
        out_file = output_dir / f"chunk_{i+1:03d}_{int(st)}s.mp4"
        # 캡컷 호환성을 위한 libx264 인코딩
        cmd = [
            "ffmpeg", "-y", "-ss", str(st), "-to", str(ed),
            "-i", str(video_path),
            "-c:v", "libx264", "-preset", "ultrafast",
            "-c:a", "aac", "-b:a", "128k",
            str(out_file)
        ]
        subprocess.run(cmd, capture_output=True)
        sys.stdout.write(f"\r진행률: {i+1}/{len(chunks)} 조각 완료...")
        sys.stdout.flush()

    print(f"\n✅ 작업 완료! 폴더: {output_dir}")
    os.system(f"open '{output_dir}'")

def main():
    print("==========================================")
    print("🚀 [V15] Simple Chunk Slicer (말 시작 기준 분할기)")
    print("==========================================")
    
    if len(sys.argv) > 1:
        inp = sys.argv[1]
    else:
        inp = input("🔗 영상 파일 경로를 입력하세요: ").strip()
        
    video_path = Path(inp)
    if not video_path.exists():
        print(f"❌ 파일을 찾을 수 없습니다: {video_path}")
        return
        
    output_dir = video_path.parent / f"Chunks_{video_path.stem}"
    slice_by_chunks(video_path, output_dir)

if __name__ == "__main__":
    main()

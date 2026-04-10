import os
import subprocess
import sys
import re

def get_silence_segments(input_file, threshold=-45, duration=0.5):
    """FFmpeg silencedetect 필터를 사용하여 무음 구간을 찾습니다."""
    print(f"🔍 무음 구간 탐색 중 (기준: {threshold}dB, {duration}s)...")
    
    cmd = [
        "ffmpeg", "-i", input_file,
        "-af", f"silencedetect=n={threshold}dB:d={duration}",
        "-f", "null", "-"
    ]
    
    # FFmpeg outputs duration/silence info to stderr
    process = subprocess.Popen(cmd, stderr=subprocess.PIPE, text=True)
    _, stderr = process.communicate()
    
    starts = [float(x) for x in re.findall(r"silence_start: ([\d\.]+)", stderr)]
    ends = [float(x) for x in re.findall(r"silence_end: ([\d\.]+)", stderr)]
    
    if len(starts) != len(ends):
        # If the file ends during a silent period, ffmpeg might not report silence_end
        # We can append the file duration or just trim the ends list
        ends = ends[:len(starts)]
        
    return list(zip(starts, ends))

def get_video_duration(input_file):
    cmd = [
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", input_file
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return float(result.stdout.strip())

def auto_cut(input_file, padding=0.5):
    """무음 구간을 제외하고 0.5초 여유를 둔 채 자르고 합칩니다."""
    if not os.path.exists(input_file):
        print(f"❌ 파일을 찾을 수 없습니다: {input_file}")
        return

    duration = get_video_duration(input_file)
    silences = get_silence_segments(input_file)
    
    if not silences:
        print("✅ 무음 구간이 발견되지 않았습니다. 원본 그대로 보존합니다.")
        return

    # 소리가 있는(Keep) 구간 계산
    keep_segments = []
    last_end = 0.0
    
    for s_start, s_end in silences:
        # 소리가 있는 구간: 지난 무음 종료 ~ 이번 무음 시작
        # 사용자 요청에 따라 0.5초 여유를 둡니다 (padding)
        k_start = max(0, last_end - padding)
        k_end = min(duration, s_start + padding)
        
        if k_end > k_start:
            keep_segments.append((k_start, k_end))
        last_end = s_end

    # 마지막 구간 처리
    if last_end < duration:
        keep_segments.append((max(0, last_end - padding), duration))

    # 중첩 구간 병합 (padding으로 인해 겹칠 수 있음)
    merged_segments = []
    if keep_segments:
        curr_start, curr_end = keep_segments[0]
        for next_start, next_end in keep_segments[1:]:
            if next_start < curr_end:
                curr_end = max(curr_end, next_end)
            else:
                merged_segments.append((curr_start, curr_end))
                curr_start, curr_end = next_start, next_end
        merged_segments.append((curr_start, curr_end))

    if not merged_segments:
        print("⚠️ 남길 수 있는 유효 구간이 없습니다.")
        return

    # FFmpeg 필터 생성
    # select/aselect 필터를 사용하여 여러 구간을 한 번에 추출합니다.
    v_filter = ""
    a_filter = ""
    for i, (start, end) in enumerate(merged_segments):
        v_filter += f"between(t,{start},{end})+"
        a_filter += f"between(t,{start},{end})+"
    
    v_filter = v_filter.rstrip('+')
    a_filter = a_filter.rstrip('+')

    output_file = os.path.splitext(input_file)[0] + "_Trimmed" + os.path.splitext(input_file)[1]
    
    print(f"✂️ 총 {len(merged_segments)}개의 구간을 추출하여 합치는 중...")
    
    # 주의: 필터가 너무 길어지면 명령줄 제한에 걸릴 수 있으므로 복잡한 필터 체인을 사용합니다.
    # 하지만 일반적인 강의 수준에서는 select 필터로 충분합니다.
    cmd = [
        "ffmpeg", "-i", input_file,
        "-vf", f"select='{v_filter}',setpts=N/FRAME_RATE/TB",
        "-af", f"aselect='{a_filter}',asetpts=N/SR/TB",
        "-y", output_file
    ]
    
    subprocess.run(cmd)
    print(f"✨ 작업 완료! 저장된 파일: {output_file}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("사용법: python auto_cut_lecture.py [파일경로]")
    else:
        auto_cut(sys.argv[1])

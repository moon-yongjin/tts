import os
import subprocess
import sys
import time

def get_best_ffmpeg():
    try:
        import imageio_ffmpeg
        exe = imageio_ffmpeg.get_ffmpeg_exe()
        if os.path.exists(exe): return exe
    except ImportError: pass
    conda_ffmpeg = os.path.join(os.path.dirname(sys.executable), "ffmpeg")
    if os.path.exists(conda_ffmpeg): return conda_ffmpeg
    return "/opt/homebrew/bin/ffmpeg" if sys.platform == "darwin" else "ffmpeg"

FFMPEG_EXE = get_best_ffmpeg()
DOWNLOADS_DIR = os.path.join(os.path.expanduser("~"), "Downloads")

def get_duration(file_path):
    try:
        cmd = [FFMPEG_EXE, "-i", file_path]
        result = subprocess.run(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
        for line in result.stderr.splitlines():
            if "Duration" in line:
                # Duration: 00:00:08.00 -> 8.0
                time_str = line.split("Duration:")[1].split(",")[0].strip()
                h, m, s = time_str.split(":")
                return float(h) * 3600 + float(m) * 60 + float(s)
    except:
        return 0
    return 0

def run_merge():
    print("🎬 [Intro Merger] 인트로 영상 합치기를 시작합니다...")
    
    # Downloads 폴더의 모든 mp4 파일 찾기 (루트만)
    files = [os.path.join(DOWNLOADS_DIR, f) for f in os.listdir(DOWNLOADS_DIR) if f.lower().endswith(".mp4")]
    if len(files) < 2:
        print("❌ 합칠 파일이 부족합니다. (최소 2개의 MP4 파일 필요)")
        return

    # 길이 순으로 정렬 (가장 짧은 게 인트로, 가장 긴 게 본편)
    file_durations = []
    for f in files:
        d = get_duration(f)
        file_durations.append((f, d))
    
    sorted_files = sorted(file_durations, key=lambda x: x[1])
    
    intro_file = sorted_files[0][0]
    main_file = sorted_files[-1][0]
    
    print(f"👉 인트로 선택: {os.path.basename(intro_file)} ({sorted_files[0][1]}초)")
    print(f"👉 본편 선택: {os.path.basename(main_file)} ({sorted_files[-1][1]}초)")

    output_name = f"최종_인트로포함_영상_{int(time.time())%1000:03d}.mp4"
    output_path = os.path.join(DOWNLOADS_DIR, output_name)

    # FFmpeg Concat (재인코딩 없이 시도, 안 되면 재인코딩)
    # 다른 코덱일 가능성이 높으므로 재인코딩(libx264) 추천
    mylist_path = "mylist_intro.txt"
    with open(mylist_path, "w", encoding="utf-8") as f:
        f.write(f"file '{intro_file}'\n")
        f.write(f"file '{main_file}'\n")

    cmd = [
        FFMPEG_EXE, "-y", "-f", "concat", "-safe", "0", "-i", mylist_path,
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "24", "-c:a", "aac",
        output_path
    ]

    try:
        subprocess.run(cmd, check=True)
        print(f"✨ 완성! 결과물: {output_path}")
        if os.path.exists(mylist_path): os.remove(mylist_path)
    except Exception as e:
        print(f"❌ 합치기 실패: {e}")

if __name__ == "__main__":
    run_merge()


import os
import sys
import subprocess
import unicodedata
from concurrent.futures import ThreadPoolExecutor, as_completed

# [윈도우/맥 호환성]
if sys.platform != "darwin":
    sys.stdout.reconfigure(encoding='utf-8')

# FFmpeg 경로 설정
FFMPEG_PATH = "/opt/homebrew/bin/ffmpeg"
if not os.path.exists(FFMPEG_PATH):
    FFMPEG_PATH = "/usr/local/bin/ffmpeg"

def print_progress_bar(iteration, total, prefix='', suffix='', decimals=1, length=30, fill='█', printEnd="\r"):
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    print(f'\r{prefix} |{bar}| {percent}% {suffix}', end=printEnd)
    if iteration == total: print()

def convert_to_vertical_cinematic(video_path, output_path):
    """
    FFmpeg를 사용하여 가로형 영상을 9:16 세로형으로 변환합니다.
    - 배경: 원본 영상을 1080x1920로 늘리고 박스 블러(boxblur) 처리
    - 전경: 원본 비율을 유지하며 중앙에 얹기
    """
    if not os.path.exists(video_path): return False
    if os.path.exists(output_path): os.remove(output_path)

    # FFmpeg 필터 체인
    # 1. 원본을 1080x1920으로 강제 스케일링 후 블러 적용 -> 배경 [bg]
    # 2. 원본 가로비율 유지하며 가로 1080에 맞추고 적재 -> 전경 [fg]
    # 3. overlay로 중앙 배치
    filter_complex = (
        "[0:v]scale=1080:1920,boxblur=25:25[bg];"
        "[0:v]scale=1080:-2[fg];"
        "[bg][fg]overlay=(W-w)/2:(H-h)/2[outv]"
    )

    cmd = [
        FFMPEG_PATH, "-y",
        "-i", video_path,
        "-filter_complex", filter_complex,
        "-map", "[outv]",
        "-map", "0:a?", # 오디오가 있으면 가져오기
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-crf", "18",
        "-c:a", "copy", # 오디오 인코딩 생략 복사
        output_path
    ]

    try:
        # 로그는 간소화처리
        result = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return result.returncode == 0
    except Exception as e:
        return False

def run_batch_vertical_video():
    base_downloads = os.path.join(os.path.expanduser("~"), "Downloads")
    def normalize_name(n):
        return unicodedata.normalize('NFC', n)

    search_prefixes = ("다이어리_", "무협_", "틱톡_", "시나리오_", "막장_")
    
    subdirs = []
    for d in os.listdir(base_downloads):
        full_path = os.path.join(base_downloads, d)
        if not os.path.isdir(full_path): continue
        norm_d = normalize_name(d)
        if any(norm_d.startswith(p) for p in search_prefixes):
            subdirs.append(full_path)
            
    subdirs = sorted(subdirs, key=os.path.getmtime, reverse=True)
    if not subdirs: 
        print("❌ 작업할 폴더(다이어리/무협/틱톡 등)를 찾을 수 없습니다."); return
    target_dir = subdirs[0] 

    videos = sorted([f for f in os.listdir(target_dir) if f.endswith(".mp4") and not f.endswith("_Vertical.mp4")])
    if not videos: 
        print("❌ 폴더 내 대상 비디오(.mp4) 파일이 없습니다."); return

    print("\n" + "="*50)
    print("🎥 [영상 변환] 프리미엄 세로 시네마틱 (MP4 Video Edition)")
    print("   1080x1920 / 가로 영상 ➡️ 블러 배경 세로형 최적화")
    print("="*50)
    print(f"📂 대상 폴더: {os.path.basename(target_dir)}")
    
    to_process = []
    for i, vid_name in enumerate(videos):
        vid_path = os.path.join(target_dir, vid_name)
        v_name = vid_path.replace(".mp4", "_Vertical.mp4")
        to_process.append((vid_path, v_name, vid_name))

    print(f"🚀 {len(to_process)}개의 영상을 가동합니다...")
    
    completed = 0
    total = len(to_process)
    print_progress_bar(0, total, prefix='진행률:', suffix='준비 중...', length=40)
    
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {executor.submit(convert_to_vertical_cinematic, v, out): n for v, out, n in to_process}
        for future in as_completed(futures):
            name = futures[future]
            completed += 1
            res = future.result()
            status = "완료" if res else "실패"
            print_progress_bar(completed, total, prefix='진행률:', suffix=f"{status} ({name[:12]}...)", length=40)
    
    print("\n✨ 모든 영상이 고품질 세로 시네마틱(_Vertical.mp4)으로 변환되었습니다!")

if __name__ == "__main__":
    run_batch_vertical_video()

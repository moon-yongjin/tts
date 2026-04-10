import os
import numpy as np
import PIL.Image
from moviepy import VideoClip
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import sys
import random
import subprocess

# [윈도우/맥 호환성]
if sys.platform != "darwin":
    sys.stdout.reconfigure(encoding='utf-8')

# [경로 설정]
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if os.path.basename(SCRIPT_DIR) == "core_v2":
    ROOT_DIR = os.path.dirname(SCRIPT_DIR)
    CORE_DIR = SCRIPT_DIR
else:
    ROOT_DIR = SCRIPT_DIR
    CORE_DIR = os.path.join(ROOT_DIR, "core_v2")

# FFmpeg 경로 설정
FFMPEG_PATH = "/opt/homebrew/bin/ffmpeg"
if not os.path.exists(FFMPEG_PATH):
    FFMPEG_PATH = "/usr/local/bin/ffmpeg"

if os.path.exists(FFMPEG_PATH):
    try:
        from moviepy.config import change_settings
        change_settings({"FFMPEG_BINARY": FFMPEG_PATH})
    except ImportError:
        os.environ["IMAGEIO_FFMPEG_EXE"] = FFMPEG_PATH

DOWNLOADS_DIR = os.path.join(os.path.expanduser("~"), "Downloads")

def get_latest_master_audio():
    candidates = [os.path.join(DOWNLOADS_DIR, f) for f in os.listdir(DOWNLOADS_DIR) 
                  if f.lower().endswith(".mp3")]
    if candidates:
        return max(candidates, key=os.path.getmtime)
    return None

def get_audio_duration(audio_path):
    try:
        cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", audio_path]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, text=True)
        return float(result.stdout.strip())
    except:
        return None

def ease_in_out_sine(t):
    return -(np.cos(np.pi * t) - 1) / 2

def print_progress_bar(iteration, total, prefix='', suffix='', decimals=1, length=30, fill='█', printEnd="\r"):
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    print(f'\r{prefix} |{bar}| {percent}% {suffix}', end=printEnd)
    if iteration == total: print()

# --- [뉴스용 깔끔한 무빙 패턴] ---
def generate_news_cinematic(img_path, output_name, index, base_duration=6.0):
    """
    Step 03-12: AI 뉴스용 깔끔한 무빙 에디션
    """
    fps = 30
    w, h = 1280, 720
    if not os.path.exists(img_path): return False

    duration = base_duration
    pattern_idx = index % 6
    
    try:
        with PIL.Image.open(img_path) as p_img:
            img_rgb = p_img.convert("RGB")
        
        def make_frame(t):
            raw_prog = t / duration
            prog = ease_in_out_sine(raw_prog)
            
            s = 1.15 
            move_x, move_y = 0, 0
            
            if pattern_idx == 0: s = 1.05 + (0.2 * prog)
            elif pattern_idx == 1: s = 1.25 - (0.2 * prog)
            elif pattern_idx == 2: move_x = int((-w * 0.1) + (w * 0.2 * prog))
            elif pattern_idx == 3: move_x = int((w * 0.1) - (w * 0.2 * prog))
            elif pattern_idx == 4: move_y = int((-h * 0.05) + (h * 0.1 * prog))
            elif pattern_idx == 5: move_y = int((h * 0.05) - (h * 0.1 * prog))

            nw, nh = int(w * s), int(h * s)
            img_resized = img_rgb.resize((nw, nh), PIL.Image.Resampling.LANCZOS)
            canvas = PIL.Image.new("RGB", (w, h), (0, 0, 0))
            canvas.paste(img_resized, (int(w/2 - nw/2 + move_x), int(h/2 - nh/2 + move_y)))
            
            frame_array = np.array(canvas, dtype=np.uint8)

            fade = 1.0
            if t < 0.5: fade = t / 0.5
            elif t > (duration - 0.5): fade = (duration - t) / 0.5
            
            if fade < 1.0:
                frame_array = (frame_array.astype(np.float32) * fade).astype(np.uint8)

            return frame_array

        clip = VideoClip(make_frame, duration=duration)
        clip.write_videofile(output_name, fps=fps, codec="libx264", bitrate="5000k", threads=4, preset="medium", audio=False, logger=None)
        return True
    except Exception as e:
        print(f"⚠️ 에러 ({os.path.basename(img_path)}): {e}")
        return False

def run_batch_news():
    base_downloads = os.path.join(os.path.expanduser("~"), "Downloads")
    
    # [유연한 폴더 감지]
    # 1순위: 특정 키워드
    subdirs = [os.path.join(base_downloads, d) for d in os.listdir(base_downloads) 
               if os.path.isdir(os.path.join(base_downloads, d)) and ("_생성_" in d or "_로컬생성_" in d or "무협_" in d)]
    
    # 2순위: PNG가 들어있는 가장 최신 폴더
    if not subdirs:
        all_dirs = [os.path.join(base_downloads, d) for d in os.listdir(base_downloads) 
                    if os.path.isdir(os.path.join(base_downloads, d)) and not d.startswith(".")]
        png_dirs = []
        for d in all_dirs:
            try:
                if any(f.lower().endswith(".png") for f in os.listdir(d)):
                    png_dirs.append(d)
            except: pass
        if png_dirs:
            subdirs = [max(png_dirs, key=os.path.getmtime)]

    if not subdirs:
        print("❌ 작업할 이미지 폴더를 찾을 수 없습니다. (.png 파일이 들어있는 폴더를 확인해주세요)")
        return
    
    target_dir = sorted(subdirs)[-1]
    images = sorted([f for f in os.listdir(target_dir) if f.lower().endswith(".png")])
    if not images:
        print("❌ 폴더 내 이미지가 없습니다.")
        return

    print("\n" + "="*50)
    print(f"🎥 [STEP 03-12] AI 뉴스 깔끔 무빙 영상 생성")
    print(f"📂 대상 폴더: {os.path.basename(target_dir)}")
    print("="*50)
    
    to_process = []
    for i, img_name in enumerate(images):
        img_path = os.path.join(target_dir, img_name)
        v_name = img_path.replace(".png", ".mp4").replace(".PNG", ".mp4")
        to_process.append((img_path, v_name, i, img_name))

    print(f"🚀 {len(to_process)}개의 파일을 변환합니다...")

    base_duration = 6.0
    master_audio = get_latest_master_audio()
    if master_audio:
        audio_len = get_audio_duration(master_audio)
        if audio_len:
            base_duration = audio_len / len(to_process)
            print(f"⚖️ [자동 싱크] 오디오({os.path.basename(master_audio)}) 기준 클립당 {base_duration:.2f}초 적용")

    user_input = input(f"👉 기준 지속 시간 입력 [엔터 = {base_duration:.2f}초]: ").strip()
    if user_input:
        try: base_duration = float(user_input)
        except: pass
    
    completed = 0
    total = len(to_process)
    print_progress_bar(0, total, prefix='진행률:', suffix='준비 중...', length=40)
    
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {executor.submit(generate_news_cinematic, p, v, i, base_duration): n for p, v, i, n in to_process}
        for future in as_completed(futures):
            name = futures[future]
            completed += 1
            res = future.result()
            status = "완료" if res else "실패"
            print_progress_bar(completed, total, prefix='진행률:', suffix=f"{status} ({name[:12]}...)", length=40)
    
    print("\n✨ 깔끔한 AI 뉴스 영상 생성이 완료되었습니다!")

if __name__ == "__main__":
    run_batch_news()

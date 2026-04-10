import os
import numpy as np
import PIL.Image
import PIL.ImageEnhance
from moviepy import VideoClip
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import sys
import random
import json
import subprocess
import cv2
import unicodedata
import librosa

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

# --- [유틸리티] ---
def ease_in_out_sine(t):
    return -(np.cos(np.pi * t) - 1) / 2

def print_progress_bar(iteration, total, prefix='', suffix='', decimals=1, length=30, fill='█', printEnd="\r"):
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    print(f'\r{prefix} |{bar}| {percent}% {suffix}', end=printEnd)
    if iteration == total: print()

def get_audio_duration():
    base_downloads = os.path.join(os.path.expanduser("~"), "Downloads")
    audio_files = sorted([os.path.join(base_downloads, f) for f in os.listdir(base_downloads) 
                   if (f.endswith(".mp3") or f.endswith(".wav")) and ("_Full_Merged" in f or "_SFX_ONLY_" in f)], 
                   key=os.path.getmtime, reverse=True)
    if not audio_files:
        audio_files = sorted([os.path.join(base_downloads, f) for f in os.listdir(base_downloads) 
                             if f.endswith(".mp3") or f.endswith(".wav")], 
                             key=os.path.getmtime, reverse=True)
    
    if audio_files:
        try:
            y, sr = librosa.load(audio_files[0], sr=None)
            duration = librosa.get_duration(y=y, sr=sr)
            return duration, os.path.basename(audio_files[0])
        except: pass
    return None, None

def get_srt_durations():
    import re
    base_downloads = os.path.join(os.path.expanduser("~"), "Downloads")
    srt_files = sorted([os.path.join(base_downloads, f) for f in os.listdir(base_downloads) 
                   if f.endswith(".srt") and "최종" not in f], 
                   key=os.path.getmtime, reverse=True)
    
    if not srt_files: return None, None
    
    latest_srt = srt_files[0]
    durations = []
    try:
        with open(latest_srt, 'r', encoding='utf-8') as f:
            content = f.read()
        
        blocks = re.split(r'\n\s*\n', content.strip())
        for block in blocks:
            lines = block.split('\n')
            if len(lines) >= 3:
                time_line = lines[1]
                match = re.search(r'(\d+):(\d+):(\d+),(\d+)\s*-->\s*(\d+):(\d+):(\d+),(\d+)', time_line)
                if match:
                    start_ms = (int(match.group(1)) * 3600 + int(match.group(2)) * 60 + int(match.group(3))) * 1000 + int(match.group(4))
                    end_ms = (int(match.group(5)) * 3600 + int(match.group(6)) * 60 + int(match.group(7))) * 1000 + int(match.group(8))
                    dur_seconds = (end_ms - start_ms) / 1000.0
                    durations.append(dur_seconds)
        
        return durations, os.path.basename(latest_srt)
    except Exception as e:
        print(f"⚠️ SRT 파싱 오류: {e}")
        return None, None

def variable_speed_curve(t):
    """ 4단계 리듬: 초고속 -> 보통 -> 저속 -> 보통 (C1 Continuity 확보) """
    t_pts = [0.0, 0.2, 0.5, 0.8, 1.0]
    v_pts = [4.5, 1.8, 1.0, 0.2, 1.5]
    
    def get_v(curr_t):
        if curr_t <= t_pts[0]: return v_pts[0]
        if curr_t >= t_pts[-1]: return v_pts[-1]
        for i in range(len(t_pts)-1):
            if t_pts[i] <= curr_t <= t_pts[i+1]:
                p = (curr_t - t_pts[i]) / (t_pts[i+1] - t_pts[i])
                return v_pts[i] + (v_pts[i+1] - v_pts[i]) * p
        return v_pts[-1]

    steps = 40
    dt = t / steps if t > 0 else 0
    area = 0
    for i in range(steps):
        area += get_v(i * dt) * dt
    
    total_area = 0
    for i in range(len(t_pts)-1):
        dt_seg = t_pts[i+1] - t_pts[i]
        total_area += (v_pts[i] + v_pts[i+1]) / 2 * dt_seg
    
    return area / total_area

# --- [핵심: 시네마틱 V3.2 Square Edition] ---
def generate_square_cinematic(img_path, output_name, index, base_duration=3.0):
    fps = 24
    w, h = 1080, 1080 # 1:1 Resolution
    if not os.path.exists(img_path): return False

    duration = base_duration
    pattern_idx = index % 8

    if os.path.exists(output_name): os.remove(output_name)

    try:
        with PIL.Image.open(img_path) as p_img:
            img_rgb = p_img.convert("RGB")
            # 입력 이미지가 1:1이 아닐 경우 강제 리사이즈 (가득 채우기)
            if p_img.size[0] != p_img.size[1]:
                ratio = max(w / p_img.size[0], h / p_img.size[1])
                target_w, target_h = int(p_img.size[0] * ratio), int(p_img.size[1] * ratio)
                img_rgb = img_rgb.resize((target_w, target_h), PIL.Image.Resampling.LANCZOS)
        
        def get_state(prog):
            s = 1.3
            mx, my = 0, 0
            # 정사각형에 맞게 이동 범위 조절 (1080 기준 15%는 162px)
            if pattern_idx == 0: s = 1.1 + (0.4 * prog) # Zoom In
            elif pattern_idx == 1: my = int((-h * 0.12) + (h * 0.24 * prog)) # Pan Up/Down
            elif pattern_idx == 2: mx = int((-w * 0.12) + (w * 0.24 * prog)) # Pan Left/Right
            elif pattern_idx == 3: # Diagonal
                mx = int((-w * 0.1) + (w * 0.2 * prog))
                my = int((-h * 0.1) + (h * 0.2 * prog))
            elif pattern_idx == 4: # Tilt Down
                my = int((h * 0.12) - (h * 0.24 * prog))
            elif pattern_idx == 5: # Pan L
                mx = int((w * 0.12) - (w * 0.24 * prog))
            elif pattern_idx == 6: # Zoom Out
                s = 1.5 - (0.4 * prog)
            else: # Random Subtle Shift
                mx = int((w * 0.05) - (w * 0.1 * prog))
                my = int((-h * 0.05) + (h * 0.1 * prog))
            return s, mx, my

        def make_frame(t):
            g_prog = variable_speed_curve(t / duration)
            s, move_x, move_y = get_state(g_prog)

            nw, nh = int(w * s), int(h * s)
            img_resized = img_rgb.resize((nw, nh), PIL.Image.Resampling.LANCZOS)
            canvas = PIL.Image.new("RGB", (w, h), (0, 0, 0))
            canvas.paste(img_resized, (int(w/2 - nw/2 + move_x), int(h/2 - nh/2 + move_y)))
            
            frame_array = np.array(canvas, dtype=np.uint8)
            
            # Simple Fade
            fade = 1.0
            if t < 0.5: fade = t / 0.5
            elif t > (duration - 0.5): fade = (duration - t) / 0.5
            if fade < 1.0:
                frame_array = (frame_array.astype(np.float32) * fade).astype(np.uint8)

            return frame_array

        clip = VideoClip(make_frame, duration=duration)
        clip.write_videofile(output_name, fps=fps, codec="libx264", bitrate="6000k", threads=4, preset="ultrafast", audio=False, logger=None)
        return True
    except Exception as e:
        print(f"⚠️ 에러 ({os.path.basename(img_path)}): {e}")
        return False

def merge_videos_to_one(video_list, output_path):
    if not video_list: return
    list_file = os.path.join(os.path.dirname(output_path), "concat_list_square.txt")
    with open(list_file, "w", encoding="utf-8") as f:
        for v in video_list:
            f.write(f"file '{os.path.abspath(v)}'\n")
    
    print(f"\n🚀 [합치기] 모든 폴더 내 영상을 하나로...")
    cmd = [
        FFMPEG_PATH, "-y", "-f", "concat", "-safe", "0", 
        "-i", list_file, 
        "-fflags", "+genpts",
        "-c", "copy", output_path
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True)
        print(f"✅ 합치기 완료: {output_path}")
        if os.path.exists(list_file): os.remove(list_file)
    except subprocess.CalledProcessError as e:
        print(f"❌ 합치기 실패: {e.stderr.decode('utf-8', errors='ignore')}")

def run_batch_square():
    base_downloads = os.path.join(os.path.expanduser("~"), "Downloads")
    
    # [대표님 요청] '무협_생성' 폴더로 고정
    target_name = "무협_생성"
    target_dir = os.path.join(base_downloads, target_name)
    
    # 유니코드 정규화 문제(NFC/NFD) 대비 체크
    if not os.path.exists(target_dir):
        import unicodedata
        nfd_name = unicodedata.normalize('NFD', target_name)
        target_dir = os.path.join(base_downloads, nfd_name)

    if not os.path.exists(target_dir):
        print(f"❌ '{target_name}' 폴더를 찾을 수 없습니다. 경로를 확인해주세요: {target_dir}"); return
    
    images = sorted([f for f in os.listdir(target_dir) if f.lower().endswith((".png", ".jpg", ".jpeg"))])
    
    if not images: 
        print(f"❌ '{target_name}' 폴더 내에 이미지가 없습니다."); return

    print("\n" + "="*50)
    print("🎥 [STEP 03-2-1] 프리미엄 1:1 정사각형 시네마틱")
    print("   자막 실제 시간 동기화 (지능형 리듬) / 고화질 렌더링")
    print(f"📍 대상 폴더 고정: {target_name} (이미지 {len(images)}장)")
    print("="*50)
    
    audio_duration, audio_name = get_audio_duration()
    if audio_duration:
        print(f"🎵 오디오 총 길이 감지: {audio_name} ({audio_duration:.2f}s)")
    else:
        print("⚠️ 오디오를 찾을 수 없습니다. SRT를 기준으로 합니다.")

    # 1. 자막 청크(SRT 블록) 파싱
    srt_path = None
    import glob
    srt_candidates = sorted(glob.glob(os.path.join(base_downloads, "*.srt")), key=os.path.getmtime, reverse=True)
    if srt_candidates:
        srt_path = srt_candidates[0]
    
    srt_blocks = []
    if srt_path:
        import re
        try:
            with open(srt_path, 'r', encoding='utf-8') as f:
                content = f.read()
            raw_blocks = re.split(r'\n\s*\n', content.strip())
            for block in raw_blocks:
                lines = block.split('\n')
                if len(lines) >= 3:
                    time_line = lines[1]
                    match = re.search(r'(\d+):(\d+):(\d+),(\d+)\s*-->\s*(\d+):(\d+):(\d+),(\d+)', time_line)
                    if match:
                        start_sec = (int(match.group(1)) * 3600 + int(match.group(2)) * 60 + int(match.group(3))) + int(match.group(4))/1000.0
                        end_sec = (int(match.group(5)) * 3600 + int(match.group(6)) * 60 + int(match.group(7))) + int(match.group(8))/1000.0
                        srt_blocks.append({"start": start_sec, "end": end_sec})
            print(f"📄 SRT 자막 감지: {os.path.basename(srt_path)} (총 {len(srt_blocks)}개 블록)")
        except Exception as e:
            print(f"⚠️ SRT 로드 에러: {e}")

    # [지능형 동기화 -> 3초 고정 모드]
    # 대표님 요청: 무조건 장당 3초로 고정
    per_img_dur = 3.0
    
    print(f"⚖️ 3초 고정 배분 모드: 이미지 {len(images)}장 x 3.0s = 총 {len(images)*per_img_dur:.2f}s 예상")

    for i, img_name in enumerate(images):
        img_path = os.path.join(target_dir, img_name)
        v_dir = os.path.dirname(img_path)
        v_base = f"{i+1:03d}_{os.path.splitext(img_name)[0]}.mp4"
        v_name = os.path.join(v_dir, v_base)
        
        to_process.append((img_path, v_name, i, img_name, per_img_dur))

    print(f"🚀 {len(to_process)}개의 파일 생성을 시작합니다... (장당 3.0초 고정)")

    print(f"🚀 {len(to_process)}개의 파일 생성을 시작합니다... (리듬: 길이 기반 지능형 분할 3.0s)")
    
    # 영상 조각들의 실제 파일 이름을 순번을 붙여서 확정
    final_to_process = []
    for i, (p, v, idx, n, dur) in enumerate(to_process):
        # 3자리 순번 + 원본이름 (예: 001_Whisk_12345.mp4)
        v_dir = os.path.dirname(v)
        v_base = os.path.basename(v)
        new_v_name = os.path.join(v_dir, f"{i+1:03d}_{v_base}")
        final_to_process.append((p, new_v_name, idx, n, dur))

    completed = 0
    total = len(final_to_process)
    print_progress_bar(0, total, prefix='진행률:', suffix='준비 중...', length=40)
    
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {executor.submit(generate_square_cinematic, p, v, idx, dur): n for p, v, idx, n, dur in final_to_process}
        for future in as_completed(futures):
            name = futures[future]
            completed += 1
            res = future.result()
            status = "완료" if res else "실패"
            print_progress_bar(completed, total, prefix='진행률:', suffix=f"{status} ({name[:12]}...)", length=40)
    
    generated_videos = [v for _, v, _, _, _ in final_to_process if os.path.exists(v)]
    if generated_videos:
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        final_merged = os.path.join(target_dir, f"combined_square_{timestamp}.mp4")
        merge_videos_to_one(generated_videos, final_merged)
    
    print(f"\n✨ 모든 영상이 자막 실제 시간 동기화 버전으로 완성되었습니다! ({timestamp})")

if __name__ == "__main__":
    run_batch_square()

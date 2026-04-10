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
import librosa  # 오디오 길이 분석용 추가

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

# --- [추가: 오디오 길이 분석] ---
def get_audio_duration():
    base_downloads = os.path.join(os.path.expanduser("~"), "Downloads")
    # 최신 Full_Merged, SFX_ONLY 또는 일반 WAV/MP3 오디오 탐색
    audio_files = sorted([os.path.join(base_downloads, f) for f in os.listdir(base_downloads) 
                   if (f.endswith(".mp3") or f.endswith(".wav")) and ("_Full_Merged" in f or "_SFX_ONLY_" in f)], 
                   key=os.path.getmtime, reverse=True)
    if not audio_files:
        # 없으면 일반 mp3/wav 중 가장 최신 것
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

# --- [고급 변속 곡선: Velocity Integration] ---
def variable_speed_curve(t):
    """ 4단계 리듬: 초고속 -> 보통 -> 저속 -> 보통 (C1 Continuity 확보) """
    t_pts = [0.0, 0.2, 0.5, 0.8, 1.0]
    v_pts = [4.5, 1.8, 1.0, 0.2, 1.5] # 속도감 조절
    
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

# --- [핵심: 시네마틱 V3.2 Vertical Edition - Clean Ver] ---
def generate_vertical_cinematic(img_path, output_name, index, base_duration=6.0):
    fps = 24
    w, h = 1080, 1920
    if not os.path.exists(img_path): return False

    duration = base_duration
    pattern_idx = index % 9

    # [Cleanup] 작업 시작 전 동일 인덱스 파일이 있으면 삭제하여 에러 방지
    if os.path.exists(output_name): os.remove(output_name)

    try:
        with PIL.Image.open(img_path) as p_img:
            img_rgb = p_img.convert("RGB")
        
        def get_stage1_state(prog):
            s = 1.3
            mx, my = 0, 0
            if pattern_idx == 0: s = 1.1 + (0.4 * prog)
            elif pattern_idx == 1: my = int((-h * 0.15) + (h * 0.3 * prog))
            elif pattern_idx == 2: mx = int((-w * 0.15) + (w * 0.3 * prog))
            elif pattern_idx == 3: # Diagonal
                mx = int((-w * 0.1) + (w * 0.2 * prog))
                my = int((-h * 0.1) + (h * 0.2 * prog))
            elif pattern_idx == 4: # Tilt Up
                my = int((h * 0.15) - (h * 0.3 * prog))
            elif pattern_idx == 5: # Pan L
                mx = int((w * 0.15) - (w * 0.1 * prog))
            elif pattern_idx == 6: # Zoom Out
                s = 1.5 - (0.3 * prog)
            else: # Random Pan Mix
                mx = int((w * 0.1) - (w * 0.2 * prog))
                my = int((-h * 0.1) + (h * 0.2 * prog))
            return s, mx, my

        s_b, mx_b, my_b = get_stage1_state(1.0)

        def make_frame(t):
            # [0-1초 속도 곡선 적용] 전역 진행률 계산
            g_prog = variable_speed_curve(t / duration)
            
            # 전역 진행률을 기준으로 1단계(이동)와 2단계(얼굴줌) 배분 (50:50)
            if g_prog <= 0.5:
                # 1단계: 이동 (g_prog 0.0~0.5 -> s1_prog 0.0~1.0)
                s1_prog = g_prog / 0.5
                s, move_x, move_y = get_stage1_state(s1_prog)
            else:
                # 2단계: 얼굴줌 (g_prog 0.5~1.0 -> s2_prog 0.0~1.0)
                s2_prog = (g_prog - 0.5) / 0.5
                s = s_b + (0.8 * s2_prog) 
                target_y_c = h * 0.25 # 상단 25% 지점
                move_x = int(mx_b * (1.0 - s2_prog)) 
                move_y = int(my_b + (target_y_c - my_b) * s2_prog)

            nw, nh = int(w * s), int(h * s)
            img_resized = img_rgb.resize((nw, nh), PIL.Image.Resampling.LANCZOS)
            canvas = PIL.Image.new("RGB", (w, h), (0, 0, 0))
            canvas.paste(img_resized, (int(w/2 - nw/2 + move_x), int(h/2 - nh/2 + move_y)))
            
            # [Clean Mode]
            frame_array = np.array(canvas, dtype=np.uint8)
            
            # Simple Fade only
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

# --- [신규 추가: 영상 합치기 함수] ---
def merge_videos_to_one(video_list, output_path):
    if not video_list: return
    list_file = os.path.join(os.path.dirname(output_path), "concat_list.txt")
    with open(list_file, "w", encoding="utf-8") as f:
        for v in video_list:
            f.write(f"file '{os.path.abspath(v)}'\n")
    
    print(f"\n🚀 [영상 합치기] 하나로 병합 시작...")
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

def run_batch_vertical():
    base_downloads = os.path.join(os.path.expanduser("~"), "Downloads")
    # [NFC/NFD 통합 대응] 모든 한글 폴더 이름을 표준형으로 변환해서 검색
    def normalize_name(n):
        return unicodedata.normalize('NFC', n)

    search_prefixes = ("다이어리_", "무협_", "틱톡_", "시나리오_", "막장_", "drama_")
    
    subdirs = []
    for d in os.listdir(base_downloads):
        full_path = os.path.join(base_downloads, d)
        if not os.path.isdir(full_path):
            continue
            
        norm_d = normalize_name(d)
        if any(norm_d.startswith(p) for p in search_prefixes):
            subdirs.append(full_path)
            
    # 최신 순 정렬
    subdirs = sorted(subdirs, key=os.path.getmtime, reverse=True)
    
    target_dir = None
    if subdirs:
        target_dir = subdirs[0] # 가장 최신 폴더
        images = sorted([f for f in os.listdir(target_dir) if f.endswith(".png")])
    else:
        # 폴더가 없으면 Downloads 폴더 자체에서 PNG 검색 (유남규 장면_.. 형식 대응)
        images = sorted([f for f in os.listdir(base_downloads) if f.endswith(".png")])
        if images:
            target_dir = base_downloads

    if not target_dir or not images: 
        print("❌ 작업할 폴더나 이미지 파일을 찾을 수 없습니다."); return

    print("\n" + "="*50)
    print("🎥 [STEP 03-2-1] 프리미엄 세로 시네마틱 + 자동 병합")
    print("   1080x1920 / 세로 이동 최적화 / 합치기 기능 추가")
    print("="*50)
    
    # [Sync] 3초 고정 배분 (02-3 프롬프팅 주기와 일치)
    audio_duration, audio_name = get_audio_duration()
    base_duration = 3.0
    
    if audio_duration:
        print(f"🎵 오디오 감지: {audio_name} ({audio_duration:.1f}s)")
        print(f"⚖️ 3초 고정 모드: 이미지 {len(images)}장 x 3.0s = {len(images)*base_duration:.1f}s")
    else:
        print(f"⚖️ 3초 고정 모드: 이미지 {len(images)}장 x 3.0s = {len(images)*base_duration:.1f}s")

    to_process = []
    for i, img_name in enumerate(images):
        img_path = os.path.join(target_dir, img_name)
        v_name = img_path.replace(".png", ".mp4")
        to_process.append((img_path, v_name, i, img_name))

    print(f"🚀 {len(to_process)}개의 파일을 세로 영화급 영상으로 변환합니다...")
    
    completed = 0
    total = len(to_process)
    print_progress_bar(0, total, prefix='진행률:', suffix='준비 중...', length=40)
    
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {executor.submit(generate_vertical_cinematic, p, v, i, base_duration): n for p, v, i, n in to_process}
        for future in as_completed(futures):
            name = futures[future]
            completed += 1
            res = future.result()
            status = "완료" if res else "실패"
            print_progress_bar(completed, total, prefix='진행률:', suffix=f"{status} ({name[:12]}...)", length=40)
    
    # --- [병합 파트 추가] ---
    generated_videos = [v for _, v, _, _ in to_process if os.path.exists(v)]
    if generated_videos:
        final_merged = os.path.join(base_downloads, "combined_background.mp4")
        merge_videos_to_one(generated_videos, final_merged)
    
    print("\n✨ 모든 영상이 하나로 합쳐져 다운로드 폴더에 저장되었습니다!")

if __name__ == "__main__":
    run_batch_vertical()

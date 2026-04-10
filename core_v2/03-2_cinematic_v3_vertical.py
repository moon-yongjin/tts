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

# --- [추가: 자막 파일 길이 분석] ---
def get_srt_durations(audio_duration=None):
    """가장 최신 .srt 파일을 읽어 문장별 지속 시간을 초 단위로 반환 (무진동/여백 싱크)"""
    import re
    base_downloads = os.path.join(os.path.expanduser("~"), "Downloads")
    srt_files = sorted([os.path.join(base_downloads, f) for f in os.listdir(base_downloads) 
                       if f.endswith(".srt")], key=os.path.getmtime, reverse=True)
    if not srt_files: return []
    
    srt_path = srt_files[0]
    print(f"📄 자막 연동 감지: {os.path.basename(srt_path)}")
    
    with open(srt_path, 'r', encoding='utf-8-sig') as f:
        content = f.read()
    
    blocks = re.split(r'\n\s*\n', content.strip())
    durations = []
    
    def parse_srt_time(t_str):
        if not t_str: return 0.0
        t_str = t_str.replace(' ', '').replace('\t', '')
        h, m, s_ms = t_str.split(':')
        s, ms = s_ms.split(',')
        return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000.0

    for i in range(len(blocks)):
        lines = blocks[i].splitlines()
        if len(lines) >= 2:
            times = re.findall(r'(\d{2}:\d{2}:\d{2},\d{3})', lines[1])
            if len(times) >= 2:
                curr_start = parse_srt_time(times[0])
                
                # 🚀 [핵심] 다음 문장의 시작 시간 찾기 (여백 및 프레임 버벅임 gap 흡수)
                next_start = None
                if i + 1 < len(blocks):
                    next_lines = blocks[i+1].splitlines()
                    if len(next_lines) >= 2:
                        next_times = re.findall(r'(\d{2}:\d{2}:\d{2},\d{3})', next_lines[1])
                        if len(next_times) >= 2:
                            next_start = parse_srt_time(next_times[0])

                if next_start is not None:
                    duration = next_start - curr_start
                else:
                    # 마지막 문장 ➡️ 오디오 총 길이에 맞추거나 마진 배분
                    curr_end = parse_srt_time(times[1])
                    if audio_duration and audio_duration > curr_start:
                        duration = audio_duration - curr_start
                    else:
                        duration = (curr_end - curr_start) + 3.0 # 마진

                durations.append(max(2.0, duration))
    return durations
def get_audio_duration():
    base_downloads = os.path.join(os.path.expanduser("~"), "Downloads")
    # 최신 Full_Merged 또는 SFX_ONLY 오디오 탐색
    audio_files = sorted([os.path.join(base_downloads, f) for f in os.listdir(base_downloads) 
                   if f.endswith(".mp3") and ("_Full_Merged" in f or "_SFX_ONLY_" in f)], 
                   key=os.path.getmtime, reverse=True)
    if not audio_files:
        # 없으면 일반 mp3 중 가장 최신 것
        audio_files = sorted([os.path.join(base_downloads, f) for f in os.listdir(base_downloads) if f.endswith(".mp3")], 
                             key=os.path.getmtime, reverse=True)
    
    if audio_files:
        try:
            # 🚀 [속도 업] load 없이 path로 직접 길이를 읽어 에러를 방지합니다
            duration = librosa.get_duration(path=audio_files[0])
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
def generate_vertical_cinematic(img_path, output_name, index, base_duration=3.0):
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
        clip.write_videofile(output_name, fps=fps, codec="libx264", bitrate="8000k", threads=4, preset="ultrafast", audio=False, logger=None)
        return True
    except Exception as e:
        print(f"⚠️ 에러 ({os.path.basename(img_path)}): {e}")
        return False

def run_batch_vertical():
    base_downloads = os.path.join(os.path.expanduser("~"), "Downloads")
    # [NFC/NFD 통합 대응] 모든 한글 폴더 이름을 표준형으로 변환해서 검색
    def normalize_name(n):
        return unicodedata.normalize('NFC', n)

    search_prefixes = ("다이어리_", "무협_", "틱톡_", "시나리오_", "막장_", "AutoDirector_")
    
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
    
    if not subdirs: 
        print("❌ 작업할 폴더(다이어리/무협/틱톡/시나리오 등)를 찾을 수 없습니다."); return
    target_dir = subdirs[0] # 가장 최신 폴더
    
    def extract_number(n):
        import re
        nums = re.findall(r'\d+', n)
        return int(nums[0]) if nums else 0

    # PNG뿐만 아니라 JPG, JPEG 확장자도 모두 수집
    valid_extensions = ('.png', '.PNG', '.jpg', '.JPG', '.jpeg', '.JPEG', '.webp', '.WEBP')
    images = sorted([f for f in os.listdir(target_dir) if f.lower().endswith(valid_extensions)], key=extract_number)
    if not images: 
        print("❌ 폴더 내 이미지 파일이 없습니다."); return

    print("\n" + "="*50)
    print("🎥 [STEP 03-2] 프리미엄 세로 시네마틱 (V3.2 Vertical)")
    print("   1080x1920 / 세로 이동 최적화 / 고화질 8000k")
    print("="*50)
    
    # 💡 기본 가동 모드 (환경 변수가 있으면 그 값을, 없으면 3.0초)
    base_duration = float(os.getenv("CINEMATIC_DURATION", 3.0))
    srt_durations = []

    to_process = []
    for i, img_name in enumerate(images):
        img_path = os.path.join(target_dir, img_name)
        # 확장자를 제거하고 _v2.mp4를 붙임
        base_name = os.path.splitext(img_name)[0]
        v_name = os.path.join(target_dir, f"{base_name}_v2.mp4")
        
        # 개별 재생 길이 할당
        clip_duration = base_duration
        if i < len(srt_durations):
            clip_duration = srt_durations[i]
            
        # generate_vertical_cinematic parameter: (img_path, output_name, index, base_duration)
        to_process.append((img_path, v_name, i, clip_duration, img_name))

    print(f"🚀 {len(to_process)}개의 파일을 세로 영화급 영상으로 변환합니다...")
    
    completed = 0
    total = len(to_process)
    print_progress_bar(0, total, prefix='진행률:', suffix='준비 중...', length=40)
    
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {executor.submit(generate_vertical_cinematic, p, v, i, d): n for p, v, i, d, n in to_process}
        for future in as_completed(futures):
            name = futures[future]
            completed += 1
            res = future.result()
            status = "완료" if res else "실패"
            print_progress_bar(completed, total, prefix='진행률:', suffix=f"{status} ({name[:12]}...)", length=40)
    
    print("\n✨ 모든 영상이 고품질 세로 시네마틱으로 완성되었습니다!")

if __name__ == "__main__":
    run_batch_vertical()

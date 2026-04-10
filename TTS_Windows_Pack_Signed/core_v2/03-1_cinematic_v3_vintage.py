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

# --- [고급 이펙트 함수] ---

def apply_chromatic_aberration(frame, intensity=3):
    """색수차 효과 (R/B 채널 분리)"""
    h, w, _ = frame.shape
    new_frame = frame.copy()
    # Red 채널 왼쪽 이동
    new_frame[:, intensity:, 0] = frame[:, :-intensity, 0]
    # Blue 채널 오른쪽 이동
    new_frame[:, :-intensity, 2] = frame[:, intensity:, 2]
    return new_frame

def apply_pillow_distortion(frame, strength=0.1):
    """필로우(볼록/오목) 렌즈 왜곡 효과"""
    h, w, _ = frame.shape
    k1 = strength # 왜곡 계수
    cam_matrix = np.array([[w, 0, w/2], [0, h, h/2], [0, 0, 1]], dtype=np.float32)
    dist_coeffs = np.array([k1, 0, 0, 0], dtype=np.float32)
    new_frame = cv2.undistort(frame, cam_matrix, dist_coeffs)
    return new_frame

# --- [핵심: 시네마틱 V3.1 빈티지 에디션] ---
def generate_master_cinematic(img_path, output_name, index, base_duration=6.0):
    """
    고급 빈티지 에디션: 6종 무빙 + 색수차 + 왜곡 + 필름번 + 레터박스
    """
    fps = 18
    w, h = 1280, 720
    if not os.path.exists(img_path): return False

    # [0] 설정 세팅
    speed_factor = random.choice([0.8, 0.9, 1.0, 1.1, 1.2])
    duration = base_duration * speed_factor
    pattern_idx = index % 6
    
    # 랜덤 이펙트 스위치
    use_ca = (index % 3 == 0) # 색수차
    use_distort = (index % 4 == 0) # 왜곡
    use_film_burn = (index % 5 == 0) # 필름번
    use_letterbox = True # 레터박스는 시네마틱 기본

    try:
        with PIL.Image.open(img_path) as p_img:
            img_rgb = p_img.convert("RGB")
        
        def make_frame(t):
            raw_prog = t / duration
            prog = ease_in_out_sine(raw_prog)
            
            # [1] 6종 무빙 (Keyframe 6 Types)
            s = 1.25 # 기본 스케일
            move_x, move_y = 0, 0
            
            if pattern_idx == 0: s = 1.1 + (0.3 * prog) # Zoom In
            elif pattern_idx == 1: s = 1.4 - (0.3 * prog) # Zoom Out
            elif pattern_idx == 2: move_x = int((-w * 0.15) + (w * 0.3 * prog)) # Pan L to R
            elif pattern_idx == 3: move_x = int((w * 0.15) - (w * 0.3 * prog)) # Pan R to L
            elif pattern_idx == 4: move_y = int((-h * 0.1) + (h * 0.2 * prog)) # Tilt Down
            elif pattern_idx == 5: move_y = int((h * 0.1) - (h * 0.2 * prog)) # Tilt Up

            nw, nh = int(w * s), int(h * s)
            img_resized = img_rgb.resize((nw, nh), PIL.Image.Resampling.LANCZOS)
            canvas = PIL.Image.new("RGB", (w, h), (0, 0, 0))
            canvas.paste(img_resized, (int(w/2 - nw/2 + move_x), int(h/2 - nh/2 + move_y)))
            frame_array = np.array(canvas, dtype=np.float32)

            # [2] 고급 시각 효과 (AI & CV2)
            
            # 2-1. 왜곡 (Distortion)
            if use_distort:
                dist_str = 0.05 * (1.0 - abs(0.5 - raw_prog)*2) # 중간에 왜곡 강하게
                frame_array = apply_pillow_distortion(frame_array, strength=dist_str)

            # 2-2. 색수차 (Chromatic Aberration)
            if use_ca:
                ca_int = int(4 * (1.0 - abs(0.5 - raw_prog)*2)) + 1
                frame_array = apply_chromatic_aberration(frame_array, intensity=ca_int)

            # 2-3. 필름 그레인 & 노이즈 (Grain)
            noise = np.random.normal(0, 18 * (1.0 + 0.5 * np.sin(t*10)), (h, w, 3))
            frame_array += noise

            # 2-4. 더스트 & 스크래치 (Dust & Scratches)
            for _ in range(int(3 * raw_prog + 1)):
                if random.random() < 0.2:
                    sx = random.randint(0, w-1)
                    frame_array[:, sx:sx+2, :] += random.randint(50, 120) # 세로선
                if random.random() < 0.1:
                    dx, dy = random.randint(0, w-5), random.randint(0, h-5)
                    frame_array[dy:dy+3, dx:dx+3, :] += 150 # 먼지 점

            # 2-5. 필름 번 (Film Burn / Light Leak)
            if use_film_burn:
                burn_pos = int((t * 400) % (w + 400)) - 200
                burn_mask = np.zeros((h, w, 3), dtype=np.float32)
                if 0 <= burn_pos < w:
                    cv2.circle(burn_mask, (burn_pos, h//2), 300, (255, 120, 30), -1)
                    cv2.blur(burn_mask, (150, 150), burn_mask)
                    frame_array += burn_mask * 0.4 * (1.0 - abs(0.5 - raw_prog)*2)

            # 2-6. 비네트 (Vignette)
            Y, X = np.ogrid[:h, :w]
            dist = np.sqrt(((X-w/2)/(w/2))**2 + ((Y-h/2)/(h/2))**2)
            v_mask = np.clip(1.0 - (dist - 0.2) * 1.6, 0.35, 1.0)
            for i in range(3): frame_array[:, :, i] *= v_mask

            # [3] 시네마틱 레터박스 (Letterbox)
            if use_letterbox:
                lb_h = int(h * 0.12) # 상하 12% 블랙바
                frame_array[:lb_h, :, :] = 0
                frame_array[-lb_h:, :, :] = 0

            # [4] 트랜지션 & 색보정 (깜빡임 효과 포함)
            flicker = 1.0 + (random.random() * 0.08 - 0.04)
            frame_array *= flicker
            
            fade = 1.0
            if t < 0.6: fade = t / 0.6
            elif t > (duration - 0.6): fade = (duration - t) / 0.6
            frame_array *= fade

            return np.clip(frame_array, 0, 255).astype(np.uint8)

        clip = VideoClip(make_frame, duration=duration)
        # 고화질 유지를 위해 비트레이트 4000k 유지
        clip.write_videofile(output_name, fps=fps, codec="libx264", bitrate="4000k", threads=4, preset="ultrafast", audio=False, logger=None)
        return True
    except Exception as e:
        print(f"⚠️ 에러 ({os.path.basename(img_path)}): {e}")
        return False

def run_batch_master():
    base_downloads = os.path.join(os.path.expanduser("~"), "Downloads")
    subdirs = [os.path.join(base_downloads, d) for d in os.listdir(base_downloads) 
               if os.path.isdir(os.path.join(base_downloads, d)) and (d.startswith("무협_생성_") or d.startswith("무협_로컬생성_"))]
    
    if not subdirs: return
    target_dir = sorted(subdirs)[-1]
    
    images = sorted([f for f in os.listdir(target_dir) if f.endswith(".png")])
    if not images: return

    print("\n" + "="*50)
    print("🎥 [STEP 03-1] 마스터 시네마틱 (V3.1 Elite)")
    print("   색수차 + 왜곡 + 필름번 + 레터박스 + 8000k")
    print("="*50)
    
    base_duration = 6.0
    user_input = input(f"👉 기준 지속 시간 입력 [엔터 = 6.0초]: ").strip()
    if user_input:
        try: base_duration = float(user_input)
        except: pass

    to_process = []
    for i, img_name in enumerate(images):
        img_path = os.path.join(target_dir, img_name)
        v_name = img_path.replace(".png", ".mp4")
        to_process.append((img_path, v_name, i, img_name))

    print(f"🚀 {len(to_process)}개의 파일을 엘리트급 영상으로 변환합니다...")
    
    completed = 0
    total = len(to_process)
    print_progress_bar(0, total, prefix='진행률:', suffix='준비 중...', length=40)
    
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {executor.submit(generate_master_cinematic, p, v, i, base_duration): n for p, v, i, n in to_process}
        for future in as_completed(futures):
            name = futures[future]
            completed += 1
            res = future.result()
            status = "완료" if res else "실패"
            print_progress_bar(completed, total, prefix='진행률:', suffix=f"{status} ({name[:12]}...)", length=40)
    
    print("\n✨ 모든 영상이 압도적인 시네마틱 감성으로 완성되었습니다!")

if __name__ == "__main__":
    run_batch_master()

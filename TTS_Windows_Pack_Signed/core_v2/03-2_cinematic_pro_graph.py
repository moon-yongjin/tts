import os
import numpy as np
import PIL.Image
import cv2
from rembg import remove
from moviepy import VideoClip
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import sys
import random
import json
import subprocess

# [윈도우 호환성]
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

# FFmpeg 경로 설정 (Mac 전용)
FFMPEG_PATH = "/opt/homebrew/bin/ffmpeg"
if not os.path.exists(FFMPEG_PATH):
    # 다른 경로 시도 (Homebrew 기본 경로)
    FFMPEG_PATH = "/usr/local/bin/ffmpeg"

if os.path.exists(FFMPEG_PATH):
    try:
        from moviepy.config import change_settings
        change_settings({"FFMPEG_BINARY": FFMPEG_PATH})
    except ImportError:
        os.environ["IMAGEIO_FFMPEG_EXE"] = FFMPEG_PATH

# --- [유틸리티: Easing 함수] ---
def ease_in_out_sine(t):
    """부드러운 카메라 움직임을 위한 S-커브 가속/감속"""
    return -(np.cos(np.pi * t) - 1) / 2

# --- [그래프 UI 함수] ---
def print_progress_bar(iteration, total, prefix='', suffix='', decimals=1, length=30, fill='█', printEnd="\r"):
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    print(f'\r{prefix} |{bar}| {percent}% {suffix}', end=printEnd)
    if iteration == total: print()

# --- [핵심: 시네마틱 프로 생성기] ---
def generate_pro_cinematic(img_path, output_name, index, duration=6.0):
    """
    프로 버전: Easing Keyframes + 3D Parallax Separation + 고급 FX
    """
    fps = 18
    w, h = 1280, 720
    if not os.path.exists(img_path): return False

    try:
        # [1] 이미지 로드 및 AI 배경 분리 시도
        with PIL.Image.open(img_path) as p_img:
            img_rgb = p_img.convert("RGB")
            
            # 패럴랙스 (Parallax) 효과를 위해 배경 분리 시도
            # (매번 하면 느릴 수 있으므로 2장당 한 번 혹은 랜덤하게 시도하거나, 성능 좋으면 상시 적용)
            try:
                fg_rgba = remove(img_rgb)
                bg_mask = np.array(fg_rgba)[:, :, 3] > 0
                has_fg = np.sum(bg_mask) > (w * h * 0.05) # 전체의 5% 이상일 때만 분리 적용
            except:
                has_fg = False

        # [배경 인페인팅/준비]
        orig_np = np.array(img_rgb)
        if has_fg:
            # OpenCV용 BGR 변환
            cv_img = cv2.cvtColor(orig_np, cv2.COLOR_RGB2BGR)
            mask = (np.array(fg_rgba)[:, :, 3] > 0).astype(np.uint8) * 255
            # 배경 복원
            bg_cv = cv2.inpaint(cv_img, mask, 3, cv2.INPAINT_TELEA)
            bg_np = cv2.cvtColor(bg_cv, cv2.COLOR_BGR2RGB)
            fg_np = np.array(fg_rgba)
        else:
            bg_np = orig_np
            fg_np = None

        def make_frame(t):
            # t: 0.0 ~ duration
            raw_prog = t / duration
            # Easing 적용 (S-커브)
            prog = ease_in_out_sine(raw_prog)
            
            is_even = index % 2 == 0
            
            # [2] 하이브리드 입체 무빙
            if has_fg:
                # 배경 무빙 (매우 느림)
                if is_even: bs = 1.05 - (0.05 * prog); bx, by = int(10 * prog), int(5 * prog)
                else: bs = 1.0 + (0.05 * prog); bx, by = int(-10 * prog), int(-5 * prog)
                
                # 배경 캔버스
                bw, bh = int(w * bs), int(h * bs)
                bg_img = PIL.Image.fromarray(bg_np).resize((bw, bh), PIL.Image.Resampling.LANCZOS)
                canvas = PIL.Image.new("RGB", (w, h), (0, 0, 0))
                canvas.paste(bg_img, (int(w/2 - bw/2 + bx), int(h/2 - bh/2 + by)))
                
                # 캐릭터 무빙 (반대 방향/더 빠름)
                if is_even: fs = 1.1 + (0.1 * prog); fx, fy = int(-20 * prog), int(-10 * prog)
                else: fs = 1.2 - (0.1 * prog); fx, fy = int(20 * prog), int(10 * prog)
                
                fw, fh = int(w * fs), int(h * fs)
                fg_img = PIL.Image.fromarray(fg_np).resize((fw, fh), PIL.Image.Resampling.LANCZOS)
                canvas.paste(fg_img, (int(w/2 - fw/2 + fx), int(h/2 - fh/2 + fy)), fg_img)
                frame_array = np.array(canvas, dtype=np.float32)
            else:
                # 일반 Ken Burns (Easing 적용)
                if is_even: s = 1.3 - (0.2 * prog); mx, my = int(35 * prog), int(15 * prog)
                else: s = 1.1 + (0.2 * prog); mx, my = int(-35 * prog), int(-15 * prog)
                
                nw, nh = int(w * s), int(h * s)
                img_resized = img_rgb.resize((nw, nh), PIL.Image.Resampling.BICUBIC)
                canvas = PIL.Image.new("RGB", (w, h), (0, 0, 0))
                canvas.paste(img_resized, (int(w/2 - nw/2 + mx), int(h/2 - nh/2 + my)))
                frame_array = np.array(canvas, dtype=np.float32)

            # [3] 고성능 먼지 FX (입자감 강화)
            for _ in range(12):
                seeds = [33, 77, 11, 88, 55, 22]
                sd = seeds[_ % len(seeds)]
                rx = int((index*sd + _*250) % w)
                ry = int((index*17 + t*80 + _*210) % h)
                dust_fade = 0.3 * (1.0 - abs(0.5 - raw_prog)*2) # 중간에 가장 선명
                size = 1 + (_ % 2)
                frame_array[max(0,ry-size):min(h,ry+size), max(0,rx-size):min(w,rx+size), :] += 180 * dust_fade

            # [4] 고급 시네마 효과 (다양성 강화)
            eff_idx = index % 15
            fade = 1.0
            if t < 0.8: fade = t / 0.8
            elif t > (duration - 0.8): fade = (duration - t) / 0.8

            if fade > 0:
                if eff_idx == 0: # 화염 일렁임
                    frame_array[:, :, 0] += (np.sin(t * 18) * 15 + 10) * fade
                elif eff_idx in [3, 13]: # 시네마틱 비네트 (Edge)
                    Y, X = np.ogrid[:h, :w]
                    dist = np.sqrt(((X-w/2)/(w/2))**2 + ((Y-h/2)/(h/2))**2)
                    v_mask = np.clip(1.0 - (dist - 0.3) * 1.8 * fade, 0.3, 1.0)
                    for i in range(3): frame_array[:, :, i] *= v_mask
                elif eff_idx == 6: # 빛 번짐 (Anamorphic Flare)
                    leak_x = int((t * 240) % w)
                    frame_array[h//2-30:h//2+30, max(0, leak_x-200):min(w, leak_x+200), 2] += 40 * fade
                elif eff_idx == 8: # 극강의 색수차
                    frame_array[:, 3:, 0] = frame_array[:, :-3, 0]
                    frame_array[:, :-3, 2] = frame_array[:, 3:, 2]
                elif eff_idx == 2: # 벼락 효과
                    if (int(t*100) % 120 < 4): frame_array += 100 * fade

            # [5] 최종 트랜지션 (시작/끝 0.5초)
            if t < 0.5: frame_array *= (t / 0.5)
            if t > (duration - 0.5): frame_array *= ((duration - t) / 0.5)

            return np.clip(frame_array, 0, 255).astype(np.uint8)

        clip = VideoClip(make_frame, duration=duration)
        clip.write_videofile(output_name, fps=fps, codec="libx264", bitrate="4000k", threads=4, preset="ultrafast", audio=False, logger=None)
        return True
    except Exception as e:
        print(f"⚠️ 에러 ({os.path.basename(img_path)}): {e}")
        return False

def run_batch_video_pro():
    # 1. 대상 폴더 찾기
    base_downloads = os.path.join(os.path.expanduser("~"), "Downloads")
    subdirs = [os.path.join(base_downloads, d) for d in os.listdir(base_downloads) 
               if os.path.isdir(os.path.join(base_downloads, d)) and (d.startswith("무협_생성_") or d.startswith("무협_로컬생성_"))]
    
    if not subdirs: 
        print("❌ 작업 폴더를 찾을 수 없습니다.")
        return
    
    target_dir = sorted(subdirs)[-1]
    print(f"🎬 [PRO RENDERING] 대상: {target_dir}")
    
    images = sorted([f for f in os.listdir(target_dir) if f.endswith(".png")])
    if not images: return

    # 3. 설정 및 시간 입력
    duration = 6.0
    print("\n" + "="*50)
    print("🎥 [STEP 03-1] 시네마틱 프로 (V5 Hybrid)")
    print(f"   AI 배경 분리 + S-커브 무빙 + 입자 강화")
    print("="*50)
    
    user_input = input(f"👉 지속 시간(초) 입력 [엔터 = 6.0초]: ").strip()
    if user_input:
        try: duration = float(user_input)
        except: pass

    to_process = []
    for i, img_name in enumerate(images):
        img_path = os.path.join(target_dir, img_name)
        v_name = img_path.replace(".png", ".mp4")
        to_process.append((img_path, v_name, i, img_name))

    print(f"\n🚀 {len(to_process)}개의 파일을 프로급으로 변환합니다...")
    
    completed = 0
    total = len(to_process)
    print_progress_bar(0, total, prefix='진행률:', suffix='시작 중...', length=40)
    
    # [주의] rembg 모델 로딩 시간이 있으므로 초기 1개는 조금 느릴 수 있습니다.
    # Mac M1/M2/M3 환경에서는 병렬 처리를 적절히 조절 (배경 분리는 CPU/GPU 소모가 큼)
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = {executor.submit(generate_pro_cinematic, p, v, i, duration): n for p, v, i, n in to_process}
        
        for future in as_completed(futures):
            name = futures[future]
            completed += 1
            res = future.result()
            msg = f"완료 ({name[:15]}...)" if res else f"❌ 실패 ({name[:15]}...)"
            print_progress_bar(completed, total, prefix='진행률:', suffix=msg, length=40)
    
    print("\n✨ 모든 영상이 프로 장인의 손길로 완성되었습니다!")

if __name__ == "__main__":
    run_batch_video_pro()

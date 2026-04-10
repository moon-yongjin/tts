import os
import numpy as np
import PIL.Image
from moviepy import VideoClip
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import sys
import random
import json
import io
import subprocess

# [경로 설정]
BASE_PATH = os.path.dirname(os.path.abspath(__file__))

# FFmpeg 경로 설정
FFMPEG_PATH = r"C:\Users\moori\Downloads\ffmpeg-2026-01-07-git-af6a1dd0b2-essentials_build\ffmpeg-2026-01-07-git-af6a1dd0b2-essentials_build\bin\ffmpeg"
if os.path.exists(FFMPEG_PATH):
    try:
        from moviepy.config import change_settings
        change_settings({"FFMPEG_BINARY": FFMPEG_PATH})
    except ImportError:
        os.environ["IMAGEIO_FFMPEG_EXE"] = FFMPEG_PATH
FFPROBE_PATH = FFMPEG_PATH.replace("ffmpeg", "ffprobe")

def get_video_duration(file_path):
    try:
        cmd = [FFPROBE_PATH, "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", file_path]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, check=True)
        return float(result.stdout.strip())
    except: return 0.0

def generate_cinematic(img_path, output_name, index, duration=6.0):
    """안정적인 시네마틱: Ken Burns 무빙 + 10종 효과"""
    fps = 18
    total_frames = int(fps * duration)
    w, h = 1280, 720

    if not os.path.exists(img_path): return False

    try:
        with PIL.Image.open(img_path) as img_full:
            img_rgb = img_full.convert("RGB")
            
        def make_frame(t):
            prog = t / duration 
            is_even = index % 2 == 0
            
            # [1] Ken Burns 무빙
            if is_even:
                s = 1.3 - (0.2 * prog) # Zoom Out
                move_x, move_y = int(40 * prog), int(20 * prog)
            else:
                s = 1.1 + (0.2 * prog) # Zoom In
                move_x, move_y = int(-40 * prog), int(-20 * prog)

            new_w, new_h = int(w * s), int(h * s)
            resized_img = img_rgb.resize((new_w, new_h), PIL.Image.Resampling.BICUBIC)
            pos = (int(w/2 - new_w/2 + move_x), int(h/2 - new_h/2 + move_y))
            canvas = PIL.Image.new("RGB", (w, h), (0, 0, 0))
            canvas.paste(resized_img, pos)
            frame_array = np.array(canvas, dtype=np.float32)

            # [2] 시네마틱 효과 엔진
            eff_idx = index % 10
            fade = 1.0
            if t < 0.5: fade = t / 0.5
            if t > (duration - 0.5): fade = (duration - t) / 0.5

            if fade > 0:
                if eff_idx == 0: # 횃불 일렁임
                    flicker = (np.sin(t * 12) * np.cos(t * 7)) * 10 * fade
                    frame_array[:, :, 0] += flicker + 5
                elif eff_idx == 1: # 미세 안개
                    frame_array[:, :, 2] += 10 * fade
                elif eff_idx == 3: # 비네트
                    Y, X = np.ogrid[:h, :w]
                    dist = np.sqrt(((X - w/2) / (w/2))**2 + ((Y - h/2) / (h/2))**2)
                    v_mask = np.clip(1.0 - (dist - 0.5) * fade, 0.5, 1.0)
                    for i in range(3): frame_array[:, :, i] *= v_mask
                elif eff_idx == 8: # 색수차 (미세)
                    frame_array[:, 1:, 0] = frame_array[:, :-1, 0]

            # 페이드 인/아웃 트랜지션
            if t < 0.3: frame_array *= (t / 0.3)
            if t > (duration - 0.3): frame_array *= ((duration - t) / 0.3)

            return np.clip(frame_array, 0, 255).astype(np.uint8)

        clip = VideoClip(make_frame, duration=duration)
        clip.write_videofile(output_name, fps=fps, codec="libx264", bitrate="3000k", threads=4, preset="ultrafast", audio=False, logger=None)
        return True
    except Exception as e:
        print(f"⚠️ 에러 ({os.path.basename(img_path)}): {e}")
        return False

def run_batch_video():
    base_downloads = os.path.join(os.path.expanduser("~"), "Downloads")
    subdirs = [os.path.join(base_downloads, d) for d in os.listdir(base_downloads) if os.path.isdir(os.path.join(base_downloads, d)) and d.startswith("무협_생성_")]
    if not subdirs: 
        print("❌ '무협_생성_'으로 시작하는 폴더를 찾을 수 없습니다.")
        return
    
    target_dir = sorted(subdirs)[-1]
    print(f"🎬 대상 폴더: {target_dir}")
    images = sorted([f for f in os.listdir(target_dir) if f.endswith(".png")])
    if not images: 
        print("❌ 폴더 내 이미지가 없습니다.")
        return

    # [추가] visual_settings.json에서 clip_duration 읽기 시도
    clip_duration = 6.0
    settings_candidates = [
        os.path.join(target_dir, "visual_settings.json"),
        os.path.join(BASE_PATH, "visual_settings.json")
    ]
    root_settings = [f for f in os.listdir(BASE_PATH) if f.startswith("visual_settings_") and f.endswith(".json")]
    if root_settings:
        latest_settings = max([os.path.join(BASE_PATH, f) for f in root_settings], key=os.path.getmtime)
        settings_candidates.insert(0, latest_settings)

    for s_path in settings_candidates:
        if os.path.exists(s_path):
            try:
                with open(s_path, "r", encoding="utf-8") as f:
                    s_data = json.load(f)
                    if "clip_duration" in s_data:
                        clip_duration = float(s_data["clip_duration"])
                        break
            except: pass

    # [사용자 요청] 영상 길이 입력 기능 유지
    print(f"\n🎬 시네마틱 영상 길이를 설정합니다. (기본값: {clip_duration}초)")
    user_input = input(f"👉 원하는 길이(초)를 입력하고 Enter를 누르세요 (그냥 Enter 시 {clip_duration}초): ").strip()
    if user_input:
        try:
            clip_duration = float(user_input)
            print(f"✅ {clip_duration}초로 설정을 변경했습니다.")
        except ValueError:
            print(f"⚠️ 올바른 숫자가 아닙니다. 기본값 {clip_duration}초를 사용합니다.")

    to_process = []
    for i, img_name in enumerate(images):
        img_path = os.path.join(target_dir, img_name)
        v_name = img_path.replace(".png", ".mp4")
        # 기존 영상이 없거나, 너무 작거나, 길이가 짧으면(설정값보다 작으면) 다시 생성
        if not os.path.exists(v_name) or os.path.getsize(v_name) < 1000 or get_video_duration(v_name) < (clip_duration - 0.1):
            to_process.append((img_path, v_name, i))

    if not to_process:
        print("✅ 모든 비디오가 설정된 길이로 제작되어 있습니다.")
        return

    print(f"\n🚀 {len(to_process)}개의 영상을 시네마틱 효과로 제작합니다... (길이: {clip_duration}s)")
    with ThreadPoolExecutor(max_workers=4) as executor:
        for img_path, v_name, idx in to_process:
            executor.submit(generate_cinematic, img_path, v_name, idx, duration=clip_duration)
    print("\n✨ 모든 영상 제작 완료!")

if __name__ == "__main__":
    run_batch_video()

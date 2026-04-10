import os
import numpy as np
import PIL.Image
from moviepy import VideoClip
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import sys
import random

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
    import subprocess
    try:
        cmd = [FFPROBE_PATH, "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", file_path]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, check=True)
        return float(result.stdout.strip())
    except: return 0.0

def generate_6s_cinematic(img_path, output_name, index):
    """6초 고퀄리티 시네마틱: 지하 석실 전용 효과 + 다양한 트랜지션"""
    fps = 18
    duration = 6.0
    total_frames = int(fps * duration)
    w, h = 1280, 720

    if not os.path.exists(img_path): return False

    try:
        with PIL.Image.open(img_path) as img_full:
            img_rgb = img_full.convert("RGB")
            
        def make_frame(t):
            frame_idx = int(t * fps)
            if frame_idx >= total_frames: frame_idx = total_frames - 1
            
            prog = t / duration 
            is_even = index % 2 == 0
            
            # [1] Ken Burns 무빙 + [추가] 핸드헬드 흔들림 (Handheld Shake)
            # 인덱스에 따라 일반 무빙 / 미세 흔들림 / 격한 흔들림 교차 적용
            shake_type = index % 4 # 0: 일반, 1: 미세, 2: 일반, 3: 격함
            sx, sy = 0, 0
            if shake_type == 1: # 미세 흔들림 (Handheld)
                sx = int(np.sin(t * 15 + index) * 3)
                sy = int(np.cos(t * 12 + index) * 2)
            elif shake_type == 3: # 격한 흔들림 (Ground Shake / Tension)
                sx = int(np.sin(t * 25 + index) * 8)
                sy = int(np.cos(t * 22 + index) * 6)

            if is_even:
                s = 1.3 - (0.2 * prog) # Zoom Out
                move_x, move_y = int(40 * prog) + sx, int(20 * prog) + sy
            else:
                s = 1.1 + (0.2 * prog) # Zoom In
                move_x, move_y = int(-40 * prog) + sx, int(-20 * prog) + sy

            new_w, new_h = int(w * s), int(h * s)
            resized_img = img_rgb.resize((new_w, new_h), PIL.Image.Resampling.BICUBIC)
            pos = (int(w/2 - new_w/2 + move_x), int(h/2 - new_h/2 + move_y))
            canvas = PIL.Image.new("RGB", (w, h), (0, 0, 0))
            canvas.paste(resized_img, pos)
            frame_array = np.array(canvas, dtype=np.float32)

            # [2] 지하 석실 전용 효과 엔진 (12종 확장)
            eff_idx = index % 12
            full_time_pool = [0, 4, 8, 9, 10, 11]
            
            # [2-0] 상시 레이어: 지하 정취 (Floating Dust)
            for _ in range(12):
                rx = int((index*222 + _*180) % w)
                ry = int((index*111 + t*80 + _*150) % h) # 아주 천천히 상승
                dust_fade = 0.25 * (1.0 - abs(0.5 - (t/6.0))*2) 
                frame_array[max(0,ry-1):min(h,ry+1), max(0,rx-1):min(w,rx+1), :] += 200 * dust_fade
            
            fade = 0.0
            if eff_idx in full_time_pool:
                if t < 0.8: fade = t / 0.8
                elif t > 5.2: fade = (6.0 - t) / 0.8
                else: fade = 1.0
            else:
                if 1.5 <= t <= 4.5:
                    if t < 2.0: fade = (t - 1.5) / 0.5
                    elif t > 4.0: fade = (4.5 - t) / 0.5
                    else: fade = 1.0

            if fade > 0:
                if eff_idx == 0: # 1. 횃불 일렁임
                    flicker = (np.sin(t * 12) * np.cos(t * 7)) * 15 * fade
                    frame_array[:, :, 0] += flicker + 12
                    frame_array[:, :, 1] += flicker
                elif eff_idx == 1: # 2. 신비로운 분위기
                    mist = (np.sin(t * 1.5) + 1.0) * 18 * fade
                    frame_array[:, :, 2] += mist
                elif eff_idx == 2: # 3. 번개/플래시
                    if (int(t*100) % 91 < 4): frame_array += 85 * fade
                elif eff_idx == 3: # 4. 시네마틱 비네트
                    Y, X = np.ogrid[:h, :w]
                    dist_map = np.sqrt(((X - w/2) / (w/2))**2 + ((Y - h/2) / (h/2))**2)
                    v_mask = np.ones((h, w), dtype=np.float32); v_mask[dist_map > 0.5] = 1.0 - (dist_map[dist_map > 0.5] - 0.5) * 2.0 * fade
                    for i in range(3): frame_array[:, :, i] *= np.clip(v_mask, 0.1, 1.0)
                elif eff_idx == 4: # 5. 미세 필름 노이즈
                    frame_array += np.random.normal(0, 10 * fade, (h, w, 3)).astype(np.float32)
                elif eff_idx == 5: # 6. 수직 스크래치
                    if int(t*100) % 12 == 0:
                        sx = int((index*888 + t*5000) % w)
                        frame_array[:, sx:min(w,sx+2), :] += 45 * fade
                elif eff_idx == 7: # 7. 렌즈 글로우
                    frame_array *= (1.0 + 0.12 * fade)
                elif eff_idx == 8: # 8. 색수차
                    frame_array[:, 2:, 0] = frame_array[:, :-2, 0]
                    frame_array[:, :-2, 2] = frame_array[:, 2:, 2]
                elif eff_idx >= 9: # 9. 거친 먼지
                    for _ in range(8):
                        rx = int((index*300 + _*250) % w)
                        ry = int((index*400 + t*300) % h)
                        frame_array[max(0,ry-2):min(h,ry+2), max(0,rx-2):min(w,rx+2), :] += 65 * fade

            # [3] 트랜지션 엔진 (교차 적용)
            transition_type = index % 3
            if t < 0.5: frame_array *= (t / 0.5)
            if t > 5.5:
                out_prog = (t - 5.5) / 0.5
                if transition_type == 0: # 책넘김
                    wipe_x = int(w * out_prog)
                    frame_array[:, w-wipe_x:, :] *= (1.0 - out_prog)
                    edge = w - wipe_x
                    if edge > 0: frame_array[:, max(0, edge-40):edge, :] += (50 * np.sin(out_prog * np.pi))
                elif transition_type == 1: # 페이드 아웃
                    frame_array *= (1.0 - out_prog)
                elif transition_type == 2: # 비네팅 블랙홀
                    Y, X = np.ogrid[:h, :w]
                    dist_map = np.sqrt(((X - w/2) / (w/2))**2 + ((Y - h/2) / (h/2))**2)
                    v_collapse = 1.0 - out_prog
                    frame_array[dist_map > v_collapse] = 0

            return np.clip(frame_array, 0, 255).astype(np.uint8)

        clip = VideoClip(make_frame, duration=duration)
        clip.write_videofile(output_name, fps=fps, codec="libx264", bitrate="3500k", threads=4, preset="ultrafast", audio=False, logger=None)
        return True
    except Exception as e:
        print(f"⚠️ 에러 ({os.path.basename(img_path)}): {e}")
        return False

def run_batch_video():
    base_downloads = os.path.join(os.path.expanduser("~"), "Downloads")
    subdirs = [os.path.join(base_downloads, d) for d in os.listdir(base_downloads) if os.path.isdir(os.path.join(base_downloads, d)) and d.startswith("무협_생성_")]
    if not subdirs: return
    target_dir = sorted(subdirs)[-1]
    print(f"🎬 대상 폴더: {target_dir}")
    images = sorted([f for f in os.listdir(target_dir) if f.endswith(".png")])
    if not images: return
    to_process = []
    for i, img_name in enumerate(images):
        img_path = os.path.join(target_dir, img_name)
        v_name = img_path.replace(".png", ".mp4")
        if not os.path.exists(v_name) or os.path.getsize(v_name) < 1000 or get_video_duration(v_name) < 5.9:
            to_process.append((img_path, v_name, i))
    if not to_process:
        print("✅ 모든 비디오가 최신 효과로 준비되었습니다.")
        return
    print(f"🚀 {len(to_process)}개의 영상을 지하 석실 효과로 업그레이드합니다...")
    with ThreadPoolExecutor(max_workers=3) as executor:
        for img_path, v_name, idx in to_process:
            executor.submit(generate_6s_cinematic, img_path, v_name, idx)
    print("\n✨ 모든 영상 업그레이드 완료!")

if __name__ == "__main__":
    run_batch_video()

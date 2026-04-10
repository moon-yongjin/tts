import os
import numpy as np
import PIL.Image
from moviepy import VideoClip
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import sys
import random
import json
import subprocess

# [윈도우 호환성]
sys.stdout.reconfigure(encoding='utf-8')

# [경로 설정]
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# core_v2 폴더 내부에 있으면 부모 폴더가 ROOT, 아니면 현재 폴더가 ROOT
if os.path.basename(SCRIPT_DIR) == "core_v2":
    ROOT_DIR = os.path.dirname(SCRIPT_DIR)
    CORE_DIR = SCRIPT_DIR
else:
    ROOT_DIR = SCRIPT_DIR
    CORE_DIR = os.path.join(ROOT_DIR, "core_v2")

BASE_PATH = CORE_DIR # 기존 코드 호환

# FFmpeg 경로 설정 (기존 배포된 경로 사용)
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

def generate_advanced_cinematic(img_path, output_name, index, duration=6.0):
    """최종 시네마틱 V2: 미세 핸드헬드 + 부유 먼지 + 올드 필름 + 고전 효과 (15종)"""
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
            
            # [2] Ken Burns 무빙 (지하 석실/무협 느낌의 묵직한 무빙)
            if is_even:
                s = 1.3 - (0.2 * prog) # Zoom Out
                move_x, move_y = int(35 * prog), int(15 * prog)
            else:
                s = 1.1 + (0.2 * prog) # Zoom In
                move_x, move_y = int(-35 * prog), int(-15 * prog)

            new_w, new_h = int(w * s), int(h * s)
            resized_img = img_rgb.resize((new_w, new_h), PIL.Image.Resampling.BICUBIC)
            pos = (int(w/2 - new_w/2 + move_x), int(h/2 - new_h/2 + move_y))
            canvas = PIL.Image.new("RGB", (w, h), (0, 0, 0))
            canvas.paste(resized_img, pos)
            frame_array = np.array(canvas, dtype=np.float32)

            # [3] 부유 먼지 레이어 (Floating Ambient Particles) - 상시 적용
            for _ in range(8):
                rx = int((index*333 + _*200) % w)
                ry = int((index*111 + t*60 + _*180) % h)
                dust_fade = 0.2 * (1.0 - abs(0.5 - (t/duration))*2) 
                frame_array[max(0,ry-1):min(h,ry+1), max(0,rx-1):min(w,rx+1), :] += 150 * dust_fade

            # [4] 고급 효과 엔진 (15종 다채로운 연출)
            eff_idx = index % 15
            fade = 1.0
            # 효과의 페이드 인/아웃 (중간에만 강하게)
            if t < 0.8: fade = t / 0.8
            elif t > (duration - 0.8): fade = (duration - t) / 0.8

            if fade > 0:
                if eff_idx == 0: # 횃불 일렁임 (붉은 계열)
                    flk = (np.sin(t * 14) * 12 + 5) * fade
                    frame_array[:, :, 0] += flk + 5
                elif eff_idx == 1: # 푸른 새벽 안개
                    frame_array[:, :, 2] += 15 * fade
                elif eff_idx == 2: # 번개/플래시 (순간 발광)
                    if (int(t*100) % 80 < 3): frame_array += 70 * fade
                elif eff_idx == 3: # 시네마틱 비네트 (중심부 강조)
                    Y, X = np.ogrid[:h, :w]
                    dist = np.sqrt(((X-w/2)/(w/2))**2 + ((Y-h/2)/(h/2))**2)
                    v_mask = np.clip(1.0 - (dist - 0.4) * 1.5 * fade, 0.4, 1.0)
                    for i in range(3): frame_array[:, :, i] *= v_mask
                elif eff_idx == 4: # 올드 필름: 세피아 믹스
                    sepia = np.array([1.1, 0.9, 0.7]) # 황갈색 톤
                    frame_array *= (1.0 - 0.3 * fade) + (sepia * 0.3 * fade)
                elif eff_idx == 5: # 올드 필름: 미세 노이즈 & 스크래치
                    frame_array += np.random.normal(0, 12 * fade, (h, w, 3))
                    if int(t*100) % 15 == 0:
                        sx_line = random.randint(0, w-1)
                        frame_array[:, sx_line:sx_line+1, :] += 60 * fade
                elif eff_idx == 6: # 올드 필름: 빛 번짐 (Light Leak)
                    leak_x = int((t * 200) % w)
                    frame_array[:, max(0, leak_x-50):min(w, leak_x+50), 0] += 30 * fade # Red leak
                elif eff_idx == 7: # 렌즈 글로우 (전체 밝기 일렁임)
                    frame_array *= (1.0 + 0.15 * np.sin(t*3) * fade)
                elif eff_idx == 8: # 색수차 (RGB Split)
                    frame_array[:, 2:, 0] = frame_array[:, :-2, 0]
                    frame_array[:, :-2, 2] = frame_array[:, 2:, 2]
                elif eff_idx == 9: # 거친 질감 (Grain & Dust)
                    frame_array += np.random.uniform(-15, 15, (h, w, 3)) * fade
                elif eff_idx == 10: # 수직 지터 (Projector Jitter)
                    if int(t*100) % 20 == 0:
                        frame_array = np.roll(frame_array, 2, axis=0)
                elif eff_idx == 11: # 고대 유적 느낌 (Dust + Contrast)
                    frame_array = (frame_array - 128) * (1.1) + 128
                    frame_array[:, :, 1] -= 10 * fade # 옐로우-그린 감소
                elif eff_idx == 12: # 몽환적인 글로우 (Bloom)
                    frame_array[frame_array > 180] += 20 * fade
                elif eff_idx == 13: # 화면 테두리 어둡게 (Edge Darken)
                    frame_array[:50, :, :] *= 0.5 * fade
                    frame_array[-50:, :, :] *= 0.5 * fade
                elif eff_idx == 14: # 흑백 시네마 (B&W/Muted)
                    gray = np.mean(frame_array, axis=2, keepdims=True)
                    frame_array = frame_array * (1.0 - 0.7 * fade) + gray * (0.7 * fade)

            # [5] 트랜지션 (시작 페이드 인 / 끝 페이드 아웃)
            if t < 0.4: frame_array *= (t / 0.4)
            if t > (duration - 0.4): frame_array *= ((duration - t) / 0.4)

            return np.clip(frame_array, 0, 255).astype(np.uint8)

        clip = VideoClip(make_frame, duration=duration)
        clip.write_videofile(output_name, fps=fps, codec="libx264", bitrate="3500k", threads=4, preset="ultrafast", audio=False, logger=None)
        return True
    except Exception as e:
        print(f"⚠️ 에러 ({os.path.basename(img_path)}): {e}")
        return False

def run_batch_video():
    """배치 처리: 설정 읽기 + 사용자 입력 + 병렬 생성"""
    base_downloads = os.path.join(os.path.expanduser("~"), "Downloads")
    subdirs = [os.path.join(base_downloads, d) for d in os.listdir(base_downloads) if os.path.isdir(os.path.join(base_downloads, d)) and d.startswith("무협_로컬생성_")]
    if not subdirs: 
        print("❌ '무협_생성_'으로 시작하는 폴더를 찾을 수 없습니다.")
        return
    
    target_dir = sorted(subdirs)[-1]
    print(f"🎬 대상 폴더: {target_dir}")
    images = sorted([f for f in os.listdir(target_dir) if f.endswith(".png")])
    if not images: 
        print("❌ 폴더 내 이미지가 없습니다.")
        return

    # [1] 설정 파일에서 기본 길이 읽기
    clip_duration = 6.0
    settings_candidates = [
        os.path.join(target_dir, "visual_settings.json"),
        os.path.join(CORE_DIR, "visual_settings.json"),
        os.path.join(ROOT_DIR, "visual_settings.json")
    ]
    
    root_settings = []
    for d in [ROOT_DIR, CORE_DIR]:
        if os.path.exists(d):
            root_settings += [os.path.join(d, f) for f in os.listdir(d) if f.startswith("visual_settings_") and f.endswith(".json")]
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

    # [2] 사용자 요청: 영상 길이 입력 기능
    print(f"\n🎬 시네마틱 V2 영상 길이를 설정합니다. (기본값: {clip_duration}초)")
    user_input = input(f"👉 원하는 길이(초)를 입력하고 Enter를 누르세요 (그냥 Enter 시 {clip_duration}초): ").strip()
    if user_input:
        try:
            clip_duration = float(user_input)
            print(f"✅ {clip_duration}초로 설정을 변경했습니다.")
        except ValueError:
            print(f"⚠️ 올바른 숫자가 아닙니다. 기본값 {clip_duration}초를 사용합니다.")

    # [3] 처리 대상 선별
    to_process = []
    for i, img_name in enumerate(images):
        img_path = os.path.join(target_dir, img_name)
        v_name = img_path.replace(".png", ".mp4")
        # 기존 영상이 없거나, 너무 작거나, 길이가 짧으면(설정값보다 작으면) 다시 생성
        if not os.path.exists(v_name) or os.path.getsize(v_name) < 1000 or get_video_duration(v_name) < (clip_duration - 0.1):
            to_process.append((img_path, v_name, i))

    if not to_process:
        print("✅ 모든 비디오가 고급 시네마틱 효과로 준비되어 있습니다.")
        return

    print(f"\n🚀 {len(to_process)}개의 영상을 고급 시네마틱 효과(V2)로 제작합니다... (길이: {clip_duration}s)")
    start_time = time.time()
    
    # 병렬 처리를 통해 속도 향상 (CPU 코어에 맞춰 조절)
    with ThreadPoolExecutor(max_workers=3) as executor:
        for img_path, v_name, idx in to_process:
            executor.submit(generate_advanced_cinematic, img_path, v_name, idx, duration=clip_duration)
    
    end_time = time.time()
    elapsed = end_time - start_time
    mins = int(elapsed // 60)
    secs = int(elapsed % 60)
    
    print(f"\n✨ 모든 영상(V2) 제작 완료! (소요 시간: {mins}분 {secs}초)")

if __name__ == "__main__":
    run_batch_video()

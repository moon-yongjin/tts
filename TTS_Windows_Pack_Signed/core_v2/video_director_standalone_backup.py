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
import threading
from rembg import new_session, remove

# 현재 스크립트 경로
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
    import subprocess
    try:
        cmd = [FFPROBE_PATH, "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", file_path]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, check=True)
        return float(result.stdout.strip())
    except: return 0.0

# [추가] 리소그래피/배경 제거 세션 관리
thread_local = threading.local()

def get_rembg_session():
    if not hasattr(thread_local, "session"):
        thread_local.session = new_session("u2net")
    return thread_local.session

def detect_character_cut(alpha_np):
    """배경 분리가 깔끔하게 되었는지 확인 (알파 채널 면적 비율 5~80%)"""
    h, w = alpha_np.shape
    alpha_mask = (alpha_np > 10).astype(np.uint8)
    area_ratio = np.sum(alpha_mask) / (h * w)
    
    # 너무 작거나(노이즈), 너무 크면(배경 미분리) 실패로 간주
    if 0.05 < area_ratio < 0.8:
        return True, alpha_mask
    return False, None

def generate_cinematic(img_path, output_name, index, duration=6.0):
    """고퀄리티 시네마틱: 지하 석실 전용 효과 + 다양한 트랜지션 (길이 가변)"""
    fps = 18
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
            if shake_type == 1: # 미세 흔들림 (Handheld) - 강도 낮춤
                sx = int(np.sin(t * 15 + index) * 1.5)
                sy = int(np.cos(t * 12 + index) * 1.2)
            elif shake_type == 3: # 격한 흔들림 (Ground Shake) - 대폭 낮춤 (사용자 어지러움 방지)
                sx = int(np.sin(t * 25 + index) * 3.0)
                sy = int(np.cos(t * 22 + index) * 2.5)

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
                dust_fade = 0.25 * (1.0 - abs(0.5 - (t/duration))*2) 
                frame_array[max(0,ry-1):min(h,ry+1), max(0,rx-1):min(w,rx+1), :] += 200 * dust_fade
            
            fade = 0.0
            if eff_idx in full_time_pool:
                # 시작 15%, 끝 15% 지점에서 페이드
                fade_bound = duration * 0.15
                if t < fade_bound: fade = t / fade_bound
                elif t > (duration - fade_bound): fade = (duration - t) / fade_bound
                else: fade = 1.0
            else:
                # 중간 50% 구간에서만 효과 (25% ~ 75% 지점)
                start_eff = duration * 0.25
                end_eff = duration * 0.75
                if start_eff <= t <= end_eff:
                    m_fade = duration * 0.1 # 효과 내부의 짧은 페이드
                    if t < start_eff + m_fade: fade = (t - start_eff) / m_fade
                    elif t > end_eff - m_fade: fade = (end_eff - t) / m_fade
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
            if t > (duration - 0.5):
                out_prog = (t - (duration - 0.5)) / 0.5
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
    # [추가] visual_settings.json에서 clip_duration 읽기 시도
    clip_duration = 6.0
    settings_candidates = [
        os.path.join(target_dir, "visual_settings.json"),
        os.path.join(BASE_PATH, "visual_settings.json")
    ]
    # 프로젝트별 설정 파일도 검색 (가장 최근 수정된 설정 파일 찾기)
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

    # [수정] 도스 화면에서 직접 입력받기
    print(f"\n🎬 시네마틱 영상 길이를 설정합니다. (기본값: {clip_duration}초)")
    user_input = input(f"👉 원하는 길이(초)를 입력하고 Enter를 누르세요 (그냥 Enter 시 {clip_duration}초): ").strip()
    if user_input:
        try:
            clip_duration = float(user_input)
            print(f"✅ {clip_duration}초로 설정을 변경했습니다.")
        except ValueError:
            print(f"⚠️ 올바른 숫자가 아닙니다. 기본값 {clip_duration}초를 사용합니다.")

    print(f"\n🚀 {len(to_process)}개의 영상을 하이브리드 패럴랙스 효과로 업그레이드합니다... (길이: {clip_duration}s)")
    with ThreadPoolExecutor(max_workers=4) as executor:
        for img_path, v_name, idx in to_process:
            executor.submit(generate_hybrid_video, img_path, v_name, idx, duration=clip_duration)
    print("\n✨ 모든 영상 업그레이드 완료!")

def generate_hybrid_video(img_path, output_name, index, duration=6.0):
    """배경 분리 성공 시 패럴랙스(V5 Pro), 실패 시 기존 시네마틱 효과 적용"""
    try:
        # [1] 배경 분리 시도
        with PIL.Image.open(img_path) as img_full:
            img_rgb = img_full.convert("RGB")
        
        # [중요] 배경 제거 시도
        session = get_rembg_session()
        fg_rgba = remove(img_rgb, session=session)
        fg_np = np.array(fg_rgba)
        
        is_clean, char_mask = detect_character_cut(fg_np[:, :, 3])
        
        if is_clean:
            # [A] 패럴랙스 성공 (V5 Pro 스타일)
            return generate_parallax_video(img_path, output_name, index, duration, fg_rgba)
        else:
            # [B] 패럴랙스 실패 -> 기존 방식으로 대체
            print(f"⏩ {os.path.basename(img_path)}: 배경 분리 불명확, 일반 효과 적용")
            return generate_cinematic(img_path, output_name, index, duration)
            
    except Exception as e:
        print(f"⚠️ 에러 ({os.path.basename(img_path)}): {e}")
        return generate_cinematic(img_path, output_name, index, duration)

def generate_parallax_video(image_path, output_path, index, duration, fg_rgba):
    """프로페셔널 서브틀 패럴랙스 (V5 Pro 스타일)"""
    fps = 18
    total_frames = int(fps * duration)
    
    fg_np = np.array(fg_rgba)
    orig_bgr = cv2_imread_korean(image_path)
    if orig_bgr is None: return False
    
    fg_bgr = cv2.cvtColor(fg_np[:, :, :3], cv2.COLOR_RGB2BGR)
    alpha = fg_np[:, :, 3] / 255.0
    h, w = orig_bgr.shape[:2]
    
    # 배경 인페인팅
    mask = (fg_np[:, :, 3] > 0).astype(np.uint8) * 255
    bg_inpainted = cv2.inpaint(orig_bgr, mask, 3, cv2.INPAINT_TELEA)
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (w, h))

    # 애니메이션 상수 (V5 Pro 기반)
    zoom_amp = 0.025
    tilt_amp = 0.6
    breath_amp = 2
    
    for i in range(total_frames):
        prog = i / total_frames
        t = i / fps
        
        # 1. 배경 (호흡 줌)
        zoom_factor = 1.0 + (zoom_amp * np.sin(np.pi * prog)) 
        bg_resized = cv2.resize(bg_inpainted, None, fx=zoom_factor, fy=zoom_factor, interpolation=cv2.INTER_LINEAR)
        bh, bw = bg_resized.shape[:2]
        bg_final = bg_resized[(bh-h)//2 : (bh-h)//2 + h, (bw-w)//2 : (bw-w)//2 + w]

        # 2. 캐릭터 (미세 까딱임 + 숨쉬기)
        angle = tilt_amp * np.sin(2 * np.pi * 0.15 * t + index) 
        breath_y = breath_amp * np.sin(2 * np.pi * 0.2 * t + index)
        
        pivot = (float(w // 2), float(h))
        rot_mat = cv2.getRotationMatrix2D(pivot, angle, 1.0)
        rot_mat[1, 2] += breath_y
        
        fg_layer = fg_bgr.astype(np.float32)
        alpha_3ch = np.stack([alpha]*3, axis=-1).astype(np.float32)
        
        fg_shifted = cv2.warpAffine(fg_layer, rot_mat, (w, h), borderMode=cv2.BORDER_CONSTANT, borderValue=(0,0,0))
        alpha_shifted = cv2.warpAffine(alpha_3ch, rot_mat, (w, h), borderMode=cv2.BORDER_CONSTANT, borderValue=(0,0,0))
        
        # 3. 합성
        bg_f = bg_final.astype(np.float32)
        combined = bg_f * (1 - alpha_shifted) + fg_shifted * alpha_shifted
        out.write(combined.astype(np.uint8))

    out.release()
    return True

import cv2
def cv2_imread_korean(file_path):
    try:
        img_array = np.fromfile(file_path, np.uint8)
        img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        return img
    except: return None

if __name__ == "__main__":
    run_batch_video()

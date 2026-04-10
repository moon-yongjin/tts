import os
import numpy as np
import PIL.Image
import PIL.ImageEnhance
from moviepy.editor import VideoFileClip
from moviepy.video.VideoClip import VideoClip
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import sys
import unicodedata
import librosa

# [윈도우/맥 호환성]
if sys.platform != "darwin":
    sys.stdout.reconfigure(encoding='utf-8')

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

def ease_in_out_sine(t):
    return -(np.cos(np.pi * t) - 1) / 2

def print_progress_bar(iteration, total, prefix='', suffix='', decimals=1, length=30, fill='█', printEnd="\r"):
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    print(f'\r{prefix} |{bar}| {percent}% {suffix}', end=printEnd)
    if iteration == total: print()

def variable_speed_curve(t, duration):
    """ 속도감 조절 곡선 """
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

def generate_vertical_video_fx(vid_path, output_name, index):
    """
    세로형 비디오(.mp4)에 시네마틱 Zoom/Pan 효과를 적용합니다.
    """
    fps = 24
    w, h = 1080, 1920
    if not os.path.exists(vid_path): return False
    if os.path.exists(output_name): os.remove(output_name)

    pattern_idx = index % 9

    try:
        # 비디오 로드
        v_clip = VideoFileClip(vid_path)
        duration = v_clip.duration

        def get_stage_state(prog):
            s = 1.0
            mx, my = 0, 0
            if pattern_idx == 0: s = 1.0 + (0.3 * prog) # Zoom In
            elif pattern_idx == 1: my = int((-h * 0.1) + (h * 0.2 * prog)) # Tilt Down
            elif pattern_idx == 2: mx = int((-w * 0.1) + (w * 0.2 * prog)) # Pan Right
            elif pattern_idx == 3: # Diagonal
                mx = int((-w * 0.08) + (w * 0.16 * prog))
                my = int((-h * 0.08) + (h * 0.16 * prog))
            elif pattern_idx == 4: # Tilt Up
                my = int((h * 0.1) - (h * 0.2 * prog))
            elif pattern_idx == 5: # Pan Left
                mx = int((w * 0.1) - (w * 0.2 * prog))
            elif pattern_idx == 6: # Zoom Out
                s = 1.3 - (0.3 * prog)
            else:
                mx = int((w * 0.05) - (w * 0.1 * prog))
                my = int((-h * 0.05) + (h * 0.1 * prog))
            return s, mx, my

        s_b, mx_b, my_b = get_stage_state(1.0)

        def make_frame(t):
            # 프레임 가져오기 및 PIL 이미지 변환
            # t가 duration을 초과하지 않도록 보정
            frame_t = min(t, duration - 0.01)
            frame_arr = v_clip.get_frame(frame_t)
            p_img = PIL.Image.fromarray(frame_arr)

            g_prog = variable_speed_curve(t / duration, duration)
            
            if g_prog <= 0.5:
                s1_prog = g_prog / 0.5
                s, move_x, move_y = get_stage_state(s1_prog)
            else:
                s2_prog = (g_prog - 0.5) / 0.5
                s = s_b + (0.4 * s2_prog) 
                target_y_c = h * 0.25
                move_x = int(mx_b * (1.0 - s2_prog)) 
                move_y = int(my_b + (target_y_c - my_b) * s2_prog)

            nw, nh = int(w * s), int(h * s)
            img_resized = p_img.resize((nw, nh), PIL.Image.Resampling.LANCZOS)
            canvas = PIL.Image.new("RGB", (w, h), (0, 0, 0))
            canvas.paste(img_resized, (int(w/2 - nw/2 + move_x), int(h/2 - nh/2 + move_y)))
            
            frame_array = np.array(canvas, dtype=np.uint8)
            
            fade = 1.0
            if t < 0.3: fade = t / 0.3
            elif t > (duration - 0.3): fade = (duration - t) / 0.3
            if fade < 1.0:
                frame_array = (frame_array.astype(np.float32) * fade).astype(np.uint8)

            return frame_array

        new_clip = VideoClip(make_frame, duration=duration)
        if v_clip.audio is not None:
             new_clip = new_clip.set_audio(v_clip.audio)

        new_clip.write_videofile(output_name, fps=fps, codec="libx264", bitrate="5000k", threads=4, preset="ultrafast", audio=True, logger=None)
        v_clip.close()
        new_clip.close()
        return True
    except Exception as e:
        print(f"⚠️ 에러 ({os.path.basename(vid_path)}): {e}")
        return False

def run_batch_vertical_video_fx():
    base_downloads = os.path.join(os.path.expanduser("~"), "Downloads")
    def normalize_name(n):
        return unicodedata.normalize('NFC', n)

    search_prefixes = ("다이어리_", "무협_", "틱톡_", "시나리오_", "막장_")
    
    subdirs = []
    for d in os.listdir(base_downloads):
        full_path = os.path.join(base_downloads, d)
        if not os.path.isdir(full_path): continue
        norm_d = normalize_name(d)
        if any(norm_d.startswith(p) for p in search_prefixes):
            subdirs.append(full_path)
            
    subdirs = sorted(subdirs, key=os.path.getmtime, reverse=True)
    if not subdirs: 
        print("❌ 작업할 폴더(다이어리/무협/틱톡 등)를 찾을 수 없습니다."); return
    target_dir = subdirs[0] 

    # 원본 세로 비디오 탐색
    videos = sorted([f for f in os.listdir(target_dir) if f.endswith(".mp4") and not (f.endswith("_Vertical.mp4") or f.endswith("_Cinematic.mp4"))])
    if not videos: 
        print("❌ 폴더 내 대상 비디오(.mp4) 파일이 없습니다."); return

    print("\n" + "="*50)
    print("🎥 [영상 변환] 프리미엄 세로 시네마틱 (Video Keyframe FX)")
    print("   1080x1920 / 기존 세로 영상에 키프레임 효과 주입")
    print("="*50)
    print(f"📂 대상 폴더: {os.path.basename(target_dir)}")
    
    to_process = []
    for i, vid_name in enumerate(videos):
        vid_path = os.path.join(target_dir, vid_name)
        v_name = vid_path.replace(".mp4", "_Cinematic.mp4")
        to_process.append((vid_path, v_name, i, vid_name))

    print(f"🚀 {len(to_process)}개의 영상에 모션 효과를 작업합니다...")
    
    completed = 0
    total = len(to_process)
    print_progress_bar(0, total, prefix='진행률:', suffix='준비 중...', length=40)
    
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = {executor.submit(generate_vertical_video_fx, v, out, i): n for v, out, i, n in to_process}
        for future in as_completed(futures):
            name = futures[future]
            completed += 1
            res = future.result()
            status = "완료" if res else "실패"
            print_progress_bar(completed, total, prefix='진행률:', suffix=f"{status} ({name[:12]}...)", length=40)
    
    print("\n✨ 모든 영상이 고급 동적 무빙 시네마틱(_Cinematic.mp4)으로 변환되었습니다!")

if __name__ == "__main__":
    run_batch_vertical_video_fx()

import os
import numpy as np
import PIL.Image
from moviepy import VideoClip
import sys
import random
import cv2

# [설정]
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SCRIPT_DIR)
DOWNLOADS_DIR = os.path.join(os.path.expanduser("~"), "Downloads")

FFMPEG_PATH = "/opt/homebrew/bin/ffmpeg"
if not os.path.exists(FFMPEG_PATH): FFMPEG_PATH = "/usr/local/bin/ffmpeg"
os.environ["IMAGEIO_FFMPEG_EXE"] = FFMPEG_PATH

def ease_in_out_sine(t): return -(np.cos(np.pi * t) - 1) / 2

# --- [고급 변속 곡선: Velocity Integration] ---
# 수동으로 속도(미분값)를 지정하여 적분한 뒤 정규화합니다.
# 이를 통해 구간 연결점에서도 속도가 0이 되지 않고 부드럽게 이어집니다.
def variable_speed_curve(t):
    """ 4단계 리듬: 초고속 -> 보통 -> 저속 -> 보통 (C1 Continuity 확보) """
    # 시간 포인트: 0.0, 0.2, 0.5, 0.8, 1.0
    # 속도 비율(Velocity): 시작(4.0), 0.2지점(1.5), 0.5지점(0.8), 0.8지점(0.3), 끝(1.2)
    t_pts = [0.0, 0.2, 0.5, 0.8, 1.0]
    v_pts = [4.5, 1.8, 1.0, 0.2, 1.5] # 속도감 조절
    
    # 1. 속도 곡선의 면적(진행률) 계산 (이산적 적분)
    def get_v(curr_t):
        if curr_t <= t_pts[0]: return v_pts[0]
        if curr_t >= t_pts[-1]: return v_pts[-1]
        for i in range(len(t_pts)-1):
            if t_pts[i] <= curr_t <= t_pts[i+1]:
                # 선형 보간으로 속도 결정
                p = (curr_t - t_pts[i]) / (t_pts[i+1] - t_pts[i])
                return v_pts[i] + (v_pts[i+1] - v_pts[i]) * p
        return v_pts[-1]

    # 2. 적분값 계산 (현재 t까지의 면적)
    # 간단한 정적분: 0부터 t까지 작은 구간으로 나누어 합산 (실시간 계산 효율을 위해 구간별 공식 사용 가능하지만 이해를 위해 합산)
    steps = 40
    dt = t / steps if t > 0 else 0
    area = 0
    for i in range(steps):
        area += get_v(i * dt) * dt
    
    # 3. 전체 면적으로 정규화 (t=1.0일 때의 면적이 1.0이 되도록)
    # 미리 1.0일 때의 면적 계산 (고급: 수식으로 처리)
    total_area = 0
    for i in range(len(t_pts)-1):
        dt_seg = t_pts[i+1] - t_pts[i]
        total_area += (v_pts[i] + v_pts[i+1]) / 2 * dt_seg
    
    return area / total_area

def generate_clean_movement(img_path, output_name, duration=4.0):
    fps = 24
    w, h = 1080, 1920
    
    with PIL.Image.open(img_path) as p_img:
        img_rgb = p_img.convert("RGB")
    
    # 패턴별 끝점(Point B) 및 설정 계산 함수
    pattern_idx = random.randint(0, 8)
    
    def get_stage1_state(prog):
        s = 1.3
        mx, my = 0, 0
        if pattern_idx == 0: s = 1.1 + (0.4 * prog)
        elif pattern_idx == 1: my = int((-h * 0.15) + (h * 0.3 * prog))
        elif pattern_idx == 2: mx = int((-w * 0.15) + (w * 0.3 * prog))
        elif pattern_idx == 3: # Diagonal
            mx = int((-w * 0.1) + (w * 0.2 * prog))
            my = int((-h * 0.1) + (h * 0.2 * prog))
        else: # Random Pan Mix
            mx = int((w * 0.1) - (w * 0.2 * prog))
            my = int((-h * 0.1) + (h * 0.2 * prog))
        return s, mx, my

    # 1단계 끝점(Point B) 미리 확보
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
            
            # 스케일: B의 스케일에서 0.8(추가확대)만큼 더함
            s = s_b + (0.8 * s2_prog) 
            
            # B -> C(얼굴 타겟)로 이어지는 좌표 계산
            target_y_c = h * 0.25 # 상단 25% 지점
            move_x = int(mx_b * (1.0 - s2_prog)) 
            move_y = int(my_b + (target_y_c - my_b) * s2_prog)

        nw, nh = int(w * s), int(h * s)
        img_resized = img_rgb.resize((nw, nh), PIL.Image.Resampling.LANCZOS)
        canvas = PIL.Image.new("RGB", (w, h), (0, 0, 0))
        canvas.paste(img_resized, (int(w/2 - nw/2 + move_x), int(h/2 - nh/2 + move_y)))
        return np.array(canvas)

    clip = VideoClip(make_frame, duration=duration)
    clip.write_videofile(output_name, fps=fps, codec="libx264", bitrate="6000k", audio=False, logger=None)

if __name__ == "__main__":
    # 최신 폴더의 첫 번째 이미지 자동 선택
    subdirs = sorted([os.path.join(DOWNLOADS_DIR, d) for d in os.listdir(DOWNLOADS_DIR) if d.startswith("무협_세로_")])
    if not subdirs: print("❌ 폴더 없음"); sys.exit(1)
    
    target_dir = subdirs[-1]
    images = sorted([f for f in os.listdir(target_dir) if f.endswith(".png")])
    if not images: print("❌ 이미지 없음"); sys.exit(1)
    
    sample_img = os.path.join(target_dir, images[0])
    
    print(f"🎬 [익스트림 속도] 4초 샘플 5개 생성 시작 (이미지: {images[0]})")
    for i in range(1, 6):
        output_video = os.path.join(target_dir, f"SAMPLE_EXTREME_{i}.mp4")
        print(f"   🎥 샘플 {i} 생성 중...")
        generate_clean_movement(sample_img, output_video, duration=4.0)
    
    print(f"✨ 완료! 총 5개의 샘플이 {target_dir} 에 생성되었습니다.")

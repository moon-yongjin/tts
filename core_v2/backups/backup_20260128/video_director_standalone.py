import os
import numpy as np
import PIL.Image
from moviepy import VideoClip
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import sys

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
    """ffprobe를 사용하여 영상의 길이를 초단위로 획득"""
    import subprocess
    try:
        cmd = [
            FFPROBE_PATH, "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", file_path
        ]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, check=True)
        return float(result.stdout.strip())
    except:
        return 0.0

def generate_6s_cinematic(img_path, output_name, index):
    """6초 고퀄리티 시네마틱: 6초 전체 이동 + 중간 3초 랜덤 효과(6종) + 0.5초 책넘김 마무리"""
    fps = 18
    duration = 6.0
    total_frames = int(fps * duration)
    w, h = 1280, 720

    if not os.path.exists(img_path):
        return False

    try:
        with PIL.Image.open(img_path) as img_full:
            img_rgb = img_full.convert("RGB")
            
        def make_frame(t):
            frame_idx = int(t * fps)
            if frame_idx >= total_frames: frame_idx = total_frames - 1
            
            prog = t / duration # 0.0 ~ 1.0 (6초 전체 진행률)
            is_even = index % 2 == 0
            
            # [1] 6초 연속 무빙 (Ken Burns)
            if is_even:
                s = 1.3 - (0.2 * prog) # Zoom Out
                move_x = int(40 * prog)
                move_y = int(20 * prog)
            else:
                s = 1.1 + (0.2 * prog) # Zoom In
                move_x = int(-40 * prog)
                move_y = int(-20 * prog)

            new_w, new_h = int(w * s), int(h * s)
            resized_img = img_rgb.resize((new_w, new_h), PIL.Image.Resampling.BICUBIC)
            pos = (int(w/2 - new_w/2 + move_x), int(h/2 - new_h/2 + move_y))
            canvas = PIL.Image.new("RGB", (w, h), (0, 0, 0))
            canvas.paste(resized_img, pos)
            
            frame_array = np.array(canvas, dtype=np.float32)

            # [2] 고품질 효과 엔진 (10종 교차 및 시간 차등 적용)
            eff_idx = index % 10
            full_time_pool = [6, 7, 8, 9] # 6초 전체: 낙화, 낙엽, 빗줄기, 스크래치
            
            fade = 0.0
            if eff_idx in full_time_pool:
                # 6초 전체형 효과 (시작 0.5s 페이드인, 종료 0.5s 페이드아웃)
                if t < 0.5: fade = t / 0.5
                elif t > 5.5: fade = (6.0 - t) / 0.5
                else: fade = 1.0
            else:
                # 3초 중간형 효과 (1.5s ~ 4.5s)
                if 1.5 <= t <= 4.5:
                    if t < 2.0: fade = (t - 1.5) / 0.5
                    elif t > 4.0: fade = (4.5 - t) / 0.5
                    else: fade = 1.0

            if fade > 0:
                if eff_idx == 0: # 1. 고화질 비네팅 (Round Vignette)
                    Y, X = np.ogrid[:h, :w]
                    dist_map = np.sqrt(((X - w/2) / (w/2))**2 + ((Y - h/2) / (h/2))**2)
                    v_mask = np.ones((h, w), dtype=np.float32)
                    v_mask[dist_map > 0.6] = 1.0 - (dist_map[dist_map > 0.6] - 0.6) * 1.8 * fade
                    v_mask = np.clip(v_mask, 0.2, 1.0)
                    for i in range(3): frame_array[:, :, i] *= v_mask

                elif eff_idx == 1: # 2. 번개/플래시 (Cinematic Lightning)
                    if (int(t*100) % 97 < 5): 
                        frame_array += 70 * fade
                        frame_array[:, :, 2] += 20 * fade 

                elif eff_idx == 2: # 3. 눈/먼지 (Dynamic Snow Particles)
                    for _ in range(25):
                        rx = int((index*200 + _*150) % w)
                        ry = int((index*100 + t*400 + _*220) % h)
                        size = 1 if _ % 3 == 0 else 2
                        color = int(255 * fade)
                        frame_array[max(0,ry-size):min(h,ry+size), max(0,rx-size):min(w,rx+size), :] = color

                elif eff_idx == 3: # 4. 시네마틱 핑크 (Classic Petal)
                    frame_array[:, :, 0] *= (1.0 + 0.15 * fade)
                    frame_array[:, :, 1] *= (1.0 - 0.1 * fade)
                    frame_array[:, :, 2] *= (1.0 - 0.05 * fade)

                elif eff_idx == 4: # 5. 안개/신비로운 분위기 (Fantasy Mist)
                    mist_alpha = (np.sin(t * 2) + 1.0) * 15 * fade
                    frame_array[:, :, 1] += mist_alpha
                    frame_array[:, :, 2] += mist_alpha * 1.5

                elif eff_idx == 5: # 6. 필름 입자 (Fine Film Grain)
                    grain = np.random.normal(0, 10 * fade, (h, w, 3)).astype(np.float32)
                    frame_array = np.clip(frame_array + grain, 0, 255)

                elif eff_idx == 6: # 7. 낙화 (Falling Petals - 🌸)
                    import math
                    for _ in range(20):
                        rx = int((index*333 + _*200 + math.sin(t*2 + _)*50) % w)
                        ry = int((index*150 + t*250 + _*180) % h)
                        size_w, size_h = 4, 6
                        color = np.array([255, 182, 193], dtype=np.float32) * fade
                        frame_array[max(0,ry-size_h):min(h,ry+size_h), max(0,rx-size_w):min(w,rx+size_w), :] = \
                            frame_array[max(0,ry-size_h):min(h,ry+size_h), max(0,rx-size_w):min(w,rx+size_w), :] * (1-0.8*fade) + color * 0.8

                elif eff_idx == 7: # 8. 낙엽 (Autumn Leaves - 🍂)
                    import math
                    for _ in range(15):
                        rx = int((index*444 + _*300 + math.cos(t*1.5 + _)*100) % w)
                        ry = int((index*200 + t*220 + _*150) % h)
                        size = 6
                        color = np.array([180, 90, 20], dtype=np.float32) * fade
                        frame_array[max(0,ry-size):min(h,ry+size), max(0,rx-size):min(w,rx+size), :] = \
                            frame_array[max(0,ry-size):min(h,ry+size), max(0,rx-size):min(w,rx+size), :] * (1-0.7*fade) + color * 0.7

                elif eff_idx == 8: # 9. 빗줄기 (Cinematic Rain - 🌧️)
                    for _ in range(30):
                        rx = int((index*555 + _*120 + t*100) % w)
                        ry = int((index*300 + t*1200 + _*50) % h)
                        frame_array[ry:min(h,ry+15), rx:min(w,rx+1), :] = 200 * fade

                elif eff_idx == 9: # 10. 수직 스크래치 (Old Movie Scratches - 🎞️)
                    if int(t*100) % 15 == 0:
                        for _ in range(3):
                            sx = int((index*777 + t*9999 + _*500) % w)
                            frame_array[:, sx:min(w,sx+1), :] += 30 * fade
                            frame_array[:, sx:min(w,sx+1), :] = np.clip(frame_array[:, sx:min(w,sx+1), :], 0, 255)

            # [3] 마지막 0.5초 책넘김 효과 (5.5s ~ 6.0s)
            if t > 5.5:
                page_prog = (t - 5.5) / 0.5
                wipe_x = int(w * page_prog)
                # 오른쪽에서 왼쪽으로 휘어지듯 넘어가는 느낌 (나선형 덮기)
                frame_array[:, w-wipe_x:, :] *= (1.0 - page_prog)
                if w-wipe_x > 0:
                    # 경계선 하이라이트 (책장 끝 넘김 광택)
                    edge = w - wipe_x
                    frame_array[:, max(0, edge-30):edge, :] += (40 * np.sin(page_prog * np.pi))

            return np.clip(frame_array, 0, 255).astype(np.uint8)

        clip = VideoClip(make_frame, duration=duration)
        clip.write_videofile(
            output_name, fps=fps, codec="libx264", bitrate="3500k",
            threads=4, preset="ultrafast", audio=False, logger=None
        )
        return True
    except Exception as e:
        print(f"⚠️ 에러 ({os.path.basename(img_path)}): {e}")
        return False

def run_batch_video():
    base_downloads = os.path.join(os.path.expanduser("~"), "Downloads")
    subdirs = [os.path.join(base_downloads, d) for d in os.listdir(base_downloads) 
               if os.path.isdir(os.path.join(base_downloads, d)) and d.startswith("무협_생성_")]
    
    if not subdirs:
        print("❌ '무협_생성_'으로 시작하는 폴더를 찾을 수 없습니다.")
        return

    target_dir = sorted(subdirs)[-1]
    print(f"🎬 대상 폴더: {target_dir}")
    
    images = sorted([f for f in os.listdir(target_dir) if f.endswith(".png")])
    if not images:
        print("❌ 이미지가 없습니다.")
        return

    print(f"🔍 폴더 분석: 총 {len(images)}장의 이미지가 있습니다.")
    
    # 생성할 대상 필터링
    to_process = []
    skipped_by_duration = 0
    for i, img_name in enumerate(images):
        img_path = os.path.join(target_dir, img_name)
        video_name = img_path.replace(".png", ".mp4")
        
        should_gen = True
        if os.path.exists(video_name) and os.path.getsize(video_name) > 1000:
            # 기존 영상의 길이가 6초(오차범위 감안 5.9초) 미만이면 재생성
            duration = get_video_duration(video_name)
            if duration >= 5.9:
                should_gen = False
            else:
                skipped_by_duration += 1
        
        if should_gen:
            to_process.append((img_path, video_name, i))

    done_count = len(images) - len(to_process)
    if skipped_by_duration > 0:
        print(f"⚠️ {skipped_by_duration}개의 짧은 영상(5.7초 등)이 발견되어 6초로 재생성합니다.")
    
    if done_count > 0:
        print(f"⏭️ {done_count}개의 영상은 이미 6초로 존재하여 건너뜁니다.")

    if not to_process:
        print("✅ 모든 이미지가 이미 비디오로 변환되어 있습니다!")
        return

    print(f"🚀 누락된 {len(to_process)}개의 비디오 생성을 시작합니다... (병렬 3장씩 처리)")
    
    start_time = time.time()
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = []
        for img_path, video_name, idx in to_process:
            futures.append(executor.submit(generate_6s_cinematic, img_path, video_name, idx))
        
        for f in as_completed(futures):
            f.result()
            print(f"✅ 비디오 생성 완료")

    elapsed = time.time() - start_time
    print(f"\n✨ 모든 영상 생성 완료! (소요 시간: {elapsed/60:.1f}분)")
    
    # [샘플 생성] 낙화 & 낙엽 샘플 추가 생성
    print("🎨 낙화/낙엽 샘플을 추가로 생성합니다...")
    sample_img = os.path.join(target_dir, images[0])
    generate_6s_cinematic(sample_img, os.path.join(target_dir, "000_샘플_낙화.mp4"), 6)
    generate_6s_cinematic(sample_img, os.path.join(target_dir, "000_샘플_낙엽.mp4"), 7)
    print("✅ 샘플 생성 완료 (000_샘플_*.mp4)")

if __name__ == "__main__":
    run_batch_video()

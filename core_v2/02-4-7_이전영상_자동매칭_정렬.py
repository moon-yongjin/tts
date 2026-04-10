#!/Users/a12/miniforge3/bin/python
import os
import cv2
import numpy as np
import shutil

# 📂 경로 설정
IMAGE_DIR = os.path.expanduser("~/Downloads/Grok_Video_Input")  # 원본 이미지 (01.png, 02.png 등)
DOWNLOAD_DIR = os.path.expanduser("~/Downloads")                 # 그록에서 받은 MP4들이 있는 곳
OUTPUT_DIR = os.path.expanduser("~/Downloads/Grok_Sorted")      # 정렬 결과물이 저장될 폴더

def extract_first_frame(video_path):
    """비디오의 첫 프레임을 넘파이 배열로 추출합니다."""
    cap = cv2.VideoCapture(video_path)
    success, frame = cap.read()
    cap.release()
    if success:
        return frame
    return None

def main():
    print("=" * 60)
    print(" 🛠️ [과거 영상 복원] 이미지-비디오 시각적 매칭 정렬기")
    print("=" * 60)

    if not os.path.exists(IMAGE_DIR):
        print(f"❌ 원본 이미지 폴더가 없습니다: {IMAGE_DIR}")
        return

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 1. 원본 이미지 로드
    image_files = [f for f in os.listdir(IMAGE_DIR) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    images_cache = {}
    
    print(f"📁 원본 이미지 읽는 중... (총 {len(image_files)}개)")
    for img_name in image_files:
        path = os.path.join(IMAGE_DIR, img_name)
        img = cv2.imread(path)
        if img is not None:
            # 연산 속도를 위해 소형화
            images_cache[img_name] = cv2.resize(img, (256, 256))

    # 2. 다운로드 폴더 내 그록 비디오 탐색
    video_files = [f for f in os.listdir(DOWNLOAD_DIR) if f.startswith("grok-video-") and f.endswith(".mp4")]
    if not video_files:
        print("👀 다운로드 폴더에 매칭할 'grok-video-...' 파일이 없습니다.")
        return

    print(f"🎬 다운로드 파일 분지 작업 중... (총 {len(video_files)}개)")

    for vid_name in video_files:
        vid_path = os.path.join(DOWNLOAD_DIR, vid_name)
        frame = extract_first_frame(vid_path)
        
        if frame is None:
            continue

        frame_resized = cv2.resize(frame, (256, 256))

        best_match = None
        min_error = float('inf')

        # 모든 원본 이미지와 오차(MSE) 비교
        for img_name, img_data in images_cache.items():
            error = np.mean((frame_resized - img_data) ** 2)
            if error < min_error:
                min_error = error
                best_match = img_name

        # 오차가 기준치 이하일 때만 매칭 (비슷해 보인다면)
        if best_match and min_error < 5000:  # 픽셀 오차 허용치
            image_prefix = os.path.splitext(best_match)[0]
            new_name = f"{image_prefix}_grok_video.mp4"
            dest_path = os.path.join(OUTPUT_DIR, new_name)

            print(f"✅ 매칭 성공: [{vid_name}] ➡️ [{best_match}]")
            shutil.copy(vid_path, dest_path)
        else:
            print(f"❓ 매칭 실패 (오차 과다): {vid_name}")

    print("\n" + "=" * 60)
    print(f"🎉 정리 완료! 결과는 다음 폴더 속에서 확인:")
    print(f"👉 {OUTPUT_DIR}")
    print("=" * 60)

if __name__ == "__main__":
    main()

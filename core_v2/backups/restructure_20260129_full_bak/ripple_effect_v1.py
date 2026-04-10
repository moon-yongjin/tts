import cv2
import numpy as np
import os
import sys

# [윈도우 한글 경로 호환 imread]
def korean_imread(file_path):
    try:
        img_array = np.fromfile(file_path, np.uint8)
        img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        return img
    except Exception as e:
        print(f"❌ 이미지 로드 실패: {e}")
        return None

def create_ripple_effect_v1(image_path, output_path='ripple_effect_v1.mp4', fps=18, duration=5):
    # 1. 이미지 로드 (한글 경로 대응)
    img = korean_imread(image_path)
    if img is None: 
        print(f"❌ 파일을 찾을 수 없습니다: {image_path}")
        return "파일을 찾을 수 없음"
    
    h, w = img.shape[:2]
    total_frames = fps * duration # 18 * 5 = 90 프레임
    
    # MP4V 코덱 설정
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (w, h))

    # 2. 좌표 그리드 생성
    x, y = np.meshgrid(np.arange(w), np.arange(h))

    print(f"🎬 리플 효과 영상 생성 중 (OpenCV)...")
    print(f"📍 소스: {os.path.basename(image_path)}")
    print(f"📍 결과: {output_path}")

    # 3. 프레임 생성 루프
    for i in range(total_frames):
        # 파동 로직
        # y / 120: 파동의 수직 간격
        # i / fps: 시간 흐름에 따른 이동
        # 진폭을 5로 설정
        offset_x = 5 * np.sin(2 * np.pi * y / 120 + 2 * np.pi * i / fps)
        
        map_x = (x + offset_x).astype(np.float32)
        map_y = y.astype(np.float32)

        # 픽셀 재배치
        warped_img = cv2.remap(img, map_x, map_y, cv2.INTER_LINEAR)
        out.write(warped_img)

    out.release()
    print(f"✅ 생성 완료!")
    return f"완료: {output_path}"

if __name__ == "__main__":
    # 다운로드 폴더에서 가장 최근 생성된 이미지 찾기
    d = os.path.join(os.path.expanduser("~"), "Downloads")
    subdirs = [os.path.join(d, o) for o in os.listdir(d) if os.path.isdir(os.path.join(d, o)) and o.startswith("무협_생성_")]
    
    target_img = ""
    
    if subdirs:
        latest_dir = max(subdirs, key=os.path.getmtime)
        images = sorted([f for f in os.listdir(latest_dir) if f.endswith(".png")])
        if images:
            target_img = os.path.join(latest_dir, images[0])
            print(f"📂 최근 생성 폴더 감지: {os.path.basename(latest_dir)}")
    
    # 만약 위에서 못 찾으면 현재 폴더의 input.png 시도
    if not target_img and os.path.exists("input.png"):
        target_img = os.path.abspath("input.png")
    
    if target_img:
        create_ripple_effect_v1(target_img)
    else:
        print("❌ 테스트할 이미지를 찾을 수 없습니다. (Downloads/무협_생성_* 폴더나 현재 폴더의 input.png 확인)")

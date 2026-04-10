import cv2
import numpy as np
import os

def create_ripple_effect_5s(image_path, output_path='ripple_output.mp4', fps=18, duration=5):
    # 1. 이미지 로드
    img = cv2.imread(image_path)
    if img is None: 
        print(f"❌ 파일을 찾을 수 없음: {image_path}")
        return "파일을 찾을 수 없음"
    
    h, w = img.shape[:2]
    total_frames = fps * duration # 18 * 5 = 90 프레임
    
    # MP4V 코덱 설정
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (w, h))

    # 2. 좌표 그리드 생성
    x, y = np.meshgrid(np.arange(w), np.arange(h))

    print(f"🎬 영상 생성 중: {output_path} ({total_frames} 프레임)...")

    # 3. 90프레임 생성 루프
    for i in range(total_frames):
        # i / total_frames를 사용하여 5초 동안 파동이 한 주기를 돌거나 연속되게 설정
        # 5 * np.sin(...) : 진폭을 5로 늘려 조금 더 역동적으로 변경
        offset_x = 5 * np.sin(2 * np.pi * y / 120 + 2 * np.pi * i / fps)
        
        map_x = (x + offset_x).astype(np.float32)
        map_y = y.astype(np.float32)

        # 픽셀 재배치
        warped_img = cv2.remap(img, map_x, map_y, cv2.INTER_LINEAR)
        out.write(warped_img)

    out.release()
    print(f"✅ 완료: {output_path} 저장됨")
    return f"완료: 5초 영상({total_frames}프레임) 저장됨"

if __name__ == "__main__":
    # 최근 생성된 폴더에서 이미지 하나 찾기
    d = os.path.join(os.path.expanduser("~"), "Downloads")
    subdirs = [os.path.join(d, o) for o in os.listdir(d) if os.path.isdir(os.path.join(d, o)) and o.startswith("무협_생성_")]
    if subdirs:
        latest_dir = max(subdirs, key=os.path.getmtime)
        images = [f for f in os.listdir(latest_dir) if f.endswith(".png")]
        if images:
            sample_img = os.path.join(latest_dir, images[0])
            create_ripple_effect_5s(sample_img)
        else:
            print("❌ 폴더 내에 이미지가 없습니다.")
    else:
        print("❌ 무협 생성 폴더를 찾을 수 없습니다.")

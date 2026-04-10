import cv2
import numpy as np
from rembg import remove
from PIL import Image
import io
import os

# OpenCV 얼굴 감지기 초기화 (Haar Cascades)
face_cascade_path = os.path.join(cv2.data.haarcascades, 'haarcascade_frontalface_default.xml')
face_cascade = cv2.CascadeClassifier(face_cascade_path)

def korean_pil_open(file_path):
    try:
        with open(file_path, "rb") as f:
            return Image.open(io.BytesIO(f.read()))
    except Exception as e:
        print(f"❌ 이미지 로드 실패: {e}")
        return None

def create_face_tracked_animation(image_path, output_path='face_tracked_output.mp4', fps=18, duration=5):
    print(f"🎬 얼굴 트래킹 패럴랙스 생성 시작 (OpenCV 모드)...")
    
    # 1. 이미지 로드 및 배경 분리
    input_img = korean_pil_open(image_path)
    if input_img is None: return
    input_img = input_img.convert("RGB")
    
    orig_bgr = cv2.cvtColor(np.array(input_img), cv2.COLOR_RGB2BGR)
    h, w = orig_bgr.shape[:2]

    # 2. 얼굴 감지 (OpenCV Haar Cascades)
    print("⏳ 얼굴 위치 찾는 중 (OpenCV)...")
    gray = cv2.cvtColor(orig_bgr, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.1, 4)
    
    pivot = (float(w // 2), float(h // 2)) # 기본값: 중앙
    if len(faces) > 0:
        # 가장 큰 면적의 얼굴 선택
        (fx, fy, fw, fh) = sorted(faces, key=lambda x: x[2]*x[3], reverse=True)[0]
        # 얼굴 하단(목 부분)을 피벗으로 설정
        px = float(fx + fw // 2)
        py = float(fy + fh)
        pivot = (px, py)
        print(f"✅ 얼굴 감지 성공! 피벗 좌표: {pivot}")
    else:
        print("⚠️ 얼굴을 찾지 못했습니다. 중앙을 기준으로 움직입니다.")

    # 3. 배경 분리 (Rembg)
    print("⏳ AI 배경 분리 중...")
    fg_rgba = remove(input_img)
    fg_np = np.array(fg_rgba)
    fg_bgr = cv2.cvtColor(fg_np[:, :, :3], cv2.COLOR_RGB2BGR)
    alpha = fg_np[:, :, 3] / 255.0
    
    # 4. 배경 인페인팅
    print("⏳ 배경 복원 중...")
    mask = (fg_np[:, :, 3] > 0).astype(np.uint8) * 255
    bg_inpainted = cv2.inpaint(orig_bgr, mask, 3, cv2.INPAINT_TELEA)
    
    # 5. 비디오 설정
    total_frames = fps * duration
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (w, h))

    print(f"🎞️ {total_frames} 프레임 렌더링 중 (목 중심 까딱임)...")

    # 6. 애니메이션 루프
    for i in range(total_frames):
        t = i / fps
        prog = i / total_frames
        
        # 배경 줌 (Oscillating)
        zoom_factor = 1.0 + (0.03 * np.sin(np.pi * prog)) 
        bg_resized = cv2.resize(bg_inpainted, None, fx=zoom_factor, fy=zoom_factor, interpolation=cv2.INTER_LINEAR)
        bh, bw = bg_resized.shape[:2]
        bg_final = bg_resized[(bh-h)//2 : (bh-h)//2 + h, (bw-w)//2 : (bw-w)//2 + w]

        # 캐릭터 까딱임 (얼굴/목 기준 회전)
        angle = 2.0 * np.sin(2 * np.pi * 0.4 * t) 
        rot_mat = cv2.getRotationMatrix2D(pivot, angle, 1.0)
        
        fg_layer = fg_bgr.astype(np.float32)
        alpha_layer = np.stack([alpha]*3, axis=-1).astype(np.float32)
        
        fg_shifted = cv2.warpAffine(fg_layer, rot_mat, (w, h), borderMode=cv2.BORDER_CONSTANT, borderValue=(0,0,0))
        alpha_shifted = cv2.warpAffine(alpha_layer, rot_mat, (w, h), borderMode=cv2.BORDER_CONSTANT, borderValue=(0,0,0))
        
        # 합성
        bg_f = bg_final.astype(np.float32)
        combined = bg_f * (1 - alpha_shifted) + fg_shifted * alpha_shifted
            
        out.write(combined.astype(np.uint8))

    out.release()
    print(f"✅ 완료: {output_path}")

if __name__ == "__main__":
    import glob
    d = os.path.join(os.path.expanduser("~"), "Downloads")
    subdirs = glob.glob(os.path.join(d, "무협_생성_*"))
    if subdirs:
        latest_dir = max(subdirs, key=os.path.getmtime)
        images = sorted(glob.glob(os.path.join(latest_dir, "*.png")))
        if images:
            create_face_tracked_animation(images[0])
        else:
            print("❌ 이미지를 찾을 수 없음")
    else:
        print("❌ 폴더를 찾을 수 없음")

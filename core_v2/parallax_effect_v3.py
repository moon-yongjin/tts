import cv2
import numpy as np
from rembg import remove
from PIL import Image
import io
import os

def korean_pil_open(file_path):
    try:
        with open(file_path, "rb") as f:
            return Image.open(io.BytesIO(f.read()))
    except Exception as e:
        print(f"❌ 이미지 로드 실패: {e}")
        return None

def get_interpolated_value(frame, keyframes, attr):
    """키프레임 사이의 선형 보간값을 계산"""
    # frame은 0 ~ total_frames-1
    # keyframes는 {frame_idx: {attr: value, ...}}
    sorted_frames = sorted(keyframes.keys())
    
    if frame <= sorted_frames[0]:
        return keyframes[sorted_frames[0]][attr]
    if frame >= sorted_frames[-1]:
        return keyframes[sorted_frames[-1]][attr]
    
    for i in range(len(sorted_frames) - 1):
        f1, f2 = sorted_frames[i], sorted_frames[i+1]
        if f1 <= frame <= f2:
            v1, v2 = keyframes[f1][attr], keyframes[f2][attr]
            ratio = (frame - f1) / (f2 - f1)
            return v1 + (v2 - v1) * ratio
    return 0

def create_keyframed_parallax_v3(image_path, output_path='parallax_output_v3.mp4', fps=18, duration=5):
    print(f"🎬 키프레임 배경 패럴랙스(V3) 생성 시작...")
    
    input_img = korean_pil_open(image_path)
    if input_img is None: return
    input_img = input_img.convert("RGB")
    
    print("⏳ AI 배경 분리 중...")
    fg_rgba = remove(input_img)
    fg_np = np.array(fg_rgba)
    
    orig_bgr = cv2.cvtColor(np.array(input_img), cv2.COLOR_RGB2BGR)
    fg_bgr = cv2.cvtColor(fg_np[:, :, :3], cv2.COLOR_RGB2BGR)
    alpha = fg_np[:, :, 3] / 255.0
    h, w = orig_bgr.shape[:2]
    
    print("⏳ 배경 복원 중...")
    mask = (fg_np[:, :, 3] > 0).astype(np.uint8) * 255
    bg_inpainted = cv2.inpaint(orig_bgr, mask, 3, cv2.INPAINT_TELEA)
    
    total_frames = fps * duration
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (w, h))

    # [배경 키프레임 설정]
    # frame_idx: {scale, off_x, off_y}
    # off_x, off_y는 픽셀 단위 이동
    bg_keyframes = {
        0: {"scale": 1.0, "off_x": 0, "off_y": 0},
        int(total_frames * 0.4): {"scale": 1.07, "off_x": 15, "off_y": 8},
        int(total_frames * 0.8): {"scale": 1.03, "off_x": -10, "off_y": -5},
        total_frames - 1: {"scale": 1.0, "off_x": 0, "off_y": 0}
    }

    print(f"🎞️ {total_frames} 프레임 합성 중 (고정급 인물 + 키프레임 배경)...")

    for i in range(total_frames):
        t = i / fps
        
        # 1. 배경 애니메이션 (키프레임 보간)
        scale = get_interpolated_value(i, bg_keyframes, "scale")
        off_x = get_interpolated_value(i, bg_keyframes, "off_x")
        off_y = get_interpolated_value(i, bg_keyframes, "off_y")
        
        bg_resized = cv2.resize(bg_inpainted, None, fx=scale, fy=scale, interpolation=cv2.INTER_LINEAR)
        bh, bw = bg_resized.shape[:2]
        
        # 중앙 기준 크롭 + 키프레임 오프셋 적용
        sx = int((bw - w) // 2 + off_x)
        sy = int((bh - h) // 2 + off_y)
        
        # 경계선 보호 (Canvas가 삐져나가지 않게)
        sx = max(0, min(sx, bw - w))
        sy = max(0, min(sy, bh - h))
        bg_final = bg_resized[sy:sy + h, sx:sx + w]

        # 2. 캐릭터 애니메이션 (극도로 미세한 움직임)
        # 0.5도 각도 + 미세한 숨쉬기 급 상하(3px)
        angle = 0.5 * np.sin(2 * np.pi * 0.2 * t) 
        breath_y = 3 * np.sin(2 * np.pi * 0.25 * t)
        
        pivot = (float(w // 2), float(h))
        rot_mat = cv2.getRotationMatrix2D(pivot, angle, 1.0)
        rot_mat[1, 2] += breath_y # 상하 이동 추가
        
        fg_layer = fg_bgr.astype(np.float32)
        alpha_layer = np.stack([alpha]*3, axis=-1).astype(np.float32)
        
        fg_shifted = cv2.warpAffine(fg_layer, rot_mat, (w, h), borderMode=cv2.BORDER_CONSTANT, borderValue=(0,0,0))
        alpha_shifted = cv2.warpAffine(alpha_layer, rot_mat, (w, h), borderMode=cv2.BORDER_CONSTANT, borderValue=(0,0,0))
        
        # 3. 최종 합성
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
            create_keyframed_parallax_v3(images[0])
        else:
            print("❌ 이미지 없음")
    else:
        print("❌ 폴더 없음")

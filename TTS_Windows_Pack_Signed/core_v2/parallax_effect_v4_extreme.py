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
    sorted_frames = sorted(keyframes.keys())
    if frame <= sorted_frames[0]: return keyframes[sorted_frames[0]][attr]
    if frame >= sorted_frames[-1]: return keyframes[sorted_frames[-1]][attr]
    for i in range(len(sorted_frames) - 1):
        f1, f2 = sorted_frames[i], sorted_frames[i+1]
        if f1 <= frame <= f2:
            v1, v2 = keyframes[f1][attr], keyframes[f2][attr]
            ratio = (frame - f1) / (f2 - f1)
            return v1 + (v2 - v1) * ratio
    return 0

def create_extreme_parallax_v4(image_path, output_path='parallax_output_v4_extreme.mp4', fps=18, duration=5):
    print(f"🎬 익스트림 패럴랙스(V4) 생성 시작...")
    
    input_img = korean_pil_open(image_path)
    if input_img is None: return
    input_img = input_img.convert("RGB")
    
    print("⏳ AI 배경 분리 중 (Rembg)...")
    fg_rgba = remove(input_img)
    fg_np = np.array(fg_rgba)
    
    orig_bgr = cv2.cvtColor(np.array(input_img), cv2.COLOR_RGB2BGR)
    fg_bgr = cv2.cvtColor(fg_np[:, :, :3], cv2.COLOR_RGB2BGR)
    alpha = fg_np[:, :, 3] / 255.0
    h, w = orig_bgr.shape[:2]
    
    print("⏳ 배경 복원 및 인페인팅 중...")
    mask = (fg_np[:, :, 3] > 0).astype(np.uint8) * 255
    bg_inpainted = cv2.inpaint(orig_bgr, mask, 3, cv2.INPAINT_TELEA)
    
    total_frames = fps * duration
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (w, h))

    # [익스트림 키프레임 설정]
    # scale: 1.0 -> 1.25 (25% 확대)
    # off_x: 0 -> 180 (강한 횡이동)
    bg_keyframes = {
        0: {"scale": 1.0, "off_x": 0, "off_y": 0},
        int(total_frames * 0.5): {"scale": 1.15, "off_x": 100, "off_y": 40},
        total_frames - 1: {"scale": 1.30, "off_x": 200, "off_y": 0}
    }

    print(f"🎞️ {total_frames} 프레임 합성 중 (줌 30%, 횡이동 200px)...")

    for i in range(total_frames):
        t = i / fps
        
        # 1. 배경 애니메이션 (익스트림 보간)
        scale = get_interpolated_value(i, bg_keyframes, "scale")
        off_x = get_interpolated_value(i, bg_keyframes, "off_x")
        off_y = get_interpolated_value(i, bg_keyframes, "off_y")
        
        bg_resized = cv2.resize(bg_inpainted, None, fx=scale, fy=scale, interpolation=cv2.INTER_LINEAR)
        bh, bw = bg_resized.shape[:2]
        
        # 중앙 기준 크롭 + 오프셋
        sx = int((bw - w) // 2 + off_x)
        sy = int((bh - h) // 2 + off_y)
        
        # 경계선 보호
        sx = max(0, min(sx, bw - w))
        sy = max(0, min(sy, bh - h))
        bg_final = bg_resized[sy:sy + h, sx:sx + w]

        # 2. 캐릭터 애니메이션 (매우 미세하게 유지하여 배경과 대비)
        # 인물은 가만히 있어야 배경이 움직이는 느낌이 더 잘 남
        angle = 0.3 * np.sin(2 * np.pi * 0.15 * t) 
        
        pivot = (float(w // 2), float(h))
        rot_mat = cv2.getRotationMatrix2D(pivot, angle, 1.0)
        
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
    import sys
    
    d = os.path.join(os.path.expanduser("~"), "Downloads")
    subdirs = glob.glob(os.path.join(d, "무협_생성_*"))
    
    # 특정 이미지가 인자로 들어오면 그것을 사용, 아니면 예측된 전신 이미지 사용
    if len(sys.argv) > 1:
        target_img = sys.argv[1]
    elif subdirs:
        latest_dir = max(subdirs, key=os.path.getmtime)
        # 전신 이미지일 확률이 높은 뒷부분 이미지(숲길 산책 등) 선택
        images = sorted(glob.glob(os.path.join(latest_dir, "*.png")))
        if len(images) > 90:
            target_img = images[91] # 92_스케치.png (가평 숲길 예상)
        elif len(images) > 20:
            target_img = images[20] # 21_스케치.png (차에서 내리는 장면 예상)
        else:
            target_img = images[0]
    else:
        target_img = "input.png"

    if os.path.exists(target_img):
        create_extreme_parallax_v4(target_img)
    else:
        print(f"❌ 이미지를 찾을 수 없음: {target_img}")

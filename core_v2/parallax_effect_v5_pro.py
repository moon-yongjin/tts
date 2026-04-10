import cv2
import numpy as np
from rembg import remove
from PIL import Image
import io
import os
import sys

def korean_pil_open(file_path):
    try:
        with open(file_path, "rb") as f:
            return Image.open(io.BytesIO(f.read()))
    except Exception as e:
        print(f"❌ 이미지 로드 실패: {e}")
        return None

def create_subtle_pro_parallax_v5(image_path, output_path='parallax_output_v5_pro.mp4', fps=18, duration=10):
    print(f"🎬 프로페셔널 서브틀 패럴랙스(V5) 생성 시작...")
    print(f"📍 설정: {duration}초, {fps}fps (장시간용)")
    
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

    print(f"🎞️ {total_frames} 프레임 렌더링 중 (최소 움직임 최적화)...")

    # [V5 프로 설정 - 극도로 절제된 움직임]
    # 배경 확대: 최대 2.5% (매우 은은함)
    # 캐릭터 흔들림: 0.6도 (거의 정지한 듯한 느낌)
    # 캐릭터 숨쉬기: 2px
    
    for i in range(total_frames):
        # 전체 진행률 (0.0 ~ 1.0)
        prog = i / total_frames
        t = i / fps
        
        # 1. 배경 애니메이션 (느린 호흡 줌)
        # 1.0 -> 1.025 -> 1.0 순환
        zoom_factor = 1.0 + (0.025 * np.sin(np.pi * prog)) 
        
        bg_resized = cv2.resize(bg_inpainted, None, fx=zoom_factor, fy=zoom_factor, interpolation=cv2.INTER_LINEAR)
        bh, bw = bg_resized.shape[:2]
        bg_final = bg_resized[(bh-h)//2 : (bh-h)//2 + h, (bw-w)//2 : (bw-w)//2 + w]

        # 2. 캐릭터 애니메이션 (극미세 까딱임 + 숨쉬기)
        # 매우 느린 주파수 (0.15Hz)
        angle = 0.6 * np.sin(2 * np.pi * 0.15 * t) 
        breath_y = 2 * np.sin(2 * np.pi * 0.2 * t)
        
        pivot = (float(w // 2), float(h))
        rot_mat = cv2.getRotationMatrix2D(pivot, angle, 1.0)
        rot_mat[1, 2] += breath_y
        
        fg_layer = fg_bgr.astype(np.float32)
        alpha_layer = np.stack([alpha]*3, axis=-1).astype(np.float32)
        
        fg_shifted = cv2.warpAffine(fg_layer, rot_mat, (w, h), borderMode=cv2.BORDER_CONSTANT, borderValue=(0,0,0))
        alpha_shifted = cv2.warpAffine(alpha_layer, rot_mat, (w, h), borderMode=cv2.BORDER_CONSTANT, borderValue=(0,0,0))
        
        # 3. 합성
        bg_f = bg_final.astype(np.float32)
        combined = bg_f * (1 - alpha_shifted) + fg_shifted * alpha_shifted
            
        out.write(combined.astype(np.uint8))

    out.release()
    print(f"✅ 완료: {output_path}")

if __name__ == "__main__":
    import glob
    
    # 최근 폴더의 096_스케치.png 우선 타겟
    d = os.path.join(os.path.expanduser("~"), "Downloads")
    subdirs = glob.glob(os.path.join(d, "무협_생성_*"))
    
    target_img = ""
    if subdirs:
        latest_dir = max(subdirs, key=os.path.getmtime)
        # 096번 이미지 우선 시도
        found = glob.glob(os.path.join(latest_dir, "096_*.png"))
        if found:
            target_img = found[0]
        else:
            # 없으면 첫 번째 이미지
            found = sorted(glob.glob(os.path.join(latest_dir, "*.png")))
            if found: target_img = found[0]
            
    if not target_img:
        print("❌ 테스트 이미지를 찾을 수 없습니다.")
    else:
        create_subtle_pro_parallax_v5(target_img)

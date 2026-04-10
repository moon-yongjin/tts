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

def create_subtle_parallax_v2(image_path, output_path='parallax_output_v2.mp4', fps=18, duration=5):
    print(f"🎬 은밀한 패럴랙스(V2) 생성 시작...")
    
    # 1. 레이어 분리
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
    
    # 2. 배경 인페인팅
    print("⏳ 배경 복원 중...")
    mask = (fg_np[:, :, 3] > 0).astype(np.uint8) * 255
    bg_inpainted = cv2.inpaint(orig_bgr, mask, 3, cv2.INPAINT_TELEA)
    
    # 3. 비디오 설정
    total_frames = fps * duration
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (w, h))

    print(f"🎞️ {total_frames} 프레임 렌더링 중 (은은한 까딱임 + 루프 줌)...")

    # 4. 애니메이션 루프
    for i in range(total_frames):
        t = i / fps
        prog = i / total_frames
        
        # [배경 애니메이션] 1.0 -> 1.05 -> 1.0 (Sin 곡선으로 왔다갔다)
        # sin(pi * progress)는 0에서 시작해 1(중간)을 찍고 다시 0(끝)으로 옴
        zoom_factor = 1.0 + (0.04 * np.sin(np.pi * prog)) 
        
        bg_resized = cv2.resize(bg_inpainted, None, fx=zoom_factor, fy=zoom_factor, interpolation=cv2.INTER_LINEAR)
        bh, bw = bg_resized.shape[:2]
        bg_final = bg_resized[(bh-h)//2 : (bh-h)//2 + h, (bw-w)//2 : (bw-w)//2 + w]

        # [캐릭터 애니메이션] 은은한 각도 까딱임 (Sway/Tilt)
        # 1.5도 내외로 아주 미세하게 회전
        angle = 1.6 * np.sin(2 * np.pi * 0.3 * t) 
        
        # 회전 중심점: 캐릭터의 하단 중앙 (발/바닥 기준)
        pivot = (w // 2, h)
        rot_mat = cv2.getRotationMatrix2D(pivot, angle, 1.0)
        
        # 레이어 회전
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
    d = os.path.join(os.path.expanduser("~"), "Downloads")
    subdirs = [os.path.join(d, o) for o in os.listdir(d) if os.path.isdir(os.path.join(d, o)) and o.startswith("무협_생성_")]
    if subdirs:
        latest_dir = max(subdirs, key=os.path.getmtime)
        images = sorted([f for f in os.listdir(latest_dir) if f.endswith(".png")])
        if images:
            create_subtle_parallax_v2(os.path.join(latest_dir, images[0]))
        else:
            print("❌ 이미지를 찾을 수 없음")
    else:
        print("❌ 폴더를 찾을 수 없음")

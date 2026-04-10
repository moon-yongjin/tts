import cv2
import numpy as np
from rembg import remove
from PIL import Image
import io
import os
import time

# [윈도우 한글 경로 호환 PIL 오픈]
def korean_pil_open(file_path):
    try:
        with open(file_path, "rb") as f:
            return Image.open(io.BytesIO(f.read()))
    except Exception as e:
        print(f"❌ 이미지 로드 실패: {e}")
        return None

def create_parallax_animation(image_path, output_path='parallax_output.mp4', fps=18, duration=5):
    print(f"🎬 패럴랙스 애니메이션 생성 시작...")
    print(f"📍 소스: {os.path.basename(image_path)}")
    
    # 1. 레이어 분리 (Rembg 사용)
    print("⏳ 배경 제거 중 (Rembg)... 처음 실행 시 모델 다운로드로 시간이 걸릴 수 있습니다.")
    input_img = korean_pil_open(image_path)
    if input_img is None: return "파일을 찾을 수 없음"
    input_img = input_img.convert("RGB")
    
    # 배경 제거된 캐릭터 레이어 (RGBA)
    fg_rgba = remove(input_img)
    fg_np = np.array(fg_rgba)
    
    # 원본 및 배경 준비
    orig_np = np.array(input_img)
    # PIL(RGB) -> OpenCV(BGR)
    orig_bgr = cv2.cvtColor(orig_np, cv2.COLOR_RGB2BGR)
    fg_bgr = cv2.cvtColor(fg_np[:, :, :3], cv2.COLOR_RGB2BGR)
    alpha = fg_np[:, :, 3] / 255.0
    
    h, w = orig_bgr.shape[:2]
    
    # 2. 배경 인페인팅 (캐릭터 자리를 주변색으로 대충 메움)
    print("⏳ 배경 빈자리 메우기 (Inpainting)...")
    mask = (fg_np[:, :, 3] > 0).astype(np.uint8) * 255
    bg_inpainted = cv2.inpaint(orig_bgr, mask, 3, cv2.INPAINT_TELEA)
    
    # 3. 비디오 설정
    total_frames = fps * duration
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (w, h))

    print(f"🎞️ {total_frames} 프레임 합성 중...")

    # 4. 애니메이션 루프
    for i in range(total_frames):
        t = i / fps  # 현재 시간(초)
        
        # [배경 애니메이션] 서서히 확대 (Zoom)
        zoom_factor = 1 + (0.05 * (i / total_frames)) # 5% 확대
        bg_resized = cv2.resize(bg_inpainted, None, fx=zoom_factor, fy=zoom_factor, interpolation=cv2.INTER_LINEAR)
        
        # 중앙 크롭하여 원래 사이즈로 복구
        bh, bw = bg_resized.shape[:2]
        start_y = (bh - h) // 2
        start_x = (bw - w) // 2
        bg_final = bg_resized[start_y:start_y + h, start_x:start_x + w]

        # [캐릭터 애니메이션] 상하 부드러운 움직임 (Sin 함수)
        move_y = int(12 * np.sin(2 * np.pi * 0.4 * t)) # 0.4Hz 속도로 12px 진폭
        
        # 합성을 위한 빈 캔버스
        combined = bg_final.copy().astype(np.float32)
        
        # 캐릭터 레이어 합성
        # move_y만큼 이미지를 시프트
        # 단순화를 위해 전체 레이어를 시프트한 뒤 알파 합성
        fg_layer = fg_bgr.astype(np.float32)
        alpha_layer = np.stack([alpha]*3, axis=-1).astype(np.float32)
        
        # 캐릭터 이동 행렬
        M = np.float32([[1, 0, 0], [0, 1, move_y]])
        fg_shifted = cv2.warpAffine(fg_layer, M, (w, h), borderMode=cv2.BORDER_CONSTANT, borderValue=(0,0,0))
        alpha_shifted = cv2.warpAffine(alpha_layer, M, (w, h), borderMode=cv2.BORDER_CONSTANT, borderValue=(0,0,0))
        
        # 최종 합성: 배경 * (1-알파) + 캐릭터 * 알파
        combined = combined * (1 - alpha_shifted) + fg_shifted * alpha_shifted
            
        out.write(combined.astype(np.uint8))

    out.release()
    print(f"✅ 완료: {output_path} 저장됨")
    return f"작업 완료: {output_path}"

if __name__ == "__main__":
    # 최근 생성된 폴더에서 이미지 하나 찾기
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
        create_parallax_animation(target_img)
    else:
        print("❌ 테스트할 이미지를 찾을 수 없습니다.")

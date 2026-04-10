import os
import cv2
import numpy as np
from pathlib import Path

def remove_watermark_perfect(img_path):
    if not os.path.exists(img_path): return False
    
    try:
        # [1] 한글 경로 안전하게 읽기
        img_array = np.fromfile(img_path, np.uint8)
        img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        if img is None: return False
        
        h, w = img.shape[:2]
        mask = np.zeros((h, w), dtype=np.uint8)
        
        # [2] 타격 좌표 설정 (우측 하단 15% 지점)
        roi_size = int(min(h, w) * 0.15) 
        y_start, x_start = h - roi_size, w - roi_size
        roi = img[y_start:h, x_start:w]
        
        # [3] 흰색 별표 정밀 추출 (HSV 채도/밝기 기반)
        hsv_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        lower_white = np.array([0, 0, 180]) 
        upper_white = np.array([180, 40, 255])
        thresh = cv2.inRange(hsv_roi, lower_white, upper_white)
        
        # 마스킹 확장
        kernel = np.ones((5,5), np.uint8)
        thresh = cv2.dilate(thresh, kernel, iterations=2)
        
        # 자동 감지 실패 시 강제 영역
        if cv2.countNonZero(thresh) < 5:
            cv2.rectangle(thresh, (roi_size-90, roi_size-90), (roi_size-10, roi_size-10), 255, -1)
        
        mask[y_start:h, x_start:w] = thresh
        
        # [4] Inpainting
        result = cv2.inpaint(img, mask, 5, cv2.INPAINT_TELEA)
        
        # [5] 저장 로직 (원본에 바로 덮어쓰기 위해 원본 경로 사용)
        _, ext = os.path.splitext(img_path)
        success, encoded = cv2.imencode(ext, result)
        if success:
            with open(img_path, 'wb') as f:
                encoded.tofile(f)
            return True
        return False
    except Exception as e:
        print(f"❌ 에러: {e}")
        return False

def run_batch():
    target_dir = os.path.join(os.path.expanduser("~"), "Downloads")
    
    # 이미 처리된 파일은 제외 (마스크 파일 등이 있을 수 있으니)
    images = [f for f in os.listdir(target_dir) 
              if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')) 
              and '_mask' not in f and '_debug_mask' not in f]
    
    if not images:
        print("🔍 처리할 이미지가 없습니다.")
        return

    print(f"🚀 다운로드 폴더 내 {len(images)}개 이미지 작업 시작...")
    count = 0
    for name in images:
        path = os.path.join(target_dir, name)
        if remove_watermark_perfect(path):
            count += 1
            print(f"✅ 지움 완료: {name}")
            
    print(f"✨ 총 {count}개 작업 완료!")

if __name__ == "__main__":
    run_batch()
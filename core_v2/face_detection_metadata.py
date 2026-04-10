
import cv2
import json
import os
import glob
from pathlib import Path

# 설정
PROJ_ROOT = Path("/Users/a12/projects/tts")
IMAGE_DIR = PROJ_ROOT / "remotion-hello-world" / "public" / "images"
OUTPUT_JSON = PROJ_ROOT / "remotion-hello-world" / "public" / "face_metadata.json"

# OpenCV 얼굴 감지 모델 (Haar Cascade)
# 시스템에 설치된 cv2 경로에서 찾거나, 없으면 기본 경로 사용
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

def detect_face(image_path):
    try:
        img = cv2.imread(str(image_path))
        if img is None:
            return None
        
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.1, 4)
        
        height, width, _ = img.shape
        
        if len(faces) > 0:
            # 가장 큰 얼굴 선택
            largest_face = max(faces, key=lambda r: r[2] * r[3])
            x, y, w, h = largest_face
            
            # 얼굴 중심 좌표 (0.0 ~ 1.0 정규화)
            center_x = (x + w / 2) / width
            center_y = (y + h / 2) / height
            
            # 너무 가장자리인지 확인 (가장자리면 보정)
            center_x = max(0.2, min(0.8, center_x))
            center_y = max(0.2, min(0.8, center_y)) # 얼굴은 보통 위에 있으므로 아래쪽 제한은 덜 해도 됨
            
            return {"x": center_x, "y": center_y, "has_face": True}
        
        else:
            # 얼굴 없으면 기본값 (중앙 위쪽)
            return {"x": 0.5, "y": 0.35, "has_face": False}
            
    except Exception as e:
        print(f"Error processing {image_path}: {e}")
        return {"x": 0.5, "y": 0.5, "has_face": False}

def main():
    print("🔍 이미지 얼굴 분석 시작...")
    
    metadata = {}
    
    # 드라마 이미지 파일 패턴
    image_pattern = str(IMAGE_DIR / "폐차장의 진실_ 배은망덕한 자식들의 몰락_장면_*.png")
    image_files = sorted(glob.glob(image_pattern))
    
    print(f"📂 총 {len(image_files)}개의 이미지 발견")
    
    for img_path in image_files:
        filename = os.path.basename(img_path)
        print(f"   - 분석 중: {filename}", end="\r")
        result = detect_face(img_path)
        metadata[filename] = result
        
    print(f"\n✨ 분석 완료! ({len(metadata)}개 처리됨)")
    
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
        
    print(f"💾 메타데이터 저장됨: {OUTPUT_JSON}")

if __name__ == "__main__":
    main()

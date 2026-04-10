import os
import shutil
import re

# 📂 대상 폴더 및 목적지 설정
SOURCE_DIR = "/Users/a12/Downloads/무협_생성"
TARGET_DIR = os.path.join(SOURCE_DIR, "홀수_이미지")

def sort_odd_files():
    if not os.path.exists(SOURCE_DIR):
        print(f"⚠️ 에러: 대상 폴더({SOURCE_DIR})가 존재하지 않습니다.")
        return

    # 1. 목적지 폴더 생성
    if not os.path.exists(TARGET_DIR):
        os.makedirs(TARGET_DIR)
        print(f"📂 목적지 폴더 생성 완료: {TARGET_DIR}")

    # 2단계: 폴더 내 파일 리스트업
    files = [f for f in os.listdir(SOURCE_DIR) if f.lower().endswith('.png') and os.path.isfile(os.path.join(SOURCE_DIR, f))]
    
    if not files:
        print("💡 폴더 내에 PNG 파일이 없습니다.")
        return

    print(f"🔍 총 {len(files)}개의 PNG 파일을 검사합니다...")
    moved_count = 0

    # 3단계: 파일명에서 숫자 추출 및 홀수 판별
    for filename in sorted(files):
        # 파일명에서 숫자 부분 추출 (예: scene_81.png -> 81)
        numbers = re.findall(r"(\d+)", filename)
        
        if numbers:
            # 보수적으로 '가장 파일명 끝에 가까운 숫자'를 인덱스로 인식
            number = int(numbers[-1])
            
            if number % 2 != 0:  # 홀수
                src_path = os.path.join(SOURCE_DIR, filename)
                dst_path = os.path.join(TARGET_DIR, filename)
                
                try:
                    shutil.move(src_path, dst_path)
                    print(f"✅ 이동 완료: {filename} ➡️ 홀수_이미지/")
                    moved_count += 1
                except Exception as e:
                    print(f"❌ 이동 실패({filename}): {e}")

    print("\n" + "="*50)
    print(f"🎉 정리 완료! 총 {moved_count}개의 홀수 번호 파일을 이동했습니다.")
    print("="*50)

if __name__ == "__main__":
    sort_odd_files()

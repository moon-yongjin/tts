import os
import shutil
import re
from pathlib import Path

def pick_grok_images():
    print("\n==========================================")
    print("🎬 [그록(Grok) 동영상 변환용 이미지 추출기]")
    print("==========================================")

    downloads_dir = Path.home() / "Downloads"
    target_dir = None

    # 1. 최신 AutoDirector_ 폴더 탐색
    print(f"📂 다운로드 폴더 탐색 중: {downloads_dir}")
    if downloads_dir.exists():
        candidates = [d for d in downloads_dir.iterdir() if d.is_dir() and d.name.startswith("AutoDirector_")]
        if candidates:
            # 수정 시간 기준 가장 최근 폴더 선택
            target_dir = max(candidates, key=os.path.getmtime)

    if not target_dir:
        print("⚠️ 'AutoDirector_' 로 시작하는 폴더를 찾지 못했습니다.")
        # 대표적인 백업 경로 탐색
        alt_dirs = [
            Path("/Users/a12/projects/tts/무협생성"),
            Path.home() / "Desktop" / "무협생성"
        ]
        for ad in alt_dirs:
            if ad.exists():
                target_dir = ad
                break

    if not target_dir:
        print("❌ 대상 이미지 폴더를 찾을 수 없습니다.")
        print("💡 폴더가 있는 정확한 경로를 알려주시면 바로 적용해 드립니다!")
        return

    print(f"✅ 대상 폴더 탐지 완료: {target_dir.name}")

    # 2. 이동할 새 폴더 생성
    output_dir = target_dir / "Grok_동영상_생성용"
    os.makedirs(output_dir, exist_ok=True)

    # 3. 폴더 내 모든 .png 파일 수집 및 정렬
    # 파일명 숫자 기준 정렬 (예: 01_Auto_Director_01.png ➡️ 1번)
    def extract_number(path):
        numbers = re.findall(r'\d+', path.name)
        return int(numbers[0]) if numbers else 0

    png_files = sorted(list(target_dir.glob("*.png")), key=extract_number)
    total_files = len(png_files)
    
    print(f"📄 총 {total_files}개의 PNG 파일을 발견했습니다.")

    if total_files == 0:
        print("❌ 폴더 내에 PNG 파일이 없습니다.")
        return

    copy_count = 0
    
    # 3분의 1 추출 로직 (매 3번째 파일 선택)
    for i, file_path in enumerate(png_files):
        if i % 3 == 0:  # 0, 3, 6, 9 ... (인덱스)
            filename = file_path.name
            dest_path = output_dir / filename
            
            # 원본 유지하기 위해 Copy 사용 (유저가 확인 후 사용)
            shutil.copy(str(file_path), str(dest_path))
            print(f"📦 복사 완료: {filename} ➡️ Grok_동영상_생성용/")
            copy_count += 1

    print("\n==========================================")
    print(f"🎉 추출 완료! 총 {copy_count}장의 이미지를 엄선했습니다.")
    print(f"📂 저장 경로: {output_dir}")
    print("==========================================")

if __name__ == "__main__":
    pick_grok_images()

import os
import shutil
import re
from pathlib import Path

def move_odd_images():
    print("\n==========================================")
    print("🖼️  [홀수 번호 이미지 추출 및 이동 렌더러]")
    print("==========================================")

    # 1. 대상 폴더 설정 (Desktop 에 있는 무협생성 폴더 추정)
    target_dir = Path.home() / "Desktop" / "무협생성"
    
    if not target_dir.exists():
        # 만약 바탕화면에 없으면, 유저 홈 디렉토리 전체에서 검색 시도
        print(f"⚠️ {target_dir} 폴더가 없습니다. 다른 경로를 탐색합니다.")
        # 대표적인 백업 경로 탐색
        alt_dirs = [
            Path.home() / "Downloads" / "무협생성",
            Path("/Users/a12/projects/tts/무협생성")
        ]
        for ad in alt_dirs:
            if ad.exists():
                target_dir = ad
                break

    if not target_dir.exists():
        print("❌ '무협생성' 폴더를 찾을 수 없습니다.")
        print("💡 폴더가 있는 정확한 경로를 알려주시면 바로 적용해 드립니다!")
        return

    print(f"✅ 대상 폴더 탐지 완료: {target_dir}")

    # 2. 이동할 새 폴더 생성
    output_dir = target_dir / "홀수_이미지_모음"
    os.makedirs(output_dir, exist_ok=True)

    # 3. 폴더 내 모든 .png 파일 수집
    png_files = list(target_dir.glob("*.png"))
    print(f"📄 총 {len(png_files)}개의 PNG 파일을 발견했습니다.")

    move_count = 0

    for file_path in png_files:
        filename = file_path.name
        # 파일명에서 숫자 추출 (예: 001.png ➡️ 1, image3.png ➡️ 3)
        numbers = re.findall(r'\d+', filename)
        
        if numbers:
            # 가장 마지막에 나타난 숫자를 기준 (보통 파일 번호)
            num = int(numbers[-1])
            
            # 홀수인지 판별
            if num % 2 != 0:
                dest_path = output_dir / filename
                shutil.move(str(file_path), str(dest_path))
                print(f"📦 이동 완료 [홀수]: {filename} ➡️ {output_dir.name}/")
                move_count += 1

    print("\n==========================================")
    print(f"🎉 이동 완료! 총 {move_count}개의 홀수 파일을 치웠습니다.")
    print(f"📂 저장 경로: {output_dir}")
    print("==========================================")

if __name__ == "__main__":
    move_odd_images()

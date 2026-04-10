import os
import re
import tkinter as tk
from tkinter import filedialog
from pathlib import Path

def reverse_numbering():
    # 윈도우 창 숨기기 및 폴더 선택 창 띄우기
    root = tk.Tk()
    root.withdraw()
    root.call('wm', 'attributes', '.', '-topmost', True) # 창을 맨 앞으로
    
    print("📂 번호를 뒤집을 이미지 폴더를 선택해 주세요...")
    target_dir = filedialog.askdirectory(title="이미지 파일이 들어있는 폴더를 선택하세요")
    
    if not target_dir:
        print("❌ 폴더 선택이 취소되었습니다.")
        return

    path = Path(target_dir)
    # 숫자(001 등)가 포함된 이미지 파일들만 골라내기 (png, jpg, jpeg, webp)
    valid_exts = {'.png', '.jpg', '.jpeg', '.webp'}
    files = [f for f in os.listdir(path) if re.search(r'\d+', f) and Path(f).suffix.lower() in valid_exts]
    files.sort() # 기본 오름차순 (001, 002, 003...)
    
    count = len(files)
    if count == 0:
        print(f"⚠️ {path.name} 폴더에 숫자가 포함된 이미지 파일이 없습니다.")
        return

    print(f"📦 [ {path.name} ] 폴더 내 {count}개의 파일을 역순으로 재정렬합니다...")

    # 1. 파일 이름 충돌 방지를 위해 임시 이름으로 우선 변경
    temp_files = []
    for i, filename in enumerate(files):
        old_path = path / filename
        temp_name = f"temp_rev_{i}_{filename}"
        temp_path = path / temp_name
        os.rename(old_path, temp_path)
        temp_files.append(temp_name)

    # 2. 역순 번호 적용 (끝번 -> 1번으로 덮어쓰기)
    for i, temp_name in enumerate(temp_files):
        old_path = path / temp_name
        
        # 새 번호 계산 (총 개수 - 현재 인덱스)
        new_num = count - i
        
        # 임시 이름 제거 후 숫자만 새 번호(048, 047...)로 교체
        clean_name = temp_name.replace(f"temp_rev_{i}_", "")
        new_name = re.sub(r'\d+', f"{new_num:03d}", clean_name)
        
        new_path = path / new_name
        
        # 중복 방지 (이미 처리된 파일과 이름이 같을 경우 등)
        if new_path.exists():
            os.remove(new_path)
            
        os.rename(old_path, new_path)
        print(f"✅ {new_num:03d}번 적용: {new_name}")

    print(f"\n✨ {count}개 파일의 번호 뒤집기 완료!")

if __name__ == "__main__":
    reverse_numbering()

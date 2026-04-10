import os
import shutil
import sys
import re
import tkinter as tk
from tkinter import filedialog, messagebox

def process_files(src=None, dst=None, silent=False):
    if not src:
        src = filedialog.askdirectory(title="NB2 다운로드 폴더 선택")
    if not src: return

    if not dst:
        dst = filedialog.askdirectory(title="정리된 파일을 저장할 폴더 선택")
    if not dst: return

    # 파일 목록 가져오기
    # 패턴: [숫자]_[이름]...
    # 오늘 생성된 파일만 필터링 (Mar 29 2026)
    import datetime
    today = datetime.date.today()
    
    scene_groups = {}
    
    for f in os.listdir(src):
        full_path = os.path.join(src, f)
        if not os.path.isfile(full_path) or f.startswith('.'):
            continue
            
        mtime = os.path.getmtime(full_path)
        mdate = datetime.date.fromtimestamp(mtime)
        
        # 오늘 날짜만 처리
        if mdate != today:
            continue
            
        # 파일명에서 첫 번째 숫자 추출 (01, 1, 001 등)
        match = re.match(r'^(\d+)', f)
        if match:
            scene_num = int(match.group(1))
            mtime = os.path.getmtime(full_path)
            
            if scene_num not in scene_groups or mtime > scene_groups[scene_num][0]:
                scene_groups[scene_num] = (mtime, f)
    
    if not scene_groups:
        # 숫자로 시작하는 파일이 없으면 시간순으로 전체 처리 (기본 모드)
        all_files = []
        for f in os.listdir(src):
            full_path = os.path.join(src, f)
            if os.path.isfile(full_path) and not f.startswith('.'):
                if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                    all_files.append((os.path.getmtime(full_path), f))
        all_files.sort(key=lambda x: x[0])
        
        if not all_files:
            if not silent: messagebox.showwarning("경고", "처리할 이미지 파일이 없습니다.")
            return
            
        for i, (mtime, f) in enumerate(all_files, 1):
            scene_groups[i] = (mtime, f)

    os.makedirs(dst, exist_ok=True)

    count = 0
    # 씬 번호 1~100까지 확장 (60개 이상 대응)
    target_range = range(1, 101)
    for scene_num in sorted(scene_groups.keys()):
        if scene_num not in target_range:
            continue
            
        mtime, filename = scene_groups[scene_num]
        _, ext = os.path.splitext(filename)
        # 001.png 형식으로 저장
        new_name = f"{scene_num:03d}{ext}"
        shutil.copy2(os.path.join(src, filename), os.path.join(dst, new_name))
        count += 1

    msg = f"스마트 정리가 완료되었습니다!\n- 총 {count}개 장면 추출\n- 중복 파일 중 최신 버전 선택됨\n- 저장 위치: {dst}"
    if not silent:
        messagebox.showinfo("완료", msg)
    else:
        print(msg)

def run_gui():
    root = tk.Tk()
    root.title("NB2 스마트 넘버링 정리")
    root.geometry("350x180")
    root.configure(bg="#1a1a2e")

    label = tk.Label(root, text="🍌 NB2 스마트 정리", font=("Segoe UI", 14, "bold"), fg="#ffd700", bg="#1a1a2e")
    label.pack(pady=20)

    btn = tk.Button(root, text="폴더 선택 & 작업 시작", font=("Segoe UI", 12), bg="#4caf50", fg="white", command=lambda: process_files())
    btn.pack(pady=10)

    root.mainloop()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        src_dir = sys.argv[1]
        dst_dir = sys.argv[2] if len(sys.argv) > 2 else os.path.join(src_dir, "smart_numbered")
        process_files(src_dir, dst_dir, silent=True)
    else:
        run_gui()

import os
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox
from collections import defaultdict

def process_files():
    # 원본 폴더 선택
    src = filedialog.askdirectory(title="원본 폴더 선택")
    if not src:
        return

    # 저장 폴더 선택
    dst = filedialog.askdirectory(title="저장 폴더 선택")
    if not dst:
        return

    # 파일 그룹핑 (파일명 기준)
    groups = defaultdict(list)
    for f in os.listdir(src):
        if not os.path.isfile(os.path.join(src, f)):
            continue
        name, ext = os.path.splitext(f)
        # _1, _2 등 제거해서 기본 이름 추출
        if '_' in name:
            parts = name.rsplit('_', 1)
            if parts[1].isdigit():
                base = parts[0]
                num = int(parts[1])
                groups[base].append((num, f, ext))
                continue
        # _숫자가 아닌 파일은 그대로
        groups[name].append((0, f, ext))

    count = 0
    for base, files in groups.items():
        files.sort(key=lambda x: x[0])

        if len(files) == 1:
            # 한 개만 있으면 → 파일명.확장자
            _, orig, ext = files[0]
            new_name = f"{base}{ext}"
            shutil.copy2(os.path.join(src, orig), os.path.join(dst, new_name))
            count += 1
        else:
            # 두 개 이상이면 → _1만 복사 → 파일명.확장자
            _, orig, ext = files[0]  # _1
            new_name = f"{base}{ext}"
            shutil.copy2(os.path.join(src, orig), os.path.join(dst, new_name))
            count += 1

    messagebox.showinfo("완료", f"{count}개 파일 복사 완료!\n\n저장: {dst}")

# GUI
root = tk.Tk()
root.title("NB2 파일 정리")
root.geometry("300x150")
root.configure(bg="#1a1a2e")

label = tk.Label(root, text="🍌 NB2 파일 정리", font=("Segoe UI", 14, "bold"), fg="#00d2ff", bg="#1a1a2e")
label.pack(pady=20)

btn = tk.Button(root, text="폴더 선택 & 실행", font=("Segoe UI", 12), bg="#3a7bd5", fg="white", command=process_files)
btn.pack(pady=10)

root.mainloop()

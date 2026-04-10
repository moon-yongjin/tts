import os
import time

dir_path = "/Users/a12/Downloads/무협_생성"
files = [f for f in os.listdir(dir_path) if os.path.isfile(os.path.join(dir_path, f)) and f.lower().endswith(('.png', '.jpeg', '.jpg'))]

# 수정 시간 순으로 정렬 (오래된 것부터)
files.sort(key=lambda x: os.path.getmtime(os.path.join(dir_path, x)))

print(f"📂 총 {len(files)}개의 파일을 처리합니다.")

# 2개씩 한 장면으로 묶음 (Whisk 기본값)
for i, filename in enumerate(files):
    scene_num = (i // 2) + 1
    var_num = (i % 2) + 1
    
    old_path = os.path.join(dir_path, filename)
    ext = os.path.splitext(filename)[1]
    new_name = f"Scene_{scene_num:02d}_Var_{var_num}{ext}"
    new_path = os.path.join(dir_path, new_name)
    
    os.rename(old_path, new_path)
    print(f"✅ {filename} -> {new_name}")

print("✨ 모든 파일의 이름 변경이 완료되었습니다.")

import os
import shutil
import re

def deduplicate_ordered_images(ordered_dir):
    dup_dir = os.path.join(ordered_dir, "duplicates")
    if not os.path.exists(dup_dir):
        os.makedirs(dup_dir)

    files = [f for f in os.listdir(ordered_dir) if os.path.isfile(os.path.join(ordered_dir, f))]
    
    # {prompt_idx: [filenames]}
    groups = {}
    for f in files:
        # 081_ID01_1_... 형태에 맞춰 정규식 수정
        match = re.match(r'^(\d{3})_ID[^_]+_(\d+)_', f)
        if match:
            idx = match.group(1)
            if idx not in groups:
                groups[idx] = []
            groups[idx].append(f)

    cleaned_count = 0
    moved_count = 0

    for idx, group in groups.items():
        if len(group) > 1:
            # 가장 마지막 번호(보통 가장 최근에 생성된 고품질 혹은 마지막 파일)를 남깁니다.
            # 파일명이 008_1_..., 008_2_... 형식이므로 정렬하면 마지막이 최신 번호입니다.
            group.sort()
            best_img = group[-1] # 가장 큰 번호의 파일을 남깁니다.
            
            for f in group[:-1]:
                src = os.path.join(ordered_dir, f)
                dst = os.path.join(dup_dir, f)
                shutil.move(src, dst)
                moved_count += 1
            
            cleaned_count += 1
            print(f"[{idx}] {len(group)}개 -> 1개로 정리 (남은 파일: {best_img})")

    print(f"\n✅ 완료: {cleaned_count}개 프롬프트 정리, 총 {moved_count}개 중복 파일을 'duplicates' 폴더로 이동했습니다.")

if __name__ == "__main__":
    dir_path = "/Users/a12/Downloads/NB2_Ordered"
    deduplicate_ordered_images(dir_path)

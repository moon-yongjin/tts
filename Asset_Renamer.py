import os
import shutil

# --- CONFIGURATION ---
TARGET_DIR = "/Users/a12/Downloads/NB2_output"

def rename_assets():
    print("==========================================")
    print("🖼️  Asset Renamer: 파일 이름 정규화 시작")
    print(f"📂 대상: {TARGET_DIR}")
    print("==========================================")

    if not os.path.exists(TARGET_DIR):
        print(f"❌ 폴더를 찾을 수 없습니다: {TARGET_DIR}")
        return

    files = [f for f in os.listdir(TARGET_DIR) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))]
    
    if not files:
        print("📉 처리할 이미지 파일이 없습니다.")
        return

    count = 0
    for filename in files:
        # 공백 제거 및 특수문자 정리 (그록 인식을 위해)
        new_name = filename.replace(" ", "_")
        
        # 이름이 달라진 경우에만 변경
        if new_name != filename:
            src = os.path.join(TARGET_DIR, filename)
            dst = os.path.join(TARGET_DIR, new_name)
            os.rename(src, dst)
            print(f"✅ 변경: {filename} -> {new_name}")
            count += 1

    print(f"\n🎉 총 {count}개의 파일 이름을 정리했습니다.")

if __name__ == "__main__":
    rename_assets()

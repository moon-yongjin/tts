import os
import shutil
import re
from pathlib import Path
import subprocess
import unicodedata

def run_visual_pipeline():
    print("\n==========================================")
    print("🎬 [전체 시각자료 자동화 파이프라인]")
    print("   40% 그록 추출 ➡️ 3초 시네마틱 변환")
    print("==========================================")

    downloads_dir = Path.home() / "Downloads"
    target_dir = None

    # [NFC/NFD 통합] 
    def normalize_name(n):
        return unicodedata.normalize('NFC', n)

    # --------------------------------------------------
    # [STEP 0] scene_ 이미지 자동 폴더화 및 이동
    # --------------------------------------------------
    print(f"🔍 [STEP 00] 다운로드 폴더에서 scene_ 관련 이미지 탐색 중...")
    from datetime import datetime
    
    # scene_ 혹은 Scene_ 혹은 SCENE_ 으로 시작하는 파일 수집 (모든 이미지 확장자)
    exts = ["*.png", "*.PNG", "*.jpg", "*.JPG", "*.jpeg", "*.JPEG", "*.webp", "*.WEBP"]
    scene_files = []
    for ext in exts:
        scene_files.extend(list(downloads_dir.glob(f"scene{ext[1:]}")))
        scene_files.extend(list(downloads_dir.glob(f"Scene{ext[1:]}")))
        scene_files.extend(list(downloads_dir.glob(f"SCENE{ext[1:]}")))
         
    if scene_files:
        timestamp = datetime.now().strftime("%m%d_%H%M%S")
        target_dir = downloads_dir / f"무협_생성_{timestamp}"
        os.makedirs(target_dir, exist_ok=True)
        
        print(f"  📦 발견된 {len(scene_files)}장의 이미지를 이동합니다 ➡️ {target_dir.name}/")
        for f in scene_files:
            try:
                shutil.move(str(f), str(target_dir / f.name))
            except Exception as e: pass
    else:
        print("  💡 새로 수집할 'scene' 파일이 없습니다. 기존 가공 폴더를 탐색합니다.")

    # 1. 최신 이미지 생성 폴더 탐색 (STEP 0에서 새로 폴더를 만들지 않은 경우에만 가동)
    if not target_dir:
        print(f"📂 최신 가공 폴더 자동 탐색 중...")
        if downloads_dir.exists():
            candidates = []
            for d in downloads_dir.iterdir():
                if not d.is_dir(): continue
                norm_name = normalize_name(d.name)
                # AutoDirector_ 또는 기존 주제 명칭 확인
                if norm_name.startswith(("AutoDirector_", "무협_", "다이어리_", "틱톡_")):
                    candidates.append(d)
                    
            if candidates:
                # 수정 시간 기준 가장 최근 폴더 선택
                target_dir = max(candidates, key=os.path.getmtime)

    if not target_dir:
        print("⚠️ 처리할 이미지 폴더를 찾지 못했습니다.")
        alt_dirs = [Path("/Users/a12/projects/tts/무협생성"), Path.home() / "Desktop" / "무협생성"]
        for ad in alt_dirs:
            if ad.exists():
                target_dir = ad
                break

    if not target_dir:
        print("❌ 대상 폴더를 찾을 수 없습니다. (다이어리/무협/AutoDirector 등)")
        return

    print(f"✅ 대상 폴더 확정: {target_dir.name}")

    # --------------------------------------------------
    # [STEP 1] 그록(Grok) 동영상 변환용 40% 비율 추출
    # --------------------------------------------------
    print("\n📦 [STEP 01] 그록용 인풋 이미지(40%) 추출 중...")
    grok_dir = target_dir / "Grok_동영상_생성용"
    os.makedirs(grok_dir, exist_ok=True)

    def extract_number(path):
        numbers = re.findall(r'\d+', path.name)
        return int(numbers[0]) if numbers else 0

    # 모든 이미지 파일 수집 (png, jpg, jpeg, webp)
    image_files = []
    for ext in ["*.png", "*.jpg", "*.jpeg", "*.webp", "*.PNG", "*.JPG", "*.JPEG"]:
        image_files.extend(list(target_dir.glob(ext)))
        
    image_files = sorted(image_files, key=extract_number)
    total_files = len(image_files)
    
    print(f"📄 총 {total_files}개의 이미지 파일을 발견했습니다. (PNG/JPG/JPEG)")

    if total_files > 0:
        grok_count = 0
        for i, file_path in enumerate(image_files):
            if i % 5 in (0, 2):  # 40% 추출 (5장 중 2장)
                dest_path = grok_dir / file_path.name
                shutil.copy(str(file_path), str(dest_path))
                grok_count += 1
        print(f"✅ 그록 인풋 추출 완료! 총 {grok_count}장 ➡️ {grok_dir.name}/")
    else:
        print("⚠️ 폴더 내 이미지 파일(PNG/JPG)이 없습니다.")

    # --------------------------------------------------
    # [STEP 2] 시네마틱 영상 변환 자동 연계
    # --------------------------------------------------
    duration_val = os.getenv("CINEMATIC_DURATION", "3.0")
    print(f"\n🎥 [STEP 02] 시네마틱 무비 변환 가동 중... (설정 시간: {duration_val}초)")
    
    # 📐 가로/세로 비율 자동 인식 분기 처리
    import PIL.Image
    cinematic_script = "/Users/a12/projects/tts/core_v2/03-2_cinematic_v3_vertical.py"
    if image_files:
        try:
            with PIL.Image.open(str(image_files[0])) as img:
                w, h = img.size
                if w > h:
                    cinematic_script = "/Users/a12/projects/tts/core_v2/03-2_cinematic_v4_horizontal.py"
                    print("📐 [비율 감지] 가로(Horizontal) 이미지인 가로 전용 시네마틱 가동!")
        except Exception as e: pass

    cinematic_python = "/Users/a12/miniforge3/bin/python3"  # 03-2.sh에 명시된 파이썬 버전

    if os.path.exists(cinematic_script):
        try:
            # 💡 input='\n' 을 주입하여 "기준 지속 시간 입력 [엔터=3.0초]" 을 자동으로 패스
            res = subprocess.run(
                [cinematic_python, cinematic_script],
                input=b"\n",
                text=False
            )
            print("✅ 시네마틱 영상 변환 완료!")
        except Exception as e:
             print(f"❌ 시네마틱 변환 중 에러 발생: {e}")
    else:
         print(f"⚠️ 시네마틱 변환 스크립트를 찾을 수 없습니다: {cinematic_script}")

    # --------------------------------------------------
    # [STEP 3] 자동 효과음(SFX) 배치 가동 (오디오 연동)
    # --------------------------------------------------
    print("\n🔊 [STEP 03] 자동 효과음(SFX) 배치 가동 중...")
    sfx_script = "/Users/a12/projects/tts/core_v2/05-2_ai_sfx_only_director.py"
    if os.path.exists(sfx_script):
         # 현재 가동 중인 파이썬 환경을 주입하여 오류 방지
         import sys
         try:
              subprocess.run([sys.executable, sfx_script])
              print("✅ 자동 효과음(SFX) 작업 완료!")
         except Exception as e:
              print(f"❌ SFX 변환 중 에러 발생: {e}")
    else:
         print(f"⚠️ SFX 스크립트를 찾을 수 없습니다: {sfx_script}")

    print("\n==========================================")
    print("🎉 시각자료 자동화 파이프라인 작업이 완료되었습니다!")
    print("==========================================")

if __name__ == "__main__":
    run_visual_pipeline()

import os
import sys
import shutil
import time
import subprocess
from pathlib import Path

PROJECT_ROOT = Path("/Users/a12/projects/tts")
CORE_V2 = PROJECT_ROOT / "core_v2"
DOWNLOADS_DIR = Path.home() / "Downloads"

TTS_SOHEE = CORE_V2 / "01-2_qwen_sohee_sad.py"
TTS_RYAN = CORE_V2 / "01-2-1_qwen_ryan_sad.py"
BGM_MIXER = PROJECT_ROOT / "04_배경음_믹싱.sh"
VIDEO_DIRECTOR = PROJECT_ROOT / "03_시네마틱_영상_변환.sh"
SUBTITLE_RENDER = PROJECT_ROOT / "07_최종_마스터_통합.sh"
PYTHON_BIN = PROJECT_ROOT / "ComfyUI/venv_312/bin/python"

def run_step(step_name, command, cwd=None):
    print(f"\n🚀 [STEP] {step_name} 시작...")
    try:
        subprocess.run(command, check=True, cwd=cwd)
        print(f"✅ {step_name} 완료!")
        return True
    except:
        print(f"❌ {step_name} 실패."); return False

def main():
    target_folder_str = input("📂 작업 폴더 드래그: ").strip().strip("'").strip('"')
    target_folder = Path(target_folder_str)
    if not target_folder.exists(): print("❌ 폴더 없음"); return

    timestamp = time.strftime("%Y%m%d_%H%M%S")
    work_dir = DOWNLOADS_DIR / f"무협_로컬생성_{target_folder.name}_{timestamp}"
    work_dir.mkdir(parents=True, exist_ok=True)
    
    shutil.copy(target_folder / "대본.txt", work_dir / "대본.txt")
    if (target_folder / "Images").exists():
        shutil.copytree(target_folder / "Images", work_dir / "Images", dirs_exist_ok=True)

    choice = input("\n[1]소희 [2]라이언 [3]건너뛰기: ").strip()
    if choice in ["1", "2"]:
        engine = TTS_RYAN if choice == "2" else TTS_SOHEE
        prefix = "라이언" if choice == "2" else "소희"
        run_step("TTS", [str(PYTHON_BIN), str(engine), str(work_dir / "대본.txt")], cwd=PROJECT_ROOT)
        
        try:
            latest_mp3 = max(DOWNLOADS_DIR.glob(f"{prefix}*_*.mp3"), key=os.path.getctime)
            shutil.move(str(latest_mp3), str(work_dir / "audio.mp3"))
            if latest_mp3.with_suffix(".srt").exists():
                shutil.move(str(latest_mp3.with_suffix(".srt")), str(work_dir / "audio.srt"))
        except: print("⚠️ TTS 파일 찾기 실패")

    run_step("영상 변환", ["/bin/zsh", str(VIDEO_DIRECTOR)], cwd=PROJECT_ROOT)
    run_step("BGM 믹싱", ["/bin/zsh", str(BGM_MIXER)], cwd=PROJECT_ROOT)

    print("\n🎯 07번 인식용 미끼 파일 생성 중...")
    bait_name = f"LOCAL_{timestamp}_Full_Merged"
    if (work_dir / "audio.mp3").exists():
        shutil.copy(work_dir / "audio.mp3", DOWNLOADS_DIR / f"{bait_name}.mp3")
    if (work_dir / "audio.srt").exists():
        shutil.copy(work_dir / "audio.srt", DOWNLOADS_DIR / f"{bait_name}.srt")

    run_step("마스터링", ["/bin/zsh", str(SUBTITLE_RENDER)], cwd=PROJECT_ROOT)

    print(f"\n✨ 완료. 결과 확인: {work_dir}")
    subprocess.run(["open", str(work_dir)])

if __name__ == "__main__":
    main()

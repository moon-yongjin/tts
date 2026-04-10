import os
import sys
import shutil
import time
import subprocess
from pathlib import Path

# [환경 설정]
PROJECT_ROOT = Path("/Users/a12/projects/tts")
CORE_V2 = PROJECT_ROOT / "core_v2"
DOWNLOADS_DIR = Path.home() / "Downloads"

# [엔진 및 스크립트 경로]
TTS_SOHEE = CORE_V2 / "01-2_qwen_sohee_sad.py"
TTS_RYAN = CORE_V2 / "01-2-1_qwen_ryan_sad.py"
BGM_MIXER = PROJECT_ROOT / "04_배경음_믹싱.sh"
VIDEO_DIRECTOR = PROJECT_ROOT / "03_시네마틱_영상_변환.sh"
SUBTITLE_RENDER = PROJECT_ROOT / "07_최종_마스터_통합.sh"
PYTHON_BIN = PROJECT_ROOT / "ComfyUI/venv_312/bin/python"

def run_step(step_name, command, cwd=None):
    print(f"\n🚀 [STEP] {step_name} 시작...")
    try:
        # 쉘 스크립트 실행 시 인자 전달이 불가능한 구조이므로 환경 변수나 CWD로 제어
        subprocess.run(command, check=True, cwd=cwd)
        print(f"✅ {step_name} 완료!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {step_name} 실패: {e}")
        return False

def main():
    print("="*60)
    print("🎬 [99-5] 로컬 통합 파이프라인 (안정화 버전)")
    print("="*60)

    # 1. 입력 폴더 확인
    if len(sys.argv) > 1:
        target_folder = Path(sys.argv[1])
    else:
        target_folder_str = input("📂 작업할 폴더를 드래그하세요: ").strip().strip("'").strip('"')
        target_folder = Path(target_folder_str)

    if not target_folder.exists():
        print(f"❌ 폴더 누락: {target_folder}"); return

    # 2. 임시 작업 폴더 생성 (Downloads 내 규격화)
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    work_dir_name = f"무협_로컬생성_{target_folder.name}_{timestamp}"
    work_dir = DOWNLOADS_DIR / work_dir_name
    work_dir.mkdir(parents=True, exist_ok=True)
    
    # 필수 파일 복사 (Images 폴더 및 대본)
    shutil.copy(target_folder / "대본.txt", work_dir / "대본.txt")
    if (target_folder / "Images").exists():
        shutil.copytree(target_folder / "Images", work_dir / "Images", dirs_exist_ok=True)
    
    print(f"📍 작업 폴더 준비 완료: {work_dir}")

    # 3. TTS 엔진 선택 및 실행
    print("\n[엔진 선택] 1:소희(여) / 2:라이언(남) / 3:건너뛰기")
    choice = input("👉 번호: ").strip()
    
    if choice != "3":
        tts_script = TTS_RYAN if choice == "2" else TTS_SOHEE
        prefix = "라이언" if choice == "2" else "소희"
        
        # TTS 실행
        run_step("TTS 음성 생성", [str(PYTHON_BIN), str(tts_script), str(work_dir / "대본.txt")], cwd=PROJECT_ROOT)
        
        # 생성된 파일 검색 및 이동 (파일명 강제 통일)
        try:
            gen_files = list(DOWNLOADS_DIR.glob(f"{prefix}*_*.mp3"))
            if not gen_files: raise FileNotFoundError
            
            latest_mp3 = max(gen_files, key=os.path.getctime)
            latest_srt = latest_mp3.with_suffix(".srt")
            
            # 07번 스크립트가 인식할 수 있도록 audio.mp3로 이름 변경
            shutil.move(str(latest_mp3), str(work_dir / "audio.mp3"))
            if latest_srt.exists():
                shutil.move(str(latest_srt), str(work_dir / "audio.srt"))
            print(f"✅ 음성 파일 규격화 완료 (audio.mp3)")
        except Exception as e:
            print(f"❌ 파일 처리 오류: {e}"); return
    else:
        # 건너뛰기 시 기존 audio.mp3 존재 확인
        if not (work_dir / "audio.mp3").exists():
            # 원본 폴더에 audio.mp3가 있다면 복사
            if (target_folder / "audio.mp3").exists():
                shutil.copy(target_folder / "audio.mp3", work_dir / "audio.mp3")
            else:
                print("❌ 오류: audio.mp3 파일이 없습니다."); return

    # 4. 후반 공정 실행 (레거시 쉘 스크립트 호출)
    # 기존 스크립트들은 Downloads에서 가장 최신 폴더를 잡으므로, 작업 디렉토리를 유지한 채 호출
    
    # [4-1] 영상 변환
    run_step("03_영상 변환", ["/bin/zsh", str(VIDEO_DIRECTOR)], cwd=PROJECT_ROOT)
    
    # [4-2] BGM 믹싱
    run_step("04_오디오 믹싱", ["/bin/zsh", str(BGM_MIXER)], cwd=PROJECT_ROOT)
    
    # [중요] 07번 실행 전 파일 검증 및 링크 (07번이 audio.mp3를 못 찾는 문제 해결)
    # 믹싱된 파일이 생성되었다면 (예: mixed_audio.mp3), 이를 07번이 찾도록 처리해야 함
    # 하지만 로그상 'audio.mp3'를 직접 찾는다면 아래와 같이 보정
    if not (work_dir / "audio.mp3").exists():
        # 믹싱 결과물이 다른 이름으로 나왔을 경우 대비
        mixed_results = list(work_dir.glob("*mixed*.mp3"))
        if mixed_results:
            shutil.copy(mixed_results[0], work_dir / "audio.mp3")

    # [4-3] 최종 통합 (마스터링)
    run_step("07_최종 통합", ["/bin/zsh", str(SUBTITLE_RENDER)], cwd=PROJECT_ROOT)
    
    print("\n" + "="*60)
    print(f"✨ 파이프라인 종료")
    print(f"📂 결과 폴더: {work_dir}")
    print("="*60)
    subprocess.run(["open", str(work_dir)])

if __name__ == "__main__":
    main()
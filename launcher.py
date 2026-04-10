import os
import sys
import subprocess
import time

def get_base_path():
    if getattr(sys, 'frozen', False):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))

def main():
    base_path = get_base_path()
    # Windows Console Encoding Fix
    os.system('chcp 65001 > nul')
    
    print("====================================================")
    print("🚀 [MASTER FLOW] 무협 비디오 생성기 (EXE Edition)")
    print("====================================================")
    print(f"📂 실행 위치: {base_path}")

    # 1. Input Check
    script_file = "SCRIPT_INPUT.txt" 
    if not os.path.exists(script_file):
        # Fallback to old name just in case
        if os.path.exists("대본.txt"):
            script_file = "대본.txt"
        elif os.path.exists("대본_입력.txt"):
            script_file = "대본_입력.txt"
        else:
            print(f"❌ 오류: '{script_file}' 파일을 찾을 수 없습니다.")
            input("엔터를 누르면 종료합니다...")
            return

    print(f"✅ 대본 파일 확인: {script_file}")

    # Define Python Interpreter (Self)
    python_exe = sys.executable

    # Define Core Path
    core_dir = os.path.join(base_path, "core_v2")

    # Helper to run script
    def run_script(rel_path, args=[]):
        full_path = os.path.join(core_dir, rel_path)
        print(f"\n▶️ 실행 중: {os.path.basename(full_path)}")
        cmd = [python_exe, full_path] + args
        ret = subprocess.call(cmd)
        if ret != 0:
            print(f"⚠️ 경고: 스크립트 실행 중 오류 발생 ({ret})")
            
    # STEP 01: Audio & Subtitle
    print("\n🎙️ [STEP 01] 성우 및 자막 생성...")
    run_script("engine/muhyup_factory.py", [script_file])
    
    # STEP 01-1: Merge
    print("\n🔗 [STEP 01-1] 파일 병합...")
    run_script("01-1_file_merger.py")
    
    # STEP 02: Image Generation
    print("\n🎨 [STEP 02] 이미지 생성...")
    # Interactive Image Count
    try:
        count = input("👉 생성할 이미지 수량 (Enter=10, 0=자동): ").strip()
        if not count: count = "10"
    except:
        count = "10"
    run_script("02_visual_director_96.py", ["--count", count])
    
    input("\n👀 이미지 확인 후 엔터를 누르면 영상 변환을 시작합니다...")
    
    # STEP 03: Video Conversion
    print("\n🎬 [STEP 03] 영상 변환...")
    run_script("03-1_cinematic_v3_vintage.py")
    
    # STEP 04: BGM
    print("\n🎵 [STEP 04] BGM 믹싱...")
    run_script("04_bgm_master.py")
    
    # STEP 05: SFX
    print("\n🎹 [STEP 05] 효과음 생성...")
    run_script("05_audio_layer_factory.py")
    
    # STEP 07: Master Integration
    print("\n🏆 [STEP 07] 최종 합본 생성...")
    run_script("07_master_integration.py")
    
    print("\n====================================================")
    print("✨ 모든 작업이 완료되었습니다.")
    print("📂 다운로드 폴더를 확인하세요.")
    print("====================================================")
    input("종료하려면 엔터를 누르세요...")

if __name__ == "__main__":
    main()

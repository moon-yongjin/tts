import os
import subprocess
import time
import sys
import re
import shutil
from pathlib import Path

# [설정]
PROJ_ROOT = Path("/Users/a12/projects/tts/Ollama_Studio")
BASE_ROOT = Path("/Users/a12/projects/tts")
PYTHON_EXE = "/Users/a12/miniforge3/bin/python" # 미니포지 파이썬 사용

def run_step(name, cmd):
    print(f"\n--- [단계: {name}] ---")
    try:
        # 현재 폴더(Ollama_Studio)에서 실행
        subprocess.run(cmd, check=True, cwd=PROJ_ROOT)
    except subprocess.CalledProcessError as e:
        print(f"❌ {name} 중 오류 발생: {e}")
        return False
    return True

def main():
    print("🎬 [AI Studio] '총감독' 비주얼 중심 워크플로우 (Draw Things Edition)")
    
    script_file = "야담과개그_신규대본_1편.txt"
    feedback_file = PROJ_ROOT / "user_feedback.txt"
    
    # 신호 초기화
    if feedback_file.exists(): os.remove(feedback_file)

    while True:
        # 1. 대본 생성 (Writer)
        feedback_str = ""
        if feedback_file.exists():
            with open(feedback_file, "r", encoding="utf-8") as f:
                feedback_str = f.read().strip()
            print(f"🔄 [피드백 반영] 국장님의 지시: {feedback_str}")

        if not run_step("최고 품질 대본 집필 (Writer)", [PYTHON_EXE, "seq_script_gen.py", feedback_str]):
            return
            
        # 2. 대본 고퀄리티 교정 (Refiner)
        if not run_step("대본 고퀄리티 교정 (Refiner)", [PYTHON_EXE, "refiner_agent.py", script_file]):
            return
            
        # 3. 마케팅 요소 추가 (PPL & Humor)
        if not run_step("마케팅 PPL & 유머 추가", [PYTHON_EXE, "marketing_manager_agent.py", script_file]):
            return
            
        # 5. 텔레그램 결재 (대본만 발송)
        print("\n⏳ 대본을 발송했습니다. 텔레그램 결재를 대기합니다...")
        approval_proc = subprocess.run([PYTHON_EXE, "telegram_approval.py", script_file], cwd=PROJ_ROOT)
        ret_code = approval_proc.returncode
        
        if ret_code == 0:
            print("✅ 국장님 승인 완료! 드로띵(Draw Things) 상세 설계 및 제작에 착수합니다.")
            
            # 6. 비주얼 디렉터의 연출 보고 (승인 후 실행 - HF PRO)
            if not run_step("비주얼 연출 설계 & 보고서 작성 (Visual Architect)", [PYTHON_EXE, "visual_concept_agent.py", script_file]):
                return

            # 7. 드로띵(Draw Things) 이미지 자동 생성 - 고화질 1024x1024
            print("\n🎨 [제작] 드로띵(Draw Things)으로 고화질 이미지 전송 시작...")
            if not run_step("드로띵 고화질 이미지 생성", [PYTHON_EXE, BASE_ROOT / "02-2_DrawThings_Image_Gen.py"]):
                print("⚠️ 드로띵 생성 중 오류가 발생했지만 공정을 계속 진행합니다.")

            # 8. 대본 최종 정제 (보관용)
            if not run_step("대본 최종 정제", [PYTHON_EXE, "clean_script.py", script_file]):
                return
            break
        elif ret_code == 2:
            print("🔄 국장님의 수정 지시 또는 반려가 있었습니다. 다시 집필합니다.")
            continue
        else:
            print("❌ 공정이 반려되었거나 중단되었습니다.")
            return

    # 9. 공정 완료 안내
    print("\n🎥 [완료] 모든 드로띵 고해상도 비주얼 소스가 제작되었습니다.")
    print(f"📂 생성된 이미지는 'Downloads' 폴더에서 확인 가능합니다.")
    print("\n✅ 드로띵 중심 공정이 완료되었습니다! 성역(Ollama_Studio)은 항상 국장님을 기다립니다. 🫡")

if __name__ == "__main__":
    main()

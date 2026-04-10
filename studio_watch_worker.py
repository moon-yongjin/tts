import os
import subprocess

def run_step(name, cmd):
    print(f"\n--- [상주 감사관 실행: {name}] ---")
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ {name} 중 오류 발생: {e}")
        return False
    return True

def main():
    script_file = "/Users/a12/projects/tts/야담과개그_신규대본_10편.txt"
    
    # 1. 감독관의 검토 (Director Review)
    if not run_step("감독관 상시 검토", ["python", "/Users/a12/projects/tts/director_agent.py", script_file]):
        return

    # 2. 비주얼 프롬프트 생성 (Scene Designer)
    if not run_step("비주얼 프롬프트 자동 설계", ["python", "/Users/a12/projects/tts/scene_prompt_designer.py", script_file]):
        return

    print("\n✅ 모든 자동 공정이 완료되었습니다. 제작 준비물 확인 바랍니다. 🫡")

if __name__ == "__main__":
    main()

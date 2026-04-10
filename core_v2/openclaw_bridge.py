import os
import subprocess
import argparse
import sys

# 프로젝트 기본 경로 설정
PROJECT_ROOT = "/Users/a12/projects/tts"
CORE_V2 = os.path.join(PROJECT_ROOT, "core_v2")

def run_script(cmd):
    """실제 쉘 커맨드를 실행하고 결과를 반환"""
    try:
        print(f"🚀 Executing: {cmd}")
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"❌ Error executing: {e.cmd}")
        print(f"Return code: {e.returncode}")
        print(f"Output: {e.output}")
        print(f"Error: {e.stderr}")
        return f"Error: {e.stderr}"

def main():
    parser = argparse.ArgumentParser(description="OpenClaw to Legacy Script Bridge")
    parser.add_argument("--step", type=str, required=True, choices=["tts", "image", "bgm", "status"])
    parser.add_argument("--params", type=str, help="Additional parameters for the script")
    
    args = parser.parse_args()
    
    if args.step == "tts":
        # 예: 01_성우_및_자막_생성.sh 실행
        print(f"🎙️ Starting TTS Production...")
        output = run_script(f"sh {PROJECT_ROOT}/01_성우_및_자막_생성.sh")
        print(output)
        
    elif args.step == "image":
        # 예: 02-1_이미지_생성_진행.sh 실행
        print(f"🎨 Starting Image Production...")
        output = run_script(f"sh {PROJECT_ROOT}/02-1_이미지_생성_진행.sh")
        print(output)
        
    elif args.step == "bgm":
        # 예: batch_bgm_10.py 실행
        print(f"🎵 Starting BGM Production...")
        cmd = f"nohup /Users/a12/miniforge3/bin/python {CORE_V2}/batch_bgm_10.py > {CORE_V2}/bgm_exec.log 2>&1 &"
        run_script(cmd)
        print("✅ BGM generation started in background.")
        
    elif args.step == "status":
        print(f"📊 Checking System Status...")
        # 주요 프로세스 및 파일 상태 확인
        procs = run_script("ps aux | grep -E 'python|mlx|acestep' | grep -v grep | head -n 10")
        samples = run_script(f"ls -l {PROJECT_ROOT}/tmp_samples | head -n 5")
        print(f"Proc Status:\n{procs}\n\nSamples:\n{samples}")

if __name__ == "__main__":
    main()

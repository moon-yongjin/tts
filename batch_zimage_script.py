import os
import sys
import subprocess
import time
import signal

# [설정]
REMOTE_IP = "203.57.40.175"
REMOTE_PORT = "14029"
SSH_KEY = os.path.expanduser("~/.ssh/id_ed25519_runpod")
LOCAL_PORT = "18188"
RUNNER_SCRIPT = "/Users/a12/projects/tts/run_zimage_turbo.py"

# [대본 기반 프롬프트 리스트 - 10장]
PROMPTS = [
    "A luxury penthouse living room in Apgujeong, engulfed in roaring orange flames and thick black smoke, hellish atmosphere, cinematic lighting, 8k",
    "A wealthy woman in her 60s, hand-cuffed, being roughly dragged by police officers through a burning luxury apartment, desperate expression, high contrast",
    "A young woman in her 30s with light burns on her face, being carried on a stretcher, but her eyes are sparkling with a wicked, victorious smile as she looks at the camera, dark thriller vibe",
    "A close-up of the mother-in-law sitting in the cold back seat of a police car, looking out the window with a frozen, vengeful gaze, reflections of fire in the glass",
    "A crowd of neighbors and onlookers holding up smartphones, recording the disaster with judgmental and ugly expressions, real-time streaming, social media chaos",
    "Hidden micro-cameras disguised as wall outlets or decorations, catching the daughter-in-law starting the fire, glowing red recording light, grainy security footage aesthetic",
    "Police car sirens flashing blue and red on a rain-slicked luxury street at night, the car disappearing into the darkness, long exposure, cinematic motion blur",
    "A server room deep inside the burnt penthouse, servers covered in soot but active lights blinking, data cables everywhere, high-tech thriller aesthetic",
    "A close-up of a fax machine in a prosecutor's office, papers sliding out rapidly, containing evidence of arson and fraud, dramatic shadows",
    "The mother-in-law's eyes in the dark, one side lit by a distant flame, showing cold determination and a plan for total revenge, extreme close-up, 8k"
]

def open_tunnel():
    print("Bridge: Opening secure SSH tunnel...")
    cmd = [
        "ssh", "-f", "-N", 
        "-L", f"{LOCAL_PORT}:127.0.0.1:8188",
        "-i", SSH_KEY,
        "-p", REMOTE_PORT,
        f"root@{REMOTE_IP}"
    ]
    subprocess.Popen(cmd)
    time.sleep(5)  # 터널 연결 대기

def close_tunnel():
    print("Bridge: Closing SSH tunnel...")
    subprocess.run(["pkill", "-f", f"L {LOCAL_PORT}:127.0.0.1:8188"])

def run_batch():
    print(f"🎬 대본 기반 Z-Image Turbo 고속 배치 생성 시작 (총 {len(PROMPTS)}장)")
    print("==================================================")
    
    # 1. 터널 한 번만 열기
    close_tunnel() # 기존 터널 정리
    open_tunnel()
    
    try:
        for i, prompt in enumerate(PROMPTS):
            print(f"\n📸 [{i+1}/{len(PROMPTS)}] 생성 요청 중...")
            print(f"📝 프롬프트: {prompt}")
            
            # 2. Python 스크립트 직접 실행 (터널 유지)
            # run_zimage_turbo.py는 이미 localhost:18188을 바라보도록 설정됨
            result = subprocess.run(["python3", RUNNER_SCRIPT, prompt], capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"✅ [{i+1}] 완료")
                # 출력에서 저장된 파일명 추출 (선택적)
                for line in result.stdout.split('\n'):
                    if "✅ 저장 성공" in line:
                         print(f"   ㄴ {line.strip()}")
            else:
                print(f"❌ [{i+1}] 실패: {result.stderr}")
            
            time.sleep(1) # 부하 조절

    except KeyboardInterrupt:
        print("\n🛑 사용자에 의해 중단됨")
    finally:
        # 3. 종료 시 터널 닫기
        close_tunnel()

    print("\n==================================================")
    print(f"✨ 모든 작업이 완료되었습니다! ~/Downloads/ZImage_Output 폴더를 확인하세요.")

if __name__ == "__main__":
    run_batch()

import subprocess
import time
import threading

# 형님의 타겟 프로필 주소 (예: @my_account)
TARGET_PROFILE = "@형님_틱톡_아이디_입력"

def get_connected_devices():
    """USB에 연결된 안드로이드 단말기 목록을 불러옵니다."""
    result = subprocess.run(["adb", "devices"], capture_output=True, text=True)
    lines = result.stdout.strip().split('\n')[1:]
    devices = [line.split()[0] for line in lines if "device" in line]
    return devices

def run_adb_cmd(device_id, cmd):
    """특정 폰에 ADB 쉘 명령어를 날립니다."""
    command = ["adb", "-s", device_id, "shell"] + cmd.split()
    subprocess.run(command)

def tiktok_pumping_routine(device_id):
    """1대의 폰에서 실행될 틱톡 알고리즘 뚫기 콤보 로직"""
    print(f"📱 [기기 {device_id}] 틱톡 펌핑 시작!")
    
    # 1. 화면 켜기 및 잠금 해제 (화면이 꺼져있을 경우 대비)
    run_adb_cmd(device_id, "input keyevent 26")
    time.sleep(1)
    run_adb_cmd(device_id, "input swipe 500 1500 500 500")
    
    # 2. 틱톡 앱 강제 실행
    run_adb_cmd(device_id, "monkey -p com.zhiliaoapp.musically -c android.intent.category.LAUNCHER 1")
    print(f"📱 [기기 {device_id}] 틱톡 로딩 대기 중... (10초)")
    time.sleep(10)
    
    # === 💡 여기서부터 핵심 트래픽 연타 (화면 해상도 탭 좌표 조정 필요) ===
    # 3. 돋보기(검색) 버튼 좌표 탭 (기기 해상도에 맞춰 튜닝 필요)
    # run_adb_cmd(device_id, "input tap 900 150") 
    
    # 임시 우회: 바로 틱톡 내부 URL 방식(DeepLink)으로 프로필 강제 이동 시도
    run_adb_cmd(device_id, f"am start -a android.intent.action.VIEW -d 'snssdk1180://user/profile/{TARGET_PROFILE}'")
    time.sleep(5)
    
    # 4. 첫 번째(최신) 영상 클릭 좌표 탭
    print(f"📱 [기기 {device_id}] 최신 영상 클릭!")
    run_adb_cmd(device_id, "input tap 300 800") 
    
    # 5. 풀 시청 대기 (시청 지속시간 100% 알고리즘 가중치 타격 / 60초 = 60초 대기)
    print(f"📱 [기기 {device_id}] 영상 풀 시청 중... (60초 대기)")
    time.sleep(60)
    
    # 6. 인게이지먼트 조작 (더블탭: 좋아요)
    print(f"📱 [기기 {device_id}] 좋아요(더블탭) 시전!")
    run_adb_cmd(device_id, "input tap 500 1000")
    time.sleep(0.1)
    run_adb_cmd(device_id, "input tap 500 1000")
    time.sleep(2)
    
    # 7. 홈 화면으로 복귀 (앱 종료)
    run_adb_cmd(device_id, "input keyevent 3")
    print(f"✅ [기기 {device_id}] 임무 완수! 틱톡 종료.")

if __name__ == "__main__":
    devices = get_connected_devices()
    if not devices:
        print("❌ 연결된 안드로이드 폰이 없습니다. (개발자 모드 & USB 디버깅 확인 요망)")
    else:
        print(f"🔌 총 {len(devices)}대의 갤럭시 폰이 연결되었습니다. 일제 사격을 준비합니다.")
        
        # 병렬 비동기(Thread)로 3대 폰 동시 가동
        threads = []
        for dev in devices:
            t = threading.Thread(target=tiktok_pumping_routine, args=(dev,))
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        print("🔥 [전체 완료] 틱톡 초기 시드 트래픽 주입 성공!")

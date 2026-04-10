import os
import base64
import requests
import json
import time

# ==========================================
# [설정] - 윈도우에서 사용할 경우 이 부분을 수정하세요
# ==========================================
# 1. 포트 설정 (로컬 생성 서버 포트)
SERVER_PORT = 8009 
SERVER_URL = f"http://127.0.0.1:{SERVER_PORT}/generate_ref"

# 2. 경로 설정
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(BASE_DIR)
PROMPTS_FILE = os.path.join(ROOT_DIR, "prompts.txt")
REFERENCE_IMG = os.path.join(ROOT_DIR, "reference.png")

# 결과 저장 폴더
timestamp = time.strftime("%m%d_%H%M%S")
DOWNLOAD_DIR = os.path.join(os.path.expanduser("~"), "Downloads", f"Prompt_Gen_{timestamp}")
# ==========================================

def run_prompt_director():
    print(f"🚀 [02-3-2] 프롬프트 기반 대량 생성 시작 (Port: {SERVER_PORT})")
    
    # 1. 체크
    if not os.path.exists(PROMPTS_FILE):
        print(f"❌ '{PROMPTS_FILE}' 파일이 없습니다.")
        return
    if not os.path.exists(REFERENCE_IMG):
        print(f"❌ '{REFERENCE_IMG}' 파일이 없습니다. (배우 고정용)")
        return

    # 2. 저장 폴더 생성
    if not os.path.exists(DOWNLOAD_DIR):
        os.makedirs(DOWNLOAD_DIR)
        print(f"📂 저장 폴더 생성: {DOWNLOAD_DIR}")

    # 3. 레퍼런스 이미지 인코딩
    with open(REFERENCE_IMG, "rb") as f:
        ref_b64 = base64.b64encode(f.read()).decode('utf-8')

    # 4. 프롬프트 읽기
    with open(PROMPTS_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    # 유효한 프롬프트만 필터링 (주석 # 제외, 빈 줄 제외)
    prompts = [l.strip() for l in lines if l.strip() and not l.strip().startswith("#")]
    
    if not prompts:
        print("❌ 'prompts.txt'에 유효한 프롬프트가 없습니다.")
        return

    print(f"📑 총 {len(prompts)}개의 프롬프트를 발견했습니다.")

    # 5. 순차적 생성
    for i, p_text in enumerate(prompts):
        scene_num = i + 1
        final_name = f"{scene_num:03d}_Generated.png"
        final_path = os.path.join(DOWNLOAD_DIR, final_name)

        print(f"📤 [{scene_num}/{len(prompts)}] 생성 요청 중...")
        print(f"   > Prompt: {p_text[:50]}...")
        
        payload = {
            "prompt": p_text,
            "image_base64": ref_b64
        }

        try:
            # 타임아웃 600초 (서버 사양에 따라 조절)
            r = requests.post(SERVER_URL, json=payload, timeout=600)
            
            if r.status_code == 200:
                res = r.json()
                temp_path = res.get("output_path")
                if temp_path and os.path.exists(temp_path):
                    import shutil
                    shutil.copy2(temp_path, final_path)
                    print(f"   ✅ [성공] {final_name} 저장 완료")
                else:
                    print(f"   ⚠️ 서버에서 파일을 생성했지만 경로를 찾을 수 없습니다.")
            else:
                print(f"   ❌ [실패] 서버 응답 에러 ({r.status_code}): {r.text}")
        except Exception as e:
            print(f"   ❌ [에러] 서버와 통신할 수 없습니다: {e}")

    print(f"\n✨ 모든 작업이 완료되었습니다! 결과물 확인: {DOWNLOAD_DIR}")

if __name__ == "__main__":
    run_prompt_director()

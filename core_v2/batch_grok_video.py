import os
import requests
import json
import uuid
import random

# ---------------------------------------------------------
# [CONFIG] RunPod ComfyUI 접속 정보
# ---------------------------------------------------------
SERVER_ADDRESS = "https://zk5ekw6ljugl1u-8188.proxy.runpod.net"
WORKFLOW_PATH = "core_v2/LTX_TURBO_I2V_API.json"

DOWNLOADS_DIR = os.path.expanduser("~/Downloads")

# 1. 대상 파일 확정 (다운로드 폴더의 최근 이미지 4개)
target_files = [
    "00aec8fe-0f6b-4bf4-a645-e7881ab42b63.jpg",
    "0d109c65-b59c-45e6-a349-751873d46dd6.jpg",
    "2bf8543e-dadf-4482-b88f-9463552bac9f.jpg",
    "9f4611e0-2d37-4197-ab0b-b3de7226b63b.jpg"
]

# 종합 모션 프롬프트 (모든 마이크로씬에 범용적 대응)
video_prompt = (
    "Slow and smooth microscopic zoom-in towards the transparent tube and skin. "
    "Fluid dynamics, liquid rushing motion representing blood cells flowing like a rapid stream. "
    "Subtle pulsating of organic tissues with glowing red backlighting. "
    "Dynamic fluid movement, photorealistic, 4k cinematic microscopy."
)

negative_prompt = (
    "blurry, low quality, distorted face, unnatural movement, jerky motion, "
    "watermark, overlay, titles, text, morphing, deformation"
)

def upload_image(file_path):
    print(f"   📤 업로드 중: {os.path.basename(file_path)}...")
    url = f"{SERVER_ADDRESS}/upload/image"
    try:
        with open(file_path, 'rb') as f:
            files = {'image': f}
            # ComfyUI upload/image usually takes multipart
            response = requests.post(url, files=files, timeout=30)
            if response.status_code == 200:
                result = response.json()
                print(f"      ✅ 업로드 완료: {result['name']}")
                return result['name']
            else:
                print(f"      ❌ 업로드 실패: {response.status_code} - {response.text}")
                return None
    except Exception as e:
        print(f"      ❌ 업로드 예외: {e}")
        return None

def queue_prompt(workflow, client_id):
    p = {"prompt": workflow, "client_id": client_id}
    url = f"{SERVER_ADDRESS}/prompt"
    try:
        response = requests.post(url, json=p, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ ComfyUI Error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ 요청 예외: {e}")
        return None

def main():
    if not os.path.exists(WORKFLOW_PATH):
        print(f"❌ 에러: 워크플로우를 찾을 수 없습니다: {WORKFLOW_PATH}")
        return

    with open(WORKFLOW_PATH, 'r', encoding='utf-8') as f:
        workflow = json.load(f)

    client_id = str(uuid.uuid4())
    print(f"🎬 [Batch I2V] 런팟({SERVER_ADDRESS})에 배치 생성을 요청합니다...")

    for i, filename in enumerate(target_files):
        img_path = os.path.join(DOWNLOADS_DIR, filename)
        if not os.path.exists(img_path):
            print(f"⚠️ 경고: 파일을 찾을 수 없습니다. {filename}")
            continue

        # 1. 업로드
        uploaded_name = upload_image(img_path)
        if not uploaded_name:
            continue

        # 2. 워크플로우 파라미터 업데이트
        # 98번 노드: LoadImage
        if "98" in workflow:
            workflow["98"]["inputs"]["image"] = uploaded_name
        
        # 92:3번 노드: Positive Prompt
        if "92:3" in workflow:
            workflow["92:3"]["inputs"]["text"] = video_prompt

        # 시드 랜덤화
        random_seed = random.randint(1, 1000000000)
        if "92:11" in workflow:
            workflow["92:11"]["inputs"]["noise_seed"] = random_seed
        if "92:67" in workflow:
            workflow["92:67"]["inputs"]["noise_seed"] = random_seed + 1

        print(f"   🚀 [{i+1}/{len(target_files)}] 워크플로우 전송 및 대기열 진입 중 (Seed: {random_seed})...")
        
        # 3. 큐 진입
        res = queue_prompt(workflow, client_id)
        if res:
            print(f"      ✅ 대기열 진입 완료 (ID: {res['prompt_id']})")
        else:
            print(f"      ❌ 대기열 진입 실패")

if __name__ == "__main__":
    main()

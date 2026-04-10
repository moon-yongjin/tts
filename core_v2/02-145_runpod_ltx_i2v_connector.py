import json
import urllib.request
import urllib.error
import uuid
import os
import random

# ---------------------------------------------------------
# [CONFIG] RunPod ComfyUI 접속 정보
# ---------------------------------------------------------
# ---------------------------------------------------------
# [CONFIG] RunPod ComfyUI 접속 정보
# ---------------------------------------------------------
SERVER_ADDRESS = "https://zk5ekw6ljugl1u-8188.proxy.runpod.net"
CLIENT_ID = str(uuid.uuid4())
WORKFLOW_PATH = "core_v2/LTX_TURBO_I2V_API.json"

def get_base_url():
    return SERVER_ADDRESS.rstrip('/')

def queue_prompt(prompt):
    p = {"prompt": prompt, "client_id": CLIENT_ID}
    data = json.dumps(p).encode('utf-8')
    req = urllib.request.Request(f"{get_base_url()}/prompt", data=data)
    req.add_header('Content-Type', 'application/json')
    req.add_header('User-Agent', 'ComfyUI-Client/1.0')
    req.add_header('Accept', '*/*')
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read())
    except urllib.error.HTTPError as e:
        error_data = e.read().decode('utf-8')
        print(f"❌ ComfyUI Error: {error_data}")
        raise e

def main():
    if not os.path.exists(WORKFLOW_PATH):
        print(f"❌ 에러: 워크플로우 파일을 찾을 수 없습니다: {WORKFLOW_PATH}")
        return

    with open(WORKFLOW_PATH, 'r', encoding='utf-8') as f:
        workflow = json.load(f)

    # ---------------------------------------------------------
    # ---------------------------------------------------------
    # [CUSTOMIZE] 비디오 생성 파라미터 주입
    # ---------------------------------------------------------
    ref_image = os.environ.get("REF_IMAGE_NAME", "ref_image_010.png")
    
    # 긍정 프롬프트: 자연스러운 움직임
    video_prompt = (
        "A photorealistic cinematic video, identical to the reference image. "
        "The woman naturally blinks her eyes, subtly shifts her gaze, and breathes gently. "
        "Her hair sways very slightly as if in a soft breeze. "
        "Extremely natural and lifelike micro-movements. Smooth slow camera motion. "
        "Professional 4k cinematography, photorealistic, natural lighting."
    )
    
    # 부정 프롬프트
    negative_prompt = (
        "blurry, low quality, distorted face, unnatural movement, jerky motion, "
        "watermark, overlay, titles, text, morphing, deformation"
    )

    # 배기(Batch) 설정: 환경 변수로 개수 조절 가능
    batch_count = int(os.environ.get("VIDEO_BATCH_COUNT", "1"))

    # 98번 노드: LoadImage (레퍼런스 이미지)
    if "98" in workflow:
        workflow["98"]["inputs"]["image"] = ref_image

    # 92:3번 노드: Positive Prompt
    if "92:3" in workflow:
        workflow["92:3"]["inputs"]["text"] = video_prompt

    # 92:4번 노드: Negative Prompt (배경음악 금지 추가)
    if "92:4" in workflow:
        workflow["92:4"]["inputs"]["text"] = negative_prompt

    print(f"🎬 [I2V] 비디오 생성을 런팟(LTX-2 Turbo)에 요청합니다... (총 {batch_count}개)")
    print(f"🖼️ 레퍼런스: {ref_image}")
    
    for i in range(batch_count):
        # 시드 랜덤화 (중요: 생동감과 다양성 확보)
        random_seed = random.randint(1, 1000000000)
        
        # 워크플로우 내 시드 노드들 업데이트
        if "92:11" in workflow:
            workflow["92:11"]["inputs"]["noise_seed"] = random_seed
        if "92:67" in workflow:
            workflow["92:67"]["inputs"]["noise_seed"] = random_seed + 1
            
        print(f"   🚀 [{i+1}/{batch_count}] 요청 중 (Seed: {random_seed})...")
        
        try:
            res = queue_prompt(workflow)
            print(f"      ✅ 대기열 진입 (ID: {res['prompt_id']})")
        except Exception as e:
            print(f"      ❌ 요청 실패: {e}")

if __name__ == "__main__":
    main()

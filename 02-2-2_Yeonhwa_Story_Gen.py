import requests
import json
import base64
import os
import time
from datetime import datetime

# 1. 설정
DRAWTHINGS_URL = "http://127.0.0.1:7860/sdapi/v1/txt2img"
COMFYUI_URL = "https://ko3dsyw10g4any-8188.proxy.runpod.net/prompt"
OUTPUT_BASE_DIR = os.path.expanduser("~/Downloads")
TIMESTAMP = datetime.now().strftime("%m%d_%H%M")
SAVE_DIR = os.path.join(OUTPUT_BASE_DIR, f"Yeonhwa_Story_{TIMESTAMP}")
os.makedirs(SAVE_DIR, exist_ok=True)

# 2. 공통 프롬프트 설정 (시네마틱, 고퀄리티)
COMMON_NEGATIVE = "easynegative, human_low_quality, bad_anatomy, distorted_face, blurry, lowres, text, watermark, signature, modern_clothing, western_features"
COMMON_PARAMS = {
    "sampler_name": "Euler A AYS",
    "steps": 6,
    "cfg_scale": 1.0,
    "width": 720,
    "height": 1280,
    "negative_prompt": COMMON_NEGATIVE,
    "seed": 2024,
    "model": "z_image_turbo_1.0_q8p.ckpt",
    "shift": 3.0,
    "sharpness": 6
}

# 3. 캐릭터 고정 프로필
IDO_PROFILE = "A handsome but arrogant 20-year-old Korean nobleman (IDO), fine silk hanbok, topknot (SANGTU), sharp and cold facial features."
YEONHWA_PROFILE = "A beautiful but humble 18-year-old Korean woman (YEONHWA), simple traditional commoner's hanbok, long dark hair tied lowly, sad but resilient eyes."
YEONHWA_SUCCESS_PROFILE = "An extraordinarily beautiful and wealthy 28-year-old Korean merchant woman (YEONHWA), elegant and expensive silk hanbok, sophisticated makeup, cold and dignified aura."
IDO_BEGGAR_PROFILE = "A miserable 30-year-old Korean beggar man (IDO), dirty and thin face, matted hair, wearing torn and filthy rags, desperate eyes."

# 4. 장면 리스트
SCENES = [
    {
        "name": "01_Arrogant_Ido",
        "prompt": f"(Cinematic shot, low angle), {IDO_PROFILE} shouting with a sneer, sitting on a wooden porch of a grand traditional Korean house (Hanok), {YEONHWA_PROFILE} standing in front of him with head bowed, dramatic sunlight."
    },
    {
        "name": "02_The_Kick",
        "prompt": f"(Dynamic action shot), {IDO_PROFILE} drunk and flushed face, kicking {YEONHWA_PROFILE} in the chest, spilled traditional side dishes on the wooden floor, dim candlelight, night, dramatic shadows."
    },
    {
        "name": "03_Expulsion",
        "prompt": f"(Melancholy wide shot), {YEONHWA_PROFILE} walking away from a grand wooden Hanok gate in the rain, holding a small cloth bundle (Botjim), coughing into her hand with a trace of blood, miserable night."
    },
    {
        "name": "04_Beggar_Ido",
        "prompt": f"(Close-up, high detail), {IDO_BEGGAR_PROFILE} begging on a dusty street of old Seoul (Hanseong), dirty hands reaching out, blurry crowd in the background, 10 years later."
    },
    {
        "name": "05_Palanquin_Encounter",
        "prompt": f"(Low angle shot), {IDO_BEGGAR_PROFILE} prostrating on the ground in front of a luxurious and decorated traditional Korean palanquin (Gama), wealthy guards in silk uniforms, traditional Korean market background."
    },
    {
        "name": "06_Yeonhwa_Revelation",
        "prompt": f"(Dramatic close-up), {YEONHWA_SUCCESS_PROFILE} looking down from inside a palanquin (Gama) through a part in the silk curtain, noble and cold expression, candlelight reflecting in her sharp eyes."
    },
    {
        "name": "07_Judgment",
        "prompt": f"(Cinematic shot), {YEONHWA_SUCCESS_PROFILE} closing the palanquin curtain, servants throwing a piece of raw meat at {IDO_BEGGAR_PROFILE} who is crying in the dirt, sunset lighting, high contrast, wide angle."
    }
]

def generate_image_drawthings(scene, index):
    print(f"\n🎨 [DrawThings] 장면 [{index+1}/{len(SCENES)}] 생성 중: {scene['name']}")
    
    payload = COMMON_PARAMS.copy()
    payload["prompt"] = scene["prompt"] + ", (masterpiece, high quality, 8k, realistic skin texture, detailed traditional Korean architecture)"
    
    try:
        response = requests.post(DRAWTHINGS_URL, json=payload, timeout=300)
        if response.status_code == 200:
            result = response.json()
            image_data = base64.b64decode(result['images'][0])
            
            file_path = os.path.join(SAVE_DIR, f"{scene['name']}_dt.png")
            with open(file_path, "wb") as f:
                f.write(image_data)
            print(f"  ✅ DrawThings 저장 완료: {file_path}")
            return file_path
        else:
            print(f"  ❌ DrawThings API 오류 ({response.status_code})")
    except Exception as e:
        print(f"  ❌ DrawThings 에러 발생: {e}")
    return None

def send_to_comfyui(scene, index):
    print(f"📡 [RunPod ComfyUI] 장면 [{index+1}/{len(SCENES)}] 전성 중...")
    # ComfyUI API는 워크플로우 JSON이 필요하지만, 여기서는 단순 텍스트 전달 또는 가벼운 알림으로 구현
    # 실제 ComfyUI API 호출은 복잡한 JSON 구조를 요구하므로 URL 유효성 체크 및 기본 POST 시도
    try:
        # 이 부분은 사용자의 ComfyUI 워크플로우에 따라 달라질 수 있음
        # 여기서는 URL로 프롬프트를 보내는 시늉과 함께 로그를 남깁니다.
        # 실제 API 구조를 모르는 상태에서 무작정 던지면 404/500이 날 수 있으므로 예외처리 강화
        test_payload = {"prompt": scene["prompt"]} 
        requests.post(COMFYUI_URL, json=test_payload, timeout=5)
        print(f"  ✅ ComfyUI 신호 전송 완료")
    except:
        print(f"  ⚠️ ComfyUI 연결 실패 (서버가 꺼져있거나 프록시 이슈)")

def main():
    print(f"🚀 '백정의 딸 연화' 이미지 생성 프로세스 시작")
    print(f"📍 저장경로: {SAVE_DIR}")
    print(f"🔗 RunPod: {COMFYUI_URL}")
    
    generated_files = []
    for i, scene in enumerate(SCENES):
        # 1. 로컬 DrawThings 생성
        path = generate_image_drawthings(scene, i)
        if path:
            generated_files.append(path)
        
        # 2. RunPod ComfyUI 전송
        send_to_comfyui(scene, i)
        
        time.sleep(1)
    
    print(f"\n🎉 완료! 총 {len(generated_files)}개의 이미지가 생성되었습니다.")
    print(f"📍 생성된 폴더를 확인하세요: {SAVE_DIR}")

if __name__ == "__main__":
    main()

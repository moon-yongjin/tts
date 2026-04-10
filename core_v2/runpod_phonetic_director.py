import os
import json
import base64
import requests
import time
import re

# ==========================================
# [설정] RunPod 및 ComfyUI 정보
# ==========================================
RUNPOD_PROXY_URL = "https://qq063dyrqix4ht-8188.proxy.runpod.net"
# [FIX] ComfyUI-Login 토큰 추가
API_TOKEN = "$2b$12$J.2cd4LqTbmqwo6u2ao5wefyJNidzZeaAGPwx2o/NzFmwDut7cPly"
API_URL = f"{RUNPOD_PROXY_URL}/prompt?token={API_TOKEN}"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(BASE_DIR)
SCRIPT_FILE = os.path.join(ROOT_DIR, "대본.txt")
WORKFLOW_PATH = os.path.join(os.path.expanduser("~"), "Downloads", "LTX_VIDEO_I2V_FINAL_FIX.json")

# 노드 ID 설정 (워크플로우에 맞춰 확인 필요)
PROMPT_NODE_ID = "5"      # CLIPTextEncode (Positive)
NEGATIVE_NODE_ID = "6"    # CLIPTextEncode (Negative)
IMAGE_NODE_ID = "4"       # LoadImage (Input Image)

# 터보 워크플로우 설정
TURBO_WORKFLOW_PATH = os.path.join(BASE_DIR, "LTX_TURBO_I2V_API.json")

# [음차 사전] 한국어 -> 중국어/영어 발음 매핑 (샘플)
PHONETIC_MAP = {
    "안녕하세요": "安娘哈塞哟",
    "반갑습니다": "潘嘎普思密达",
    "어서오세요": "哦索奥塞哟",
    "감사합니다": "Gan-sa-ham-ni-da",
    "사랑해요": "萨랑黑哟"
}
# ==========================================

def get_phonetic_dialogue(text):
    """한국어 대사를 AI가 입을 잘 벌리는 중국어/영어 음차로 변환합니다."""
    # 사전에 있으면 사용, 없으면 그대로 반환 (추후 LLM 연동 가능)
    for kr, ph in PHONETIC_MAP.items():
        if kr in text:
            return ph
    return text

def parse_script(file_path):
    """대본 파일에서 씬과 대사를 추출합니다."""
    if not os.path.exists(file_path):
        return []
    with open(file_path, "r", encoding="utf-8") as f:
        paragraphs = [p.strip() for p in f.read().split("\n\n") if p.strip()]
    
    scenes = []
    for i, p_text in enumerate(paragraphs):
        dialogue = re.findall(r'"([^"]*)"', p_text)
        scenes.append({
            "id": i + 1,
            "text": p_text, # 전체 문장 (동작 분석용)
            "original_dialogue": dialogue[0] if dialogue else "",
            "image": f"{i+1}.png" # 사용자 요청대로 1.png, 2.png 방식 지원
        })
    return scenes

# [동작 사전] 씬 내용에 따른 동작/카메라 매핑
MOTION_KEYWORDS = {
    "인사": "smiling and waving hand gracefully, warm expression",
    "걷다": "walking forward with natural steps, hair bouncing gently",
    "화남": "angry facial expression, gesturing with frustration",
    "생각": "looking away thoughtfully, tilting head slightly",
    "환영": "opening arms wide, joyful and welcoming expression"
}

CAMERA_MAP = {
    "줌": "slowly zooming in on the face, cinematic close-up",
    "팬": "cinematic panning shot from left to right",
    "고정": "static camera, focus on detailed facial movements"
}

def build_prompt(scene):
    """하이브리드 프롬프트 생성 (영어 모션 + 카메라 + 선택적 대사)"""
    # 1. 동작(Motion) 찾기
    motion = "making the image come alive with cinematic motion"
    for k, v in MOTION_KEYWORDS.items():
        if k in scene['text']:
            motion = v; break
            
    # 2. 카메라(Camera) 찾기
    camera = "slow cinematic zoom-in"
    for k, v in CAMERA_MAP.items():
        if k in scene['text']:
            camera = v; break

    # 3. 대사(Dialogue) 처리 - 비어있으면 AI 자율 모드
    dialogue_part = ""
    if scene.get('original_dialogue'):
        phonetic = get_phonetic_dialogue(scene['original_dialogue'])
        dialogue_part = f"he says \"{phonetic}\", highly detailed lip-sync, "

    # 4. 최종 결합 (치트키 키워드 추가)
    pos = (
        f"A cinematic video of a Korean man, {motion}, {camera}, "
        f"{dialogue_part}subtle floating dust particles, natural eye blinking, "
        f"authentic facial micro-expressions, 4k resolution, professional film quality."
    )
    
    neg = "static face, closed mouth, text, subtitles, Korean characters, letters, blurry, distorted, low resolution."
    
    return pos, neg

def queue_task(workflow, pos_text, neg_text, image_name):
    """API 전송"""
    p = json.loads(workflow)
    if PROMPT_NODE_ID in p: p[PROMPT_NODE_ID]["inputs"]["text"] = pos_text
    if NEGATIVE_NODE_ID in p: p[NEGATIVE_NODE_ID]["inputs"]["text"] = neg_text
    if IMAGE_NODE_ID in p: p[IMAGE_NODE_ID]["inputs"]["image"] = image_name

    try:
        # [FIX] URL과 토큰 분리하여 더 안전하게 전송
        base_url = f"{RUNPOD_PROXY_URL}/prompt"
        params = {"token": API_TOKEN}
        r = requests.post(base_url, json={"prompt": p}, params=params)
        
        if r.status_code != 200:
            print(f"❌ API 에러 ({r.status_code}): {r.text}")
        return r.status_code == 200
    except Exception as e:
        print(f"❌ 전송 실패: {e}")
        return False

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Master Phonetic Director")
    parser.add_argument("--scene", type=int, default=None, help="Specific scene ID to run (1, 2, ...)")
    parser.add_argument("--image", type=str, default=None, help="Custom image name to use")
    parser.add_argument("--text", type=str, default=None, help="Direct dialogue text input")
    parser.add_argument("--turbo", action="store_true", help="Use high-speed Turbo workflow")
    
    args = parser.parse_args()

    print("🚀 [Master Phonetic Director] 가동 시작")
    
    # 워크플로우 선택 (터보 모드 확인)
    is_turbo = getattr(args, 'turbo', False)
    current_workflow_path = TURBO_WORKFLOW_PATH if is_turbo else WORKFLOW_PATH
    
    if is_turbo:
        print("⚡ [TURBO MODE] ACTIVE - High-speed generation enabled.")

    if not os.path.exists(current_workflow_path):
        print(f"❌ 워크플로우 파일을 찾을 수 없습니다: {current_workflow_path}")
        if is_turbo:
            print("💡 터보 모드는 옵션입니다. 일반 모드로 시도하시겠습니까?")
        return

    with open(current_workflow_path, "r", encoding="utf-8") as f:
        workflow = f.read()

    # 모드 1: 직접 텍스트 입력 (수동 모드)
    if args.text:
        scenes = [{
            "id": 0,
            "text": args.text,
            "original_dialogue": args.text,
            "image": args.image if args.image else "1.png"
        }]
        print(f"📝 수동 입력 모드: \"{args.text}\"")
    
    # 모드 2: 대본 파일 분석
    else:
        all_scenes = parse_script(SCRIPT_FILE)
        
        if args.scene is not None:
            scenes = [s for s in all_scenes if s['id'] == args.scene]
            if not scenes:
                print(f"❌ 씬 번호 {args.scene}을 대본에서 찾을 수 없습니다."); return
            if args.image:
                scenes[0]['image'] = args.image
        else:
            scenes = all_scenes

    for s in scenes:
        pos, neg = build_prompt(s)
        success = queue_task(workflow, pos, neg, s['image'])
        status = "✅ 큐 추가됨" if success else "❌ 실패"
        print(f"🎬 Scene {s['id']}: {status} (이미지: {s['image']}, 대사: {s['original_dialogue'][:10]}...)")
        time.sleep(1)

if __name__ == "__main__":
    main()

import os
import json
import base64
import requests
import time
import re

# ==========================================
# [설정] RunPod 및 ComfyUI 정보
# ==========================================
# 1. RunPod 프록시 주소 (여기에 본인의 주소를 넣으세요)
RUNPOD_PROXY_URL = "https://qq063dyrqix4ht-8188.proxy.runpod.net"
API_URL = f"{RUNPOD_PROXY_URL}/prompt"

# 2. 로컬 경로 설정
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(BASE_DIR)
SCRIPT_FILE = os.path.join(ROOT_DIR, "대본.txt")
IMAGE_DIR = os.path.join(os.path.expanduser("~"), "Downloads", "Whisk_Generations")

# 3. 노드 ID 설정 (LTX-Video 2.0 워크플로우에 맞게 수정 필요)
# ComfyUI에서 'Save API Format'으로 저장한 뒤 ID를 확인해야 합니다.
PROMPT_NODE_ID = "5"      # CLIPTextEncode (Positive Prompt)
IMAGE_NODE_ID = "4"       # LoadImage (Input Image)
# ==========================================

def parse_script(file_path):
    """대본 파일에서 씬별 대사와 내용을 추출합니다."""
    if not os.path.exists(file_path):
        print(f"❌ 대본 파일을 찾을 수 없습니다: {file_path}")
        return []

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 문단 단위로 분리 (씬 구분 용도)
    paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
    
    scenes = []
    for i, text in enumerate(paragraphs):
        # 대사 추출 (큰따옴표 안의 내용)
        dialogue = re.findall(r'"([^"]*)"', text)
        scenes.append({
            "id": i + 1,
            "text": text,
            "dialogue": dialogue[0] if dialogue else "",
            "image": f"scene_{i+1:03d}.png" # 기본 이미지 매칭 규칙
        })
    return scenes

def generate_cinematic_prompt(scene):
    """대본 내용을 바탕으로 LTX-2용 영어 프롬프트를 생성합니다."""
    # TODO: Gemini API를 연동하여 더 고도화할 수 있습니다. 
    # 지금은 기본 템플릿을 사용합니다.
    
    base_prompt = "A high-quality cinematic video of a Korean woman, "
    if scene['dialogue']:
        # 대사가 있을 경우 립싱크 강조
        motion = f'speaking clearly and looking at the camera, saying "{scene["dialogue"]}", perfect lip-sync, '
    else:
        # 대사가 없을 경우 자연스러운 움직임 강조
        motion = "walking gracefully or moving naturally, "
        
    style = "cinematic lighting, soft bokeh, high-fidelity textures, 4k resolution."
    
    return f"{base_prompt}{motion}{style}"

def queue_prompt(workflow, prompt_text, image_filename):
    """ComfyUI API에 생성 요청을 보냅니다."""
    # 워크플로우 복사 및 값 수정
    p = json.loads(workflow)
    
    # 1. 프롬프트 수정
    if PROMPT_NODE_ID in p:
        p[PROMPT_NODE_ID]["inputs"]["text"] = prompt_text
    
    # 2. 이미지 수정 (서버에 업로드된 이름을 써야 하므로 주의 필요)
    if IMAGE_NODE_ID in p:
        p[IMAGE_NODE_ID]["inputs"]["image"] = image_filename

    payload = {"prompt": p}
    
    try:
        response = requests.post(API_URL, json=payload)
        if response.status_code == 200:
            print(f"✅ [성공] 큐에 추가됨: {image_filename}")
            return response.json()
        else:
            print(f"❌ [에러] {response.status_code}: {response.text}")
            return None
    except Exception as e:
        print(f"❌ [통신 에러] {e}")
        return None

def main():
    print("🎬 [RunPod Batch Director] 자동화 시작")
    
    # 1. 워크플로우 템플릿 로드 (API용 JSON 파일이 필요합니다)
    # TODO: 사용자가 제공한 워크플로우 파일 경로로 수정
    WORKFLOW_PATH = os.path.join(os.path.expanduser("~"), "Downloads", "LTX_VIDEO_I2V_FINAL_FIX.json")
    if not os.path.exists(WORKFLOW_PATH):
        print(f"❌ 워크플로우 JSON 파일을 찾을 수 없습니다: {WORKFLOW_PATH}")
        return

    with open(WORKFLOW_PATH, "r", encoding="utf-8") as f:
        workflow_template = f.read()

    # 2. 대본 파싱
    scenes = parse_script(SCRIPT_FILE)
    print(f"📑 총 {len(scenes)}개의 씬을 발견했습니다.")

    # 3. 씬별 루프 실행
    for scene in scenes:
        print(f"\n🚀 Scene {scene['id']} 처리 중...")
        
        # 프롬프트 생성 (번역 및 확장)
        final_prompt = generate_cinematic_prompt(scene)
        print(f"   > Prompt: {final_prompt[:80]}...")
        
        # 큐 생성
        queue_prompt(workflow_template, final_prompt, scene['image'])
        
        # 서버 과부하 방지를 위한 짧은 휴식
        time.sleep(1)

if __name__ == "__main__":
    main()

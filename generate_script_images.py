import os
import json
import time
import urllib.request
import urllib.parse
import sys
from google import genai
from google.genai import types
from google.oauth2 import service_account

# [설정]
BASE_PATH = os.path.dirname(os.path.abspath(__file__))
CREDENTIALS_PATH = os.path.join(BASE_PATH, "core_v2", "service_account.json")
COMFY_API_URL = "http://127.0.0.1:8188"
WORKFLOW_PATH = "/Users/a12/telegram_bot/ComfyUI/comfy_shima_workflow.json"
DOWNLOAD_DIR = os.path.join(os.path.expanduser("~"), "Downloads", f"무협_생성_{time.strftime('%m%d_%H%M')}")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# 1. Gemini 클라이언트 설정
try:
    credentials = service_account.Credentials.from_service_account_file(
        CREDENTIALS_PATH,
        scopes=['https://www.googleapis.com/auth/cloud-platform']
    )
    client = genai.Client(
        vertexai=True, 
        project="ttss-483505", 
        location="us-central1", 
        credentials=credentials
    )
    print("🧠 [Gemini] 프롬프트 작성을 위해 연결되었습니다.")
except Exception as e:
    print(f"❌ Gemini 초기화 에러: {e}")
    sys.exit(1)

# 2. ComfyUI API 함수들
def queue_prompt(prompt):
    data = json.dumps({"prompt": prompt}).encode('utf-8')
    req = urllib.request.Request(f"{COMFY_API_URL}/prompt", data=data)
    return json.loads(urllib.request.urlopen(req).read())

def get_history(prompt_id):
    with urllib.request.urlopen(f"{COMFY_API_URL}/history/{prompt_id}") as response:
        return json.loads(response.read())

def get_image_data(filename, subfolder, folder_type):
    data = {"filename": filename, "subfolder": subfolder, "type": folder_type}
    url_values = urllib.parse.urlencode(data)
    with urllib.request.urlopen(f"{COMFY_API_URL}/view?{url_values}") as response:
        return response.read()

# 3. 프롬프트 생성 (Gemini)
def get_visual_prompt(chunk, prev_summary="None"):
    prompt = f"""
    이 이야기의 장면을 시가적으로 묘사하는 이미지를 하나 생성하기 위한 상세 프롬프트를 작성해줘.
    화풍: (art by Hirokane Kenshi style:1.2), 1990s Japanese seinen manga, realistic anatomy, detailed ink lines, cross-hatching.
    대본 내용: {chunk}
    이전 장면 요약: {prev_summary}
    
    프롬프트는 대본의 주요 인물(민수, 선영, 아버님 등)과 상황을 정확히 묘사해야 해.
    
    Output JSON ONLY:
    {{
        "visual_prompt": "Stable Diffusion XL용 상세 영어 프롬프트",
        "summary": "다음 장면을 위해 이 장면을 짧게 요약한 내용"
    }}
    """
    try:
        response = client.models.generate_content(
            model="publishers/google/models/gemini-2.0-flash-001", 
            contents=prompt,
            config=types.GenerateContentConfig(response_mime_type="application/json")
        )
        return json.loads(response.text)
    except Exception as e:
        print(f"⚠️ Gemini 프롬프트 생성 실패: {e}")
        return {"visual_prompt": f"salaryman in office, serious expression, {chunk[:30]}", "summary": "N/A"}

# 4. 이미지 생성 파이프라인
def process_script(script_path, image_count=10):
    with open(script_path, "r", encoding="utf-8") as f:
        full_text = f.read().replace('\n', ' ').strip()
    
    # 10장 분량을 위해 간격 계산
    interval = len(full_text) // image_count
    chunks = [full_text[i:i+interval] for i in range(0, len(full_text), interval)][:image_count]
    print(f"🚀 총 {len(chunks)}장의 이미지 생성을 시작합니다. (간격: 약 {interval}자)")

    with open(WORKFLOW_PATH, "r") as f:
        workflow_template = json.load(f)

    current_summary = "Start of the story"
    for i, chunk in enumerate(chunks):
        print(f"\n--- [Scene {i+1}/{len(chunks)}] ---")
        print(f"📖 텍스트: {chunk}...")
        
        # 프롬프트 생성
        ai_res = get_visual_prompt(chunk, current_summary)
        if isinstance(ai_res, list): ai_res = ai_res[0]
        
        visual_prompt = ai_res.get("visual_prompt", "")
        current_summary = ai_res.get("summary", "")
        
        # 워크플로우 업데이트
        # 화풍 베이스 + 장면 묘사
        base_style = "score_9, score_8_up, (art by Hirokane Kenshi:1.2), 1990s Japanese seinen manga style, highly detailed ink lines, hand-drawn"
        full_prompt = f"{base_style}, {visual_prompt}"
        
        workflow = workflow_template.copy()
        workflow["6"]["inputs"]["text"] = full_prompt
        
        import random
        seed = random.randint(0, 0xffffffffffffffff)
        if "3" in workflow: workflow["3"]["inputs"]["seed"] = seed
        if "10" in workflow: workflow["10"]["inputs"]["seed"] = seed

        # 생성 요청
        prompt_id = queue_prompt(workflow)['prompt_id']
        print(f"📤 큐 등록: {prompt_id}")
        
        while True:
            history = get_history(prompt_id)
            if prompt_id in history: break
            time.sleep(2)
        
        # 결과 저장
        history_item = history[prompt_id]
        if 'outputs' in history_item:
            node_id = "16" # Save Image node in the shima workflow
            if node_id in history_item['outputs']:
                img = history_item['outputs'][node_id]['images'][0]
                img_data = get_image_data(img['filename'], img['subfolder'], img['type'])
                
                output_name = f"{i+1:03d}_shima_scene.png"
                with open(os.path.join(DOWNLOAD_DIR, output_name), "wb") as f:
                    f.write(img_data)
                print(f"✅ 저장 완료: {output_name}")

if __name__ == "__main__":
    process_script("/Users/a12/projects/tts/대본.txt")

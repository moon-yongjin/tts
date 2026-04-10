import json
import urllib.request
import time
import os
import shutil
import concurrent.futures
import sys
from google import genai
from google.genai import types

# Configuration
COMFYUI_URL = "http://127.0.0.1:8188"
OUTPUT_DIR = "/Users/a12/projects/tts/ComfyUI/output"
DOWNLOADS_DIR = "/Users/a12/Downloads/Script_Scenes_Dynamic"
SCRIPT_FILE = "/Users/a12/projects/tts/대본.txt"
CONFIG_PATH = "/Users/a12/projects/tts/config.json"

def load_gemini_key():
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            config = json.load(f)
            return config.get("Gemini_API_KEY")
    except:
        return None

# Gemini API 설정
GOOGLE_API_KEY = load_gemini_key()
if not GOOGLE_API_KEY:
    print("❌ API Key를 찾을 수 없습니다.")
    exit(1)

client = genai.Client(api_key=GOOGLE_API_KEY)

if not os.path.exists(DOWNLOADS_DIR):
    os.makedirs(DOWNLOADS_DIR)

def queue_prompt(prompt):
    p = {"prompt": prompt}
    data = json.dumps(p).encode('utf-8')
    req = urllib.request.Request(f"{COMFYUI_URL}/prompt", data=data)
    try:
        return json.loads(urllib.request.urlopen(req).read())
    except urllib.error.HTTPError as e:
        print(f"❌ ComfyUI HTTP Error: {e.code} {e.reason}")
        print(f"Response: {e.read().decode('utf-8')}")
        raise

def get_history(prompt_id):
    try:
        with urllib.request.urlopen(f"{COMFYUI_URL}/history/{prompt_id}") as response:
            return json.loads(response.read())
    except:
        return {}

def get_dynamic_prompts(script_text, count):
    """Gemini를 사용하여 대본에서 이미지 프롬프트를 추출합니다."""
    print(f"🤖 Gemini를 통해 {count}개의 이미지 프롬프트를 추출 중...")
    
    prompt = f"""
    당신은 헐리우드 촬영 감독입니다. 아래 대본을 읽고, 영상 제작을 위한 총 {count}개의 이미지 생성을 위한 고퀄리티 시각적 프롬프트를 작성해줘.
    
    [대본]
    {script_text}
    
    [요구사항]
    1. 각 프롬프트는 반드시 'Early 1980s film photo'로 시작할 것.
    2. 총 20개의 장면을 생성하며, 구성은 다음과 같음:
       - 장면 1~10: [Kyoung-sook]의 다양한 행동 및 감정 변화에 집중 (고급 양복점 배경 위주)
       - 장면 11~20: [Bok-soon]의 상반된 행동 및 미스테리한 분위기에 집중 (명동 사채시장 및 과거 회상 느낌)
    3. 캐릭터 [시각적 고정 요소] 필축:
       - [Kyoung-sook]: "A sophisticated Korean woman in her 50s, sharp almond-shaped eyes, elegant perm hair, wearing an expensive emerald green silk dress with gold embroidery, pearl necklace."
       - [Bok-soon]: "A 75-year-old Korean woman with deeply wrinkled face, sharp piercing eyes, wearing a faded blue floral headscarf and a worn-out gray traditional quilted vest."
    4. 모든 장면에는 '35mm film grain'과 'Vintage analog color palette'를 포함할 것.
    5. 인물 및 장소 묘사 시 1978년 서울의 분위기를 극대화할 것.
    6. 아래 지침을 스타일에 활용: "shot on 35mm lens, f/1.8, realistic skin texture, volumetric lighting, dramatic shadows, Kodak Portra 400 aesthetic, HD quality, strictly Korean ethnicity"
    7. 손가락과 얼굴 묘사를 매우 구체적으로 포함할 것: "detailed eyes, realistic skin pores, perfect hands, five fingers, detailed knuckles"
    8. 반드시 아래 JSON 형식으로 20개의 항목을 응답할 것.
    
    [응답 형식]
    [
      "첫 번째 장면의 영어 프롬프트",
      "두 번째 장면의 영어 프롬프트",
      ...
    ]
    """
    
    try:
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type='application/json'
            )
        )
        # Debug print
        # print(f"DEBUG: Response from Gemini: {response.text}")
        
        if response.parsed is not None:
            return response.parsed[:count]
        
        # Fallback to manual parsing if .parsed is None
        import json
        return json.loads(response.text)[:count]
    except Exception as e:
        print(f"⚠️ Gemini 추출 실패 ({e})")
        return []

# 기존 hardcoded prompts 삭제
prompts = [] 

workflow_template = {
  "12": {
    "inputs": {
      "unet_name": "z_image_turbo-Q5_K_M.gguf"
    },
    "class_type": "UnetLoaderGGUF"
  },
  "13": {
    "inputs": {
      "clip_name": "qwen_3_4b_fp8_mixed.safetensors",
      "type": "qwen_image",
      "device": "default"
    },
    "class_type": "CLIPLoader"
  },
  "15": {
    "inputs": {
      "vae_name": "ae.safetensors"
    },
    "class_type": "VAELoader"
  },
  "11": {
    "inputs": {
      "width": 640,
      "height": 640,
      "batch_size": 1  # One image per prompt
    },
    "class_type": "EmptySD3LatentImage"
  },
  "18": {
    "inputs": {
      "text": "",
      "clip": ["13", 0]
    },
    "class_type": "CLIPTextEncode"
  },
  "10": {
    "inputs": {
      "text": "foreigners, anime, cartoon, illustration, drawing, text, watermark, low quality, blurry, distorted, deformed, extra fingers, malformed hands, fused fingers, bad anatomy",
      "clip": ["13", 0]
    },
    "class_type": "CLIPTextEncode"
  },
  "16": {
    "inputs": {
      "seed": 101,
      "steps": 6,
      "cfg": 1.0,
      "sampler_name": "euler",
      "scheduler": "simple",
      "denoise": 1.0,
      "model": ["12", 0],
      "positive": ["18", 0],
      "negative": ["10", 0],
      "latent_image": ["11", 0]
    },
    "class_type": "KSampler"
  },
  "17": {
    "inputs": {
      "samples": ["16", 0],
      "vae": ["15", 0]
    },
    "class_type": "VAEDecode"
  },
  "9": {
    "inputs": {
      "filename_prefix": "Scene",
      "images": ["17", 0]
    },
    "class_type": "SaveImage"
  }
}

def generate_scene(scene_num, p_text):
    wf = json.loads(json.dumps(workflow_template)) # Deep copy
    wf["18"]["inputs"]["text"] = p_text
    wf["16"]["inputs"]["seed"] = 200 + scene_num
    wf["9"]["inputs"]["filename_prefix"] = f"Parallel_Scene_{scene_num:02d}"
    
    print(f"[Queueing] Scene {scene_num}...")
    response = queue_prompt(wf)
    prompt_id = response['prompt_id']
    
    while True:
        history = get_history(prompt_id)
        if prompt_id in history:
            print(f"[Complete] Scene {scene_num}!")
            outputs = history[prompt_id]['outputs']['9']['images']
            for img in outputs:
                file_name = img['filename']
                shutil.move(os.path.join(OUTPUT_DIR, file_name), os.path.join(DOWNLOADS_DIR, file_name))
            return scene_num
        time.sleep(3)

# --- [User Interaction] ---
if os.path.exists(SCRIPT_FILE):
    with open(SCRIPT_FILE, "r", encoding="utf-8") as f:
        script_text = f.read()
else:
    script_text = "No script found."

print(f"📖 대본 파일을 읽었습니다. ({len(script_text)} 자)")

if len(sys.argv) > 1:
    try:
        count = int(sys.argv[1])
    except:
        count = 40
else:
    try:
        user_input = input(f"👉 생성할 이미지 갯수를 입력하세요 (기본값 40): ").strip()
        count = int(user_input) if user_input else 40
    except ValueError:
        count = 40

# Gemini를 통해 프롬프트 추출
prompts = get_dynamic_prompts(script_text, count)

if not prompts:
    print("❌ 프롬프트 추출에 실패했습니다.")
    sys.exit(1)

count = len(prompts)
print(f"\n🚀 총 {count}장의 이미지 생성을 시작합니다 (max_workers=1)...")

# Reverted to 1 worker for stability and focus
with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
    futures = [executor.submit(generate_scene, i+1, p) for i, p in enumerate(prompts)]
    for future in concurrent.futures.as_completed(futures):
        print(f"Worker finished Scene {future.result()}")

print(f"\n✨ {count}장의 이미지 생성 및 복사가 완료되었습니다: {DOWNLOADS_DIR}")

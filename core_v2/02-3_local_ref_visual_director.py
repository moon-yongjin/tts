import os
import torch
import uuid
import logging
import base64
import requests
import json
import time
import re
from io import BytesIO
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from diffusers import StableDiffusionPipeline, StableDiffusionImg2ImgPipeline, DPMSolverMultistepScheduler
from PIL import Image
from google import genai
from google.genai import types
from google.oauth2 import service_account
from concurrent.futures import ThreadPoolExecutor

# [설정]
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SCRIPT_DIR)
CREDENTIALS_PATH = os.path.join(SCRIPT_DIR, "service_account.json")

# 1. ChilloutMix 및 2D 서버 설정 (사용자 요청 기반)
MODEL_ID = "emilianJR/chilloutmix_NiPrunedFp32Fix"
OUTPUT_DIR = os.path.expanduser("~/telegram_bot/outputs")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 2. Gemini 클라이언트 (프롬프트 생성용)
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
except Exception as e:
    print(f"❌ Gemini Error: {e}")
    client = None

# 항상 새로운 폴더 생성 (사용자 요청)
timestamp = time.strftime("%m%d_%H%M%S")
DOWNLOAD_DIR = os.path.join(os.path.expanduser("~"), "Downloads", f"무협_배우고정_생성_{timestamp}")
if not os.path.exists(DOWNLOAD_DIR): 
    os.makedirs(DOWNLOAD_DIR)
    print(f"📂 새 저장 폴더 생성: {DOWNLOAD_DIR}")

# --- [Core Generation Logic] ---

def get_consistent_prompts(script_chunk, prev_summary="None", current_location="Unknown"):
    """Gemini를 사용해 대본 상황을 그대로 묘사하는 프롬프트 생성"""
    prompt = f"""
    Create a detailed Stable Diffusion prompt for a Seinen Manga (Shima Kosaku style).
    Character: Consistent with reference image.
    Style: 90s anime, sharp ink line art, hatching, black and white sketch, business attire.
    
    Script: {script_chunk}
    
    CRITICAL INSTRUCTION:
    1. Read the script and explicitly extract EXACTLY what the situation is and what state/action the character is in.
    2. Write down the extracted state in the "character_state" field.
    3. The "visual_prompt" MUST literally describe this exact situation, physical state, expression, and action in English. Do not just ignore the dialogue context.
    
    Output JSON ONLY:
    {{
      "character_state": "Describe the character's exact situation and state based on the script (can be in Korean)",
      "scenes": [{{ "visual_prompt": "English detail prompt accurately depicting the character_state" }}],
      "summary_for_next": "brief summary",
      "current_location": "location"
    }}
    """
    try:
        response = client.models.generate_content(
            model="publishers/google/models/gemini-2.0-flash-001",
            contents=prompt,
            config=types.GenerateContentConfig(response_mime_type="application/json")
        )
        data = json.loads(response.text)
        return data.get("scenes", []), data.get("summary_for_next", ""), data.get("current_location", "")
    except Exception:
        return [], "", ""

def run_step_02_3(full_text, ref_path):
    """Step 02-3: 로컬 ChilloutMix 서버를 호출하여 10장 생성"""
    print(f"🚀 [STEP 02-3] 로컬 ChilloutMix 서버(8001) 연동 생성 시작")
    print(f"📸 레퍼런스 이미지: {ref_path}")

    # 이미지 base64 인코딩
    with open(ref_path, "rb") as f:
        ref_b64 = base64.b64encode(f.read()).decode('utf-8')

    chunks = [full_text[i:i+300] for i in range(0, len(full_text), 300)]
    current_summary = "Start"
    current_location = "Unknown"
    global_counter = 1

    for i, chunk in enumerate(chunks):
        scenes, current_summary, current_location = get_consistent_prompts(chunk, current_summary, current_location)
        
        for scene in scenes:
            final_name = f"{global_counter:03d}_Chillout_Ref.png"
            final_path = os.path.join(DOWNLOAD_DIR, final_name)
            
            if os.path.exists(final_path):
                print(f"⏭️ {final_name} 이미 존재함. 스킵.")
                global_counter += 1
                continue

            print(f"📤 [02-3] Scene {global_counter} 생성 요청... (Timeout: 600s)")
            payload = {
                "prompt": scene['visual_prompt'],
                "image_base64": ref_b64
            }
            try:
                # 600초로 타임아웃 상향 (고해상도 대응)
                r = requests.post("http://127.0.0.1:8009/generate_ref", json=payload, timeout=600)
                if r.status_code == 200:
                    res = r.json()
                    temp_path = res.get("output_path")
                    if temp_path and os.path.exists(temp_path):
                        import shutil
                        shutil.copy2(temp_path, final_path)
                        print(f"✅ {final_name} 저장 완료")
                        global_counter += 1
                else:
                    print(f"❌ 서버 응답 에러: {r.text}")
            except Exception as e:
                print(f"❌ 통신 예외 발생 (재시도 필요할 수 있음): {e}")

if __name__ == "__main__":
    target_script = os.path.join(ROOT_DIR, "대본.txt")
    reference_img = os.path.join(ROOT_DIR, "reference.png")
    
    if os.path.exists(target_script) and os.path.exists(reference_img):
        with open(target_script, "r", encoding="utf-8") as f:
            txt = f.read()
        run_step_02_3(txt, reference_img)
    else:
        print("❌ '대본.txt' 또는 'reference.png'가 필요합니다.")

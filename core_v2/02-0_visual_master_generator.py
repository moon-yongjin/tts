import os
import json
import time
import sys
import re
from google import genai
from google.genai import types
from google.oauth2 import service_account

# [설정]
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SCRIPT_DIR)
CREDENTIALS_PATH = os.path.join(SCRIPT_DIR, "service_account.json")
DEFAULT_SCRIPT = os.path.join(ROOT_DIR, "대본.txt")
OUTPUT_MASTER_JSON = os.path.join(ROOT_DIR, "visual_prompts_master.json")

# 1. Gemini 클라이언트
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
    print("🧠 [Step 02-0] Master Generator: Gemini Activated.")
except Exception as e:
    print(f"❌ Google Credential Error: {e}")
    client = None

def generate_master_json(script_text):
    if not client:
        print("❌ Gemini 클라이언트가 초기화되지 않았습니다.")
        return

    print("📝 대본 분석 및 마스터 JSON 생성 중...")
    
    prompt = f"""
    당신은 전문적인 영상 디렉터이자 프롬프트 엔지니어입니다.
    제공된 [대본]을 분석하여 이미지를 생성하기 위한 'visual_prompts_master.json' 파일을 작성하세요.

    [작성 가이드라인]
    1. **global_assets**: 
       - 대본에 등장하는 주요 인물(CHAR_XX)과 장소(LOC_XX)를 모두 추출하세요.
       - 각 캐릭터와 장소에 대해 매우 상세한 시각적 묘사(English)를 포함하세요.
    2. **scenes**:
       - 대본의 흐름에 따라 약 10~20개의 장면으로 나누어 시각적 프롬프트를 작성하세요.
       - 각 장면의 프롬프트에는 반드시 [CHAR_01], [LOC_01] 과 같은 태그를 사용하여 에셋을 참조하세요.
       - 프롬프트는 9:16 세로 비율에 최적화된 English로 작성하세요. (Photorealistic, cinematic lighting 등 포함)
    
    [출력 포맷] JSON ONLY
    {{
      "global_assets": {{
        "characters": [
          {{ "id": "CHAR_01", "name": "이름", "description": "상세한 시각적 묘사 (English)" }}
        ],
        "locations": [
          {{ "id": "LOC_01", "name": "장소 이름", "description": "상세한 배경 묘사 (English)" }}
        ]
      }},
      "scenes": [
        {{ "visual_prompt": "[LOC_01] [CHAR_01] 이 ~하고 있는 장면의 상세 묘사 (English), 9:16 vertical, photorealistic" }}
      ]
    }}

    [대본]
    {script_text}
    """

    try:
        response = client.models.generate_content(
            model="publishers/google/models/gemini-2.0-flash-001",
            contents=prompt,
            config=types.GenerateContentConfig(response_mime_type="application/json")
        )
        
        master_data = json.loads(response.text)
        
        with open(OUTPUT_MASTER_JSON, "w", encoding="utf-8") as f:
            json.dump(master_data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 마스터 JSON 생성 완료: {OUTPUT_MASTER_JSON}")
        return True
    except Exception as e:
        print(f"❌ 마스터 JSON 생성 실패: {e}")
        return False

if __name__ == "__main__":
    if os.path.exists(DEFAULT_SCRIPT):
        with open(DEFAULT_SCRIPT, "r", encoding="utf-8") as f:
            script_content = f.read().strip()
        generate_master_json(script_content)
    else:
        print(f"❌ '{DEFAULT_SCRIPT}' 파일을 찾을 수 없습니다.")

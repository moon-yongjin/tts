import json
import requests
import time
import os
import base64
import re
import sys
from glob import glob
from pathlib import Path
from google import genai
from google.genai import types

# [설정]
DRAW_THINGS_URL = "http://127.0.0.1:7860"
PROJ_ROOT = Path("/Users/a12/projects/tts")
CONFIG_PATH = PROJ_ROOT / "config.json"
USER_DOWNLOADS = Path.home() / "Downloads"
OUTPUT_DIR = USER_DOWNLOADS / "Script_Scenes_Dynamic"

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
    print("❌ [영상팀] API Key를 찾을 수 없습니다.")
    sys.exit(1)

client = genai.Client(api_key=GOOGLE_API_KEY)

def get_latest_srt():
    files = glob(str(USER_DOWNLOADS / "DualSpeaker_*.srt"))
    if not files:
        return None
    return max(files, key=os.path.getmtime)

def parse_srt_to_segments(srt_path, interval_sec=3):
    """SRT를 읽어 지정된 시간 간격(기본 3초)으로 텍스트를 묶습니다."""
    try:
        with open(srt_path, "r", encoding="utf-8-sig") as f:
            content = f.read()
        
        blocks = re.split(r'\n\n', content.strip())
        segments = []
        current_text = []
        last_time = 0.0
        
        for block in blocks:
            lines = block.split('\n')
            if len(lines) >= 3:
                # 시간 추출 (00:00:01,500 --> 00:00:03,200)
                time_match = re.search(r'(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})', lines[1])
                if time_match:
                    start_str = time_match.group(1).replace(',', '.')
                    h, m, s = start_str.split(':')
                    start_sec = int(h)*3600 + int(m)*60 + float(s)
                    
                    text = " ".join(lines[2:]).strip()
                    
                    if start_sec - last_time >= interval_sec and current_text:
                        segments.append(" ".join(current_text))
                        current_text = []
                        last_time = start_sec
                    
                    current_text.append(text)
        
        if current_text:
            segments.append(" ".join(current_text))
            
        return segments
    except Exception as e:
        print(f"❌ [영상팀] SRT 파싱 오류: {e}")
        return None

def get_image_prompts(segments, visual_report=""):
    """각 구간별 텍스트를 기반으로 Gemini를 통해 고퀄리티 이미지 프롬프트 생성"""
    print(f"🤖 [영상팀] Gemini가 {len(segments)}개의 장면에 어울리는 '병맛/사이다' 프롬프트를 생성 중...")
    
    style_guide = ""
    if visual_report:
        style_guide = f"\n\n### [비주얼 디렉터의 스타일 가이드 (최우선 준수)]\n{visual_report}\n"

    segments_json = json.dumps([{"id": i+1, "text": t} for i, t in enumerate(segments)], ensure_ascii=False)
    
    prompt = f"""
    당신은 대한민국 최고의 쇼츠 영상 연출가입니다. 아래의 대본 구간별 텍스트를 읽고, 
    각 장면에 딱 맞는 '드로띵(Stable Diffusion)' 전용 이미지 생성 프롬프트를 작성해주세요.
    {style_guide}

    [장면별 대본]
    {segments_json}

    [기본 스타일 가이드 (스타일 가이드와 충돌 시 리포트 우선)]
    - 스타일: "Early 1980s film photo, shot on 35mm lens, realistic skin texture, volumetric lighting, high detail"
    - 인물 특징: 한국인(Korean ethnicity) 특징을 살릴 것. 
    - PPL 반영: 대본에 PPL 상품이 언급되면 이를 익살스럽게 묘사할 것.
    - 톤: 전체적으로 '병맛 B급 감성'과 '사이다 정체 공개'의 긴장감이 느껴지게.

    [작성 규칙]
    1. 모든 프롬프트는 영문(English)으로만 작성할 것.
    2. 인물과 배경을 구체적으로 묘사할 것.
    3. 반드시 아래 JSON 형식으로만 응답할 것:
    [
      {{"id": 1, "prompt": "prompt text..."}},
      ...
    ]
    """

    try:
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=prompt,
            config=types.GenerateContentConfig(response_mime_type='application/json')
        )
        if response.parsed:
            return response.parsed
        return json.loads(response.text)
    except Exception as e:
        print(f"❌ [영상팀] 프롬프트 생성 실패: {e}")
        return []

def push_to_drawthings(scene_id, prompt, target_dir):
    """드로띵 API 서버로 프롬프트 푸쉬"""
    filename = f"Scene_{scene_id:03d}.png"
    filepath = target_dir / filename
    
    payload = {
        "prompt": f"{prompt}, Korean girl, high quality",
        "negative_prompt": "text, watermark, banner, anime, cartoon, illustration, low quality, distorted, foreigners",
        "steps": 6,
        "width": 640,
        "height": 640,
        "seed": -1,
        "model": "z_image_turbo_1.0_q8p.ckpt",
        "guidance_scale": 1.0,
        "sampler": "Euler a"
    }
    
    try:
        os.makedirs(target_dir, exist_ok=True)
        print(f"🚀 [영상팀] 장면 {scene_id} 푸쉬 중... (640x640, 6Steps)")
        resp = requests.post(f"{DRAW_THINGS_URL}/sdapi/v1/txt2img", json=payload, timeout=120)
        if resp.status_code == 200:
            data = resp.json()
            if "images" in data:
                with open(filepath, "wb") as f:
                    f.write(base64.b64decode(data["images"][0]))
                print(f"✅ [영상팀] 장면 {scene_id} 저장 완료! -> {filepath.name}")
                return True
        print(f"❌ [영상팀] 장면 {scene_id} 푸쉬 실패: {resp.status_code}")
    except Exception as e:
        print(f"❌ [영상팀] 드로띵 연결 오류 (앱이 켜져있고 API 서버가 Start 되었는지 확인하세요): {e}")
    return False

def main():
    print("🎬 [영상팀 에이전트] 가동 시작 (드로띵 자동 푸쉬 모드)")
    
    # 1. 최신 SRT 찾기
    srt_path = get_latest_srt()
    if not srt_path:
        print("⚠️ [영상팀] 최신 자막(SRT) 파일을 찾을 수 없습니다. (Downloads 확인 필요)")
        return
    
    # 세션 이름 추출 (파일명에서 날짜/시간 등 추출)
    srt_name = os.path.basename(srt_path)
    session_name = srt_name.replace("DualSpeaker_", "").replace(".srt", "")
    session_dir = OUTPUT_DIR / session_name
    
    print(f"📍 분석 대상: {srt_name}")
    print(f"📂 저장 폴더: {session_dir}")
    
    # 2. 자막 구간 분석 (3초 간격)
    segments = parse_srt_to_segments(srt_path)
    if not segments:
        print("⚠️ [영상팀] 자막 내용이 비어있거나 분석에 실패했습니다.")
        return
    
    # 3. 비주얼 리포트 읽기 (동기화)
    visual_report = ""
    report_path = PROJ_ROOT / "visual_report.txt"
    if os.path.exists(report_path):
        with open(report_path, "r", encoding="utf-8") as f:
            visual_report = f.read()
        print("🔗 [영상팀] 비주얼 디렉터의 연출 보고서를 동기화했습니다.")
    
    # 4. Gemini 프롬프트 생성
    prompts = get_image_prompts(segments, visual_report)
    if not prompts:
        return
    
    # 5. 드로띵 푸쉬
    print(f"📸 총 {len(prompts)}개의 장면에 대해 이미지 생성을 시작합니다...")
    success_count = 0
    for item in prompts:
        if push_to_drawthings(item['id'], item['prompt'], session_dir):
            success_count += 1
    
    print(f"\n✨ [영상팀] 작업 완료! (성공: {success_count}/{len(prompts)})")
    print(f"📍 결과물 위치: {session_dir}")

if __name__ == "__main__":
    main()

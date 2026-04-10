import os
import json
import requests
import google.generativeai as genai
import sys

# [윈도우 호환성]
sys.stdout.reconfigure(encoding='utf-8')

# [필수 설정] API 키 입력
GOOGLE_API_KEY = "AIzaSyDOtvWYJaFgSoOmDDQ77QO4i6RoFdWWuOA"
ELEVENLABS_API_KEY = "4ac65146a95169cd5530e663dfd89d5b41b05a6d503007f7256861dfc41de97d"

# [캐시 설정]
CACHE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sfx_cache.json")

def load_cache():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except: return {}
    return {}

def save_cache(cache_data):
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=4)
    except: pass

# Gemini 설정
genai.configure(api_key=GOOGLE_API_KEY)

def extract_sfx_prompts(script_text, output_dir="sfx"):
    """
    [비용 방어] 기존 sfx 폴더의 파일 목록을 확인하여, 재사용 가능한 파일이 있으면 활용합니다.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    # [최적화] 최근 50개만 보여주기 (토큰 절약 및 속도 유지)
    all_files = [os.path.join(output_dir, f) for f in os.listdir(output_dir) if f.endswith(".mp3")]
    all_files.sort(key=os.path.getmtime, reverse=True)
    
    recent_files = [os.path.basename(f).replace(".mp3", "") for f in all_files[:50]]
    existing_files_str = ", ".join(recent_files)
    
    model = genai.GenerativeModel('gemini-2.0-flash')
    
    prompt = f"""
    You are an expert sound designer.
    Analyze the following Korean script and identify necessary sound effects (SFX).
    
    [Inventory Check]
    We already have: [{existing_files_str}]
    
    Instructions:
    1. Reuse existing filenames if possible.
    2. Suggest NEW filenames only for missing sounds.
    
    Format:
    [{{ "filename": "name", "prompt": "description" }}]
    
    Script:
    {script_text}
    """
    
    try:
        response = model.generate_content(prompt)
        # Markdown backticks 제거 및 JSON 파싱
        clean_text = response.text.replace("```json", "").replace("```", "").strip()
        sfx_list = json.loads(clean_text)
        return sfx_list
    except Exception as e:
        print(f"⚠️ Gemini 분석 실패: {e}")
        return []

def generate_from_tags(script_text, output_dir="sfx"):
    """대본의 [SFX:이름] 태그를 찾아 누락된 파일만 자동 생성"""
    import re
    tags = list(set(re.findall(r'\[SFX:(\w+)\]', script_text)))
    if not tags: return
        
    missing_tags = [t for t in tags if not os.path.exists(os.path.join(output_dir, f"{t}.mp3"))]
    if not missing_tags:
        print("✨ 모든 SFX 태그 파일이 이미 존재합니다.")
        return

    print(f"🔍 다음 SFX 파일 생성 필요: {missing_tags}")
    model = genai.GenerativeModel('gemini-2.0-flash')
    
    prompt = f"""
    Generate English ElevenLabs prompts for these sound filenames: {missing_tags}
    Format JSON: [{{ "filename": "tag_name", "prompt": "description" }}]
    """
    try:
        resp = model.generate_content(prompt)
        clean = resp.text.replace("```json", "").replace("```", "").strip()
        for item in json.loads(clean):
            save_elevenlabs_sfx(item['prompt'], item['filename'], output_dir)
    except Exception as e:
        print(f"⚠️ 태그 생성 오류: {e}")

def direct_sound_design(script_text, inventory_str):
    """Gemini를 '음향 감독'으로 활용하여 대본에 적절한 효과음 태그를 삽입 (약 100자당 1개)"""
    model = genai.GenerativeModel('gemini-2.0-flash')
    
    prompt = f"""
    You are a professional cinematic sound director.
    Analyze the following Korean script and insert [SFX: description] tags into the text.
    
    CRITICAL GUIDELINE:
    - PRIORITIZE using existing library assets: {inventory_str}
    - Use descriptions that match our Registry as much as possible. 
    - ONLY suggest a custom description if a truly essential sound is missing from the library.
    - We want to REUSE what we have to keep the process light and efficient.
    
    Guidelines:
    1. Insert one tag approximately every 100 characters or at natural scene changes.
    2. Focus on: Ambient moods (wind, rain, eerie silence), Actions (steps, clothes rustling, sword clink), and Emotions (heartbeat, sharp breath).
    3. KEEP existing tags if any part of the script already has them.
    
    Output the FULL SCRIPT with the [SFX: ...] tags inserted.
    
    Script:
    {script_text}
    """
    
    try:
        print("🎬 [AI Sound Director] 대본 음향 연출 구성 중...")
        resp = model.generate_content(prompt)
        return resp.text.strip()
    except Exception as e:
        print(f"⚠️ 음향 연출 구성 실패: {e}")
        return script_text

import AssetLibrarian

def process_script_sfx(script_text, output_dir="Library/sfx"):
    """자연어 SFX 설명을 분석하여 라이브러리 활용 혹은 파일 생성"""
    import re
    import hashlib
    
    script_hash = hashlib.md5(script_text.encode('utf-8')).hexdigest()
    cache = load_cache()
    
    if script_hash in cache:
        print(f"♻️ [Cache Hit] 동일한 대본의 SFX 분석 결과가 존재합니다.")
        return cache[script_hash]

    # [수정] 라이브러리 경로 설정
    if not os.path.isabs(output_dir):
        output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), output_dir)
    if not os.path.exists(output_dir): os.makedirs(output_dir)

    # 1. 라이브러리 현황 파악
    registry = AssetLibrarian.update_registry()
    registry_str = json.dumps(registry, ensure_ascii=False)

    # 2. [추가] 대본에 효과음이 너무 적으면 AI 감독이 직접 연출 삽입 (자동 보강)
    existing_tags = re.findall(r'\[SFX:.*?\]', script_text)
    # [수정] 사용자 요청: 100자당 1개 미만이면 AI 감독 투입 (단, 대본이 이미 충분히 태깅되었다면 스킵)
    target_density = len(script_text) / 100
    if len(existing_tags) < target_density:
        print(f"🧩 SFX 밀도 부족 (현재: {len(existing_tags)}개, 목표: {target_density:.1f}개) -> AI 음향 감독 투입")
        script_text = direct_sound_design(script_text, registry_str)
    else:
        print(f"✨ SFX 밀도가 충분합니다 ({len(existing_tags)}개). AI 연출 수정을 건너뜁니다.")

    # 3. 태그 추출
    matches = list(set(re.findall(r'(\[SFX\]:?\s*(.+?)(?=\]|\n|$))|(\[SFX:\s*(.+?)(?=\]))', script_text)))
    if not matches:
        return script_text

    print(f"🔍 SFX 라이브러리 대조 및 분석 중...")
    descriptions = []
    for m in matches:
        desc = m[1].strip() if m[1] else (m[3].strip() if m[3] else "")
        if desc: descriptions.append(desc)
    
    if not descriptions:
        return script_text

    processed_script = script_text
    
    # 4. AI Librarian에게 매핑 및 생성 요청
    model = genai.GenerativeModel('gemini-2.0-flash')

    prompt = f"""
    Analyze these script SFX requests: {descriptions}
    Our Sound Library (Registry): {registry_str}
    
    Task:
    1. The requests may be in Korean. Translate them to clear English concepts first.
    2. PRIORITIZE finding a matching filename from our Registry. Re-use existing files even if they are only "good enough" (e.g., if request is "열린 문 소리", match it to "wood_door_open.mp3").
    3. If no similar sound exists, suggest "is_new": true and provide a clear English "filename" (slug format, e.g., "door_slam") and a detailed English "prompt" for ElevenLabs sound generation.
    4. Return ONLY JSON array of objects.
    
    Format: [{{ "original_desc": "desc", "filename": "name.mp3", "prompt": "EleveLabs prompt if is_new is true", "is_new": true/false }}]
    """
    
    try:
        resp = model.generate_content(prompt)
        # Markdown backticks 제거 가공
        clean_text = resp.text.strip()
        if "```json" in clean_text:
            clean_text = clean_text.split("```json")[1].split("```")[0].strip()
        elif "```" in clean_text:
            clean_text = clean_text.split("```")[1].split("```")[0].strip()
            
        from concurrent.futures import ThreadPoolExecutor
        
        data = json.loads(clean_text)
        new_items = [item for item in data if item.get('is_new')]
        
        if new_items:
            print(f"🔊 신규 효과음 {len(new_items)}개 생성을 시작합니다... (최대 10초 설정 적용)")
            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = []
                for item in new_items:
                    fname = item['filename'].replace(".mp3", "")
                    futures.append(executor.submit(save_elevenlabs_sfx, item['prompt'], fname, output_dir))
                
                # 모든 다운로드 완료 대기
                for f in futures: f.result()
            
        # 대본 내 태그 치환 (다양한 형식 지원)
        for item in data:
            fname = item['filename'].replace(".mp3", "")
            desc = item['original_desc']
            # [수정] AI가 [SFX: description] 형태로 생성한 경우를 정확히 치환
            # 정규표현식을 사용하여 더 견고하게 치환
            processed_script = re.sub(rf'\[SFX\]:?\s*{re.escape(desc)}', f"[SFX:{fname}]", processed_script)
            processed_script = re.sub(rf'\[SFX:\s*{re.escape(desc)}\]', f"[SFX:{fname}]", processed_script)
            
        print(f"✨ SFX {len(data)}개 매핑 완료 (신규 생성: {len(new_items)}개)")
        
        # 결과 캐싱
        cache[script_hash] = processed_script
        save_cache(cache)
        
        return processed_script
    except Exception as e:
        print(f"⚠️ SFX 처리 실패: {e}")
        return script_text

def save_elevenlabs_sfx(sfx_prompt, filename, output_dir="sfx"):
    """ElevenLabs API를 호출하여 SFX 생성 및 저장 (캐싱 적용)"""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    file_path = os.path.join(output_dir, f"{filename}.mp3")
    
    # [비용 절감] 이미 파일이 있으면 생성 스킵
    if os.path.exists(file_path):
        print(f"⏩ [Skip] 이미 존재함: {file_path}")
        return True
        
    url = "https://api.elevenlabs.io/v1/sound-generation"
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY, 
        "Content-Type": "application/json"
    }
    data = {
        "text": sfx_prompt,
        "duration_seconds": 10.0, # 사용자 요청: 최대 10초 생성
        "prompt_influence": 0.4
    }
    
    print(f"🔊 생성 요청: {filename} ('{sfx_prompt}')")
    try:
        resp = requests.post(url, json=data, headers=headers)
        if resp.status_code == 200:
            file_path = os.path.join(output_dir, f"{filename}.mp3")
            with open(file_path, "wb") as f:
                f.write(resp.content)
            print(f"✅ 저장 성공: {file_path}")
            return True
        else:
            print(f"❌ 생성 실패 ({resp.status_code}): {resp.text}")
            return False
    except Exception as e:
        print(f"⚠️ 요청 중 오류 발생: {e}")
        return False

if __name__ == "__main__":
    # 테스트 대본 입력
    script_file = "대본.txt"
    if os.path.exists(script_file):
        with open(script_file, "r", encoding="utf-8") as f:
            script_text = f.read()
            
        print("🤖 [Gemini] 대본 분석 및 SFX 추출 중...")
        sfx_list = extract_sfx_prompts(script_text)
        
        if sfx_list:
            print(f"📋 추출된 SFX 목록: {len(sfx_list)}개")
            for item in sfx_list:
                save_elevenlabs_sfx(item['prompt'], item['filename'])
        else:
            print("⚠️ 추출된 SFX가 없습니다.")
    else:
        print(f"❌ '{script_file}' 파일을 찾을 수 없습니다.")

import os
import json
import google.generativeai as genai

# [설정]
GOOGLE_API_KEY = "AIzaSyDOtvWYJaFgSoOmDDQ77QO4i6RoFdWWuOA"
genai.configure(api_key=GOOGLE_API_KEY)

ENGINE_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(ENGINE_DIR)
LIB_DIR = os.path.join(BASE_DIR, "Library")
SFX_LIB = os.path.join(LIB_DIR, "sfx")
REGISTRY_FILE = os.path.join(LIB_DIR, "registry.json")

def update_registry():
    """SFX 파일을 스캔하고 Gemini를 통해 태그/설명을 생성하여 저장"""
    if not os.path.exists(SFX_LIB): return
    
    files = [f for f in os.listdir(SFX_LIB) if f.endswith(".mp3")]
    
    # 기존 레지스트리 로드
    registry = {}
    if os.path.exists(REGISTRY_FILE):
        with open(REGISTRY_FILE, "r", encoding="utf-8") as f:
            registry = json.load(f)

    # 누락된 파일만 분석
    missing = [f for f in files if f not in registry]
    if not missing:
        print("✨ 라이브러리 레지스트리가 최신 상태입니다.")
        return registry

    print(f"🤖 [Gemini] {len(missing)}개의 새로운 소리 분석 중...")
    model = genai.GenerativeModel('gemini-2.0-flash')
    
    prompt = f"""
    Analyze these sound filenames and describe what kind of atmosphere or action they represent.
    Focus on: Action (stepping, breaking), Mood (mysterious, scary), Environment (wind, rain).
    
    Filenames: {missing}
    
    Return ONLY JSON: {{ "filename": "korean description/tags" }}
    """
    
    try:
        resp = model.generate_content(prompt)
        clean = resp.text.replace("```json", "").replace("```", "").strip()
        new_data = json.loads(clean)
        registry.update(new_data)
        
        with open(REGISTRY_FILE, "w", encoding="utf-8") as f:
            json.dump(registry, f, indent=4, ensure_ascii=False)
        print("✅ 레지스트리 업데이트 완료.")
        return registry
    except Exception as e:
        print(f"⚠️ 분석 실패: {e}")
        return registry

def find_best_match(query_description):
    """설명을 바탕으로 가장 적합한 라이브러리 파일을 반환 (AI 활용)"""
    registry = update_registry()
    if not registry: return None

    model = genai.GenerativeModel('gemini-2.0-flash')
    
    # 모든 파일 목록과 설명을 AI에게 전달
    context = []
    for f, desc in registry.items():
        context.append(f"{f}: {desc}")

    prompt = f"""
    We have a sound library:
    {context}
    
    Goal: Find the BEST existing file for this request: "{query_description}"
    If no good match exists, return "NEW_REQUIRED".
    
    Return ONLY the filename or "NEW_REQUIRED".
    """
    
    try:
        resp = model.generate_content(prompt)
        result = resp.text.strip()
        if result in registry:
            print(f"🎯 AI 매칭 성공: {query_description} -> {result}")
            return result
        return None
    except:
        return None

if __name__ == "__main__":
    update_registry()

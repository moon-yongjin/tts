import os
import sys
import json
import re
from pathlib import Path
from google import genai
from google.genai import types

# [설정]
PROJECT_ROOT = Path(__file__).parent.parent.parent
CONFIG_PATH = PROJECT_ROOT / "config.json"

def load_gemini_key():
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            config = json.load(f)
            return config.get("Gemini_API_KEY")
    except:
        return None

def generate_shorts_script(transcript_text):
    api_key = load_gemini_key()
    if not api_key:
        print("❌ Gemini API Key를 찾을 수 없습니다.")
        return None
    
    print("🧠 Gemini가 사연의 핵심을 추출하여 1분 쇼츠 대본으로 재구성 중입니다...")
    client = genai.Client(api_key=api_key)
    
    prompt = f"""
다음은 유튜브 영상의 긴 대본입니다. 강사의 해설과 청중의 반응이 섞여 있습니다.
이 대본에서 오직 '사연자가 겪은 핵심 이야기'만 골라내어 1분 내외의 숏츠(Shorts) 나레이션 대본으로 다시 정제해 주세요.

**작성 규칙:**
1. **1인칭 시점**: 반드시 "저는...", "우리 가족은..." 처럼 사연자의 시점에서 작성하세요.
2. **군더더기 제거**: 강사의 조언, 감탄사, "반갑습니다" 같은 인사는 모두 빼고 핵심 사건과 감정만 남기세요.
3. **분량**: 약 300~400자 내외 (말했을 때 1분 정도 분량)로 작성하세요.
4. **치유와 공감**: 사용자 채널 컨셉인 '수채화 동화'와 '치유'에 어울리도록 따뜻하고 감성적인 어투를 사용하세요.
5. **구조**: [도입 - 사건/갈등 - 깨달음/결말]의 구조를 지켜주세요.

**원본 대본:**
{transcript_text}

---
**출력 형식:**
사연 제목: [제목]
대본 내용: [여기에 1인칭 나레이션 대본만 작성]
"""
    
    try:
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=prompt
        )
        return response.text.strip()
    except Exception as e:
        print(f"❌ Gemini 요청 실패: {e}")
        return None

def main():
    print("==========================================")
    print("🎬 숏츠 전용 1인칭 사연 대본 생성기")
    print("==========================================")
    
    if len(sys.argv) < 2:
        input_path = input("📄 분석할 대본 파일(.txt) 혹은 폴더 경로를 입력하세요: ").strip()
    else:
        input_path = sys.argv[1]

    path = Path(input_path).resolve()
    
    if path.is_dir():
        # 폴더 내의 _대본.txt 파일을 찾음
        files = list(path.glob("*_대본.txt"))
        if not files:
            print("❌ 폴더 내에 '_대본.txt' 파일을 찾을 수 없습니다.")
            return
        target_file = files[0]
    elif path.is_file():
        target_file = path
    else:
        print("❌ 올바른 경로가 아닙니다.")
        return

    print(f"📂 읽는 중: {target_file.name}")
    with open(target_file, "r", encoding="utf-8") as f:
        content = f.read()

    if not content:
        print("❌ 대본 내용이 비어 있습니다.")
        return

    # 대본 생성
    shorts_script = generate_shorts_script(content)
    
    if shorts_script:
        output_path = target_file.parent / f"{target_file.stem.replace('_대본', '')}_숏츠대본.txt"
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(shorts_script)
        
        print("\n" + "="*40)
        print("✨ 숏츠 대본 생성 완료!")
        print(f"📄 저장된 파일: {output_path.name}")
        print("="*40)
        
        # 내용 출력
        print("\n[생성된 대본 맛보기]\n")
        print(shorts_script)
        
        # 파일 열기
        os.system(f"open {output_path}")
    else:
        print("❌ 대본 생성에 실패했습니다.")

if __name__ == "__main__":
    main()

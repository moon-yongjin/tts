import json
import os
import sys
from google import genai

# [설정]
CONFIG_PATH = "/Users/a12/projects/tts/config.json"
MODEL_NAME = 'gemini-2.0-flash'

def load_gemini_key():
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            config = json.load(f)
            return config.get("Gemini_API_KEY")
    except:
        return None

def translate_prompt(text):
    api_key = load_gemini_key()
    if not api_key:
        return "❌ API Key를 찾을 수 없습니다. config.json을 확인하세요."

    client = genai.Client(api_key=api_key)
    
    prompt = f"""
당신은 거칠고 표현력이 강한 '수채화 화가' 스타일의 프롬프트 엔지니어인 'Rough Watercolor Artist'야.
사용자가 한글로 입력한 내용을 투박하면서도 예술적인 '거친 수채화풍' 영어 프롬프트로 변환해 줘.

[수채화풍 작성 전략]
1. 거친 기법: 거친 붓터치(Rough brushstrokes), 가공되지 않은 느낌(Raw aesthetic), 대담한 표현을 포함해.
2. 질감: 거친 질감의 수채화지(Rough-textured watercolor paper), 눈에 띄는 종이의 결, 물감의 얼룩(Splatter, stains)을 강조해.
3. 색감: 맑기보다는 힘 있는 색감, 에너지가 느껴지는 거친 색채 대비를 사용해.
4. 마스터 키워드: Watercolor painting, rough brushstrokes, expressive style, textured paper, raw watercolor, splattered paint를 위주로 사용해.

[출력 규칙]
- 맑은(Clean), 정제된(Refined), 부드러운(Soft) 느낌의 단어는 최소화하거나 빼.
- 한국어 설명 없이 콤마(,)로 구분된 영어 키워드만 출력해.

[한국어 입력]
{text}

[생성된 프리미엄 수채화 프롬프트]
"""

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt
        )
        return response.text.strip()
    except Exception as e:
        return f"에러 발생: {str(e)}"

def main():
    print("==========================================")
    print("🎨 한글 -> 영어 이미지 프롬프트 변환기")
    print("==========================================")
    print("종료하려면 'q'를 입력하세요.\n")

    while True:
        user_input = input("📝 한글 묘사 입력: ").strip()
        
        if user_input.lower() in ['q', 'exit', 'quit', 'ㅂ']:
            print("👋 종료합니다.")
            break
            
        if not user_input:
            continue

        print("🔍 변환 중...")
        english_prompt = translate_prompt(user_input)
        print(f"\n✨ [영어 프롬프트]:")
        print(f"{english_prompt}\n")
        print("-" * 40)

if __name__ == "__main__":
    main()

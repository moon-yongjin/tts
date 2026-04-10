import google.generativeai as genai
import json
import os

def load_api_key():
    key_path = "/Users/a12/projects/tts/core_v2/api_keys.json"
    with open(key_path, 'r') as f:
        keys = json.load(f)
    return keys.get("GEMINI_API_KEY_1")

def generate_scripts():
    api_key = load_api_key()
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.0-flash')

    prompt = """
너는 대한민국 최고의 '막장 드라마' 작가이자, 시니어들의 마음을 꿰뚫어 보는 스타 유튜버 대본 작가야. 
기존의 뻔한 '병 걸려 화해하기' 같은 식상한 클리셰는 던져버리고, 시청자들이 "어머, 세상에!"를 외치다 마지막엔 손수건을 적시게 만드는 대본 10편을 작성해줘.

### 핵심 요구사항:
1. **극적인 갈등(막장)**: 대사가 아주 찰지고 매서워야 해. (예: "너 같은 게 감히 우리 집 대문을 넘봐?", "돈 냄새 맡고 온 것들 아니야!")
2. **반전과 감동**: 단순히 미안하다고 끝나는 게 아니라, 숨겨진 희생이나 예상치 못한 진심이 드러나는 '통쾌한 반전' 혹은 '가슴 먹먹한 반전'을 넣어줘.
3. **캐릭터의 깊이**: 
   - 시어머니: 그냥 악독한 게 아니라 '가문을 지키려는 독기'가 있어야 함.
   - 며느리: 무조건 당하지 않고, 할 말은 하거나 혹은 가장 밑바닥에서 버티는 강인함. 독기 품은 반격이 있어도 좋음.
   - 시장 상인, 회장님 등: 현실감 넘치는 사투리나 전문 용어(주식, 땅, 권리금 등)를 적절히 섞어줘.
4. **구성**: 각 편당 등장인물은 3명 고정.
5. **분량**: 에피소드당 공백 포함 1100자 정도의 풍성한 대화와 지문.
6. **포맷**: 
   [캐릭터이름]: 대사
   (감정/행동 지문)

### 에피소드 테마 예시 (이걸 참고하되 더 기발하고 맵게):
- '며느리가 숨겨둔 100억 통장의 비밀 - 사실은 시어머니 노후 자금이었다?'
- '치매인 줄 알았던 어머니가 매일 시장 바닥에서 구걸한 소름 돋는 이유'
- '시장 파지 줍는 할매가 알고 보니 강남 건물주?'
- '아들이 버린 줄 알았던 아버지의 낡은 일기장 - 그 속에 적힌 30년 전의 피눈물'

전체 10편을 하나의 텍스트 파일 형식으로 출력해줘. 각 에피소드 사이에는 --- 구분선을 넣어줘.
"""

    response = model.generate_content(prompt)
    
    output_path = "/Users/a12/projects/tts/generated_makjang_scripts_v2.txt"
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(response.text)
    
    print(f"✅ 성공: 업그레이드된 대본 10편이 {output_path}에 저장되었습니다.")

if __name__ == "__main__":
    generate_scripts()

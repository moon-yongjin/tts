import requests
import json
import sys
import os
import re

# [설정]
OLLAMA_API = "http://localhost:11434/api/generate"
MODEL = "qwen2.5-coder:7b"

# 사용 가능한 목소리 풀
VOICE_CATALOG = {
    "Supertone": [
        {"id": "chloe", "name": "클로이", "desc": "20-30대 여성, 감성적, 맑은 목소리"},
        {"id": "taeyang", "name": "태양", "desc": "30-40대 남성, 신뢰감 있는 성우 톤"}
    ],
    "Azure": [
        {"id": "ko-KR-JiMinNeural", "name": "지민", "desc": "뉴스/다큐 나레이션 최적화"},
        {"id": "ko-KR-InJoonNeural", "name": "인준", "desc": "중후한 남성 나레이션"},
        {"id": "ko-KR-SunHiNeural", "name": "선히", "desc": "발랄한 어린아이/소녀"}
    ],
    "Qwen": [
        {"id": "qwen_local", "name": "로컬 퀜", "desc": "독특한 개성파/악역 캐릭터"}
    ]
}

def ask_ollama(prompt):
    payload = {"model": MODEL, "prompt": prompt, "stream": False}
    try:
        response = requests.post(OLLAMA_API, json=payload)
        return response.json().get('response', '')
    except Exception as e:
        return f"Error: {e}"

def generate_casting_sheet(script_text):
    print("🎭 캐스팅 디렉터가 배역에 어울리는 목소리를 고르고 있습니다...")
    
    prompt = f"""너는 세계 최고의 오디오 드라마 캐스팅 디렉터야. 아래 대본을 분석해서 각 등장인물(나레이션 포함)에게 가장 잘 어울리는 목소리를 매칭해줘.

### 대본 내용:
{script_text}

### 사용 가능한 목소리 카탈로그:
{json.dumps(VOICE_CATALOG, ensure_ascii=False, indent=2)}

### 매칭 규칙:
1. **나레이션**: 신뢰감 있는 Azure 목소리 권장.
2. **주연(감정 중요)**: Supertone 목소리(클로이/태양) 권장.
3. **조연/악역**: 개성 있는 Qwen이나 Azure의 다른 톤 매칭.
4. **결과 형식**: 
   - 반드시 JSON 형식으로만 출력해.
   - 포맷: {{"캐릭터명": {{"engine": "엔진명", "voice_id": "아이디", "reason": "선택 이유"}}}}

오직 JSON 데이터만 출력해."""

    result = ask_ollama(prompt)
    
    # JSON 추출 시도
    try:
        json_match = re.search(r'\{.*\}', result, re.DOTALL)
        if json_match:
            casting_data = json.loads(json_match.group())
            output_path = "casting_sheet.json"
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(casting_data, f, ensure_ascii=False, indent=2)
            print(f"✅ 캐스팅 완료! 결과가 {output_path}에 저장되었습니다.")
            return casting_data
    except Exception as e:
        print(f"❌ 캐스팅 결과 분석 실패: {e}")
        print("감독관의 원본 응답:", result)
        return None

if __name__ == "__main__":
    if len(sys.argv) > 1:
        with open(sys.argv[1], 'r', encoding='utf-8') as f:
            script = f.read()
        generate_casting_sheet(script)
    else:
        print("사용법: python casting_agent.py [대본파일.txt]")

import requests
import json
import sys

# [설정]
OLLAMA_API = "http://localhost:11434/api/generate"
MODEL = "qwen2.5-coder:7b"

def ask_ollama(prompt):
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False
    }
    try:
        response = requests.post(OLLAMA_API, json=payload)
        return response.json().get('response', '')
    except Exception as e:
        return f"Error: {e}"

def generate_visual_prompts(script_text):
    print("🎨 각 장면에 맞는 최적의 이미지 프롬프트를 생성 중입니다...")
    
    prompt = f"""너는 세계 최고의 AI 영상 연출가이자 프롬프트 엔지니어어. 아래 대본을 읽고, 각 주요 장면을 위한 ComfyUI/Flux 전용 이미지 생성 프롬프트를 작성해줘.

### 대본 내용:
{script_text}

### 작성 규칙:
1. **장면 분할**: 대본의 흐름에 따라 4~6개의 핵심 장면으로 나눌 것.
2. **스타일**: 실사 영화 스타일 (Photorealistic, Cinema 4D, 8k, highly detailed).
3. **프롬프트 언어**: **반드시 영문(English)**으로 작성할 것.
4. **구성요소**: 각 장면마다 [장면 설명 - 한글]과 [Prompt - 영문]을 세트로 출력해줘.
5. **특징**: 인물의 감정(분노, 눈물, 놀람), 조명, 배경 분위기가 잘 드러나도록 매우 상세하게 묘사할 것.

오직 장면 설명과 영어 프롬프트만 출력해줘."""

    result = ask_ollama(prompt)
    print("\n[AI 연출가의 비주얼 가이드]")
    print(result)
    return result

if __name__ == "__main__":
    if len(sys.argv) > 1:
        with open(sys.argv[1], 'r', encoding='utf-8') as f:
            script = f.read()
        generate_visual_prompts(script)
    else:
        print("사용법: python scene_prompt_designer.py [대본파일.txt]")

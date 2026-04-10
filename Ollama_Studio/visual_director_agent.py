import requests
import json
import sys
import os

OLLAMA_API = "http://localhost:11434/api/generate"
MODEL = "qwen2.5-coder:7b"

def ask_ollama(prompt):
    payload = {"model": MODEL, "prompt": prompt, "stream": False}
    try:
        response = requests.post(OLLAMA_API, json=payload)
        return response.json().get('response', '')
    except Exception as e:
        return f"Error: {e}"

def report_visual_settings(script_text):
    print("🎭 비주얼 디렉터가 장면 연출을 설계 중입니다...")
    
    prompt = f"""너는 세계적인 영상미를 자랑하는 영화 감독이자 비주얼 아트 디렉터야. 
아래 대본을 바탕으로 영상의 '비주얼 컨셉'과 '장면 설정 보고서'를 작성해줘.

### 대본:
{script_text}

### 보고서 필수 항목:
1. **전체 룩앤필 (Look & Feel)**: 조명, 색감(Color Palette), 질감(Texture). 
   - 예: "고풍스러운 70년대 시골 필름 느낌, 따스한 오후 햇살의 오렌지톤"
2. **카메라 워킹**: 각 장면의 앵글 (Close-up, Wide shot, Low angle 등).
3. **인물 스타일링**: 옷차림, 표정의 디테일.
4. **이미지 생성 전략**: Flux나 Midjourney에서 사용할 핵심 키워드 조합.

국장님께 보고하듯이 정중하고 전문적인 톤으로 작성해줘."""

    result = ask_ollama(prompt)
    print("\n[비주얼 디렉터의 보고서]")
    print(result)

    # 결과를 파일로 저장 (텔레그램 게이트웨이에서 읽어갈 수 있도록)
    with open("visual_report.txt", "w", encoding="utf-8") as f:
        f.write(result)
        
    print(f"✅ 비주얼 보고서가 저장되었습니다: visual_report.txt")
    return result

if __name__ == "__main__":
    if len(sys.argv) > 1:
        with open(sys.argv[1], 'r', encoding='utf-8') as f:
            script = f.read()
        report_visual_settings(script)
    else:
        print("사용법: python visual_director_agent.py [대본파일.txt]")

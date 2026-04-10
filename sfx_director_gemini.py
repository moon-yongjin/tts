from google import genai
import json
import os

# [1] 설정
GEMINI_API_KEY = "AIzaSyDOtvWYJaFgSoOmDDQ77QO4i6RoFdWWuOA"
SRT_PATH = "/Users/a12/projects/tts/remotion-hello-world/public/final_promo_refined.srt"
OUTPUT_PATH = "/Users/a12/projects/tts/remotion-hello-world/public/sfx_config.json"

# 가용한 SFX 목록
SFX_LIST = [
    "fast_whoosh.mp3",
    "elevator_ding.mp3",
    "cinematic_boom.mp3",
    "glitch_static.mp3",
    "camera_shutter.mp3",
    "zipper_fast.mp3",
    "coin_drop.mp3",
    "keyboard_typing.mp3",
    "keyboard_mouse.mp3"
]

def run_sfx_director():
    client = genai.Client(api_key=GEMINI_API_KEY)
    
    with open(SRT_PATH, "r", encoding="utf-8") as f:
        srt_content = f.read()

    prompt = f"""
전략적 SFX 감독으로서 주어진 자막 파일(SRT)을 분석하여 고퀄리티 쇼츠(Shorts) 뉴스 영상을 위한 효과음 배치를 설계하세요. 

[가용한 효과음 목록]
{', '.join(SFX_LIST)}

[지침]
1. 전환(Swish): 문장이 바뀌는 지점 혹은 큰 문맥이 변할 때 'fast_whoosh.mp3' 또는 'zipper_fast.mp3'를 추천하세요.
2. 강조(Ding): 충격적인 숫자, 반도체 회사 이름(삼성, 엔비디아 등), 핵심 결론이 나올 때 'elevator_ding.mp3'를 추천하세요.
3. 데이터/캡처: 도표나 구체적인 수치가 제시될 때 'camera_shutter.mp3'를 쓰세요.
4. 위기/긴장: '삭감', '붕괴', '전쟁', '결핍' 같은 부정적이고 강렬한 단어가 나올 때 'glitch_static.mp3'를 쓰세요.
5. 테크/작업: PC 사양, 시스템 구축, DDR5, SSD 등 하드웨어 사양이나 작업 지시 관련 단어가 나올 때 'keyboard_typing.mp3' 또는 'keyboard_mouse.mp3'를 섞어 쓰세요.
6. 임팩트: 첫 시작 혹은 비디오 장면(8번, 19번 등)이 시작될 때 'cinematic_boom.mp3'를 쓰세요.
7. 너무 자주 넣지 말고(0.5초 간격 금지), 문맥상 가장 임팩트 있는 지점을 위주로 18~22개 정도 추천하세요.

[출력 형식]
반드시 아래와 같은 순수한 JSON 형식으로만 답변하세요. 마크다운 기호 없이 JSON 데이터만 출력하세요. 
각 효과음 포인트에 대해 해당 시점에 강조할 '말풍선/강조 자막용 단어'가 있다면 `highlight_text`에 넣으세요. 없으면 빈 문자열("")을 넣으세요.

[
  {{ 
    "timestamp": 3.379, 
    "sfx_file": "fast_whoosh.mp3", 
    "reason": "문장 전환",
    "highlight_text": "시장 격변!"
  }},
  {{ 
    "timestamp": 12.4, 
    "sfx_file": "elevator_ding.mp3", 
    "reason": "삼성전자 강조",
    "highlight_text": "삼성전자"
  }}
]

[SRT 데이터]
{srt_content}
"""

    print("🚀 Gemini (3-flash-preview)에게 효과음 디렉팅 요청 중...")
    response = client.models.generate_content(
        model='gemini-3-flash-preview',
        contents=prompt
    )
    
    try:
        # JSON 클리닝
        cleaned_text = response.text.replace("```json", "").replace("```", "").strip()
        sfx_config = json.loads(cleaned_text)
        
        with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
            json.dump(sfx_config, f, indent=2, ensure_ascii=False)
            
        print(f"✅ 효과음 설정 파일 생성 완료: {OUTPUT_PATH}")
        print(f"🎯 총 {len(sfx_config)}개의 효과음 포인트를 찾았습니다.")
        
    except Exception as e:
        print(f"❌ JSON 파싱 에러: {e}")
        print(f"원본 응답: {response.text}")

if __name__ == "__main__":
    run_sfx_director()

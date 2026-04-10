import os
import json
from mlx_lm import load, generate

# [설정] 초고속 Qwen 1.5B 주입 (모든 Mac에서 1초 만에 로드 및 생성 가능)
MODEL_ID = "mlx-community/Qwen2.5-1.5B-Instruct-4bit"
OUTPUT_JSON = "/Users/a12/projects/tts/core_v2/scenes_대본_auto_mlx.json"
SCRIPT_FILE = "/Users/a12/projects/tts/대본.txt"

# [가이드 프롬프트] 허깅(AI) 분석 기반 고퀄리티 연출 생성용 시스템 프롬프트
SYSTEM_PROMPT = """당신은 틱톡/쇼츠 전문 AI 영상 감독입니다. 
전체 대본을 시간 순서에 따라 **서로 다른 4개의 장면(Scene)**으로 분할하고, 각 장면을 하단 JSON 규격으로 출력하세요.

반드시 답변에 JSON 배열([])만 포함시키고 다른 설명은 하지 마세요.

[예시 구조]
[
  {
    "narration": "해당 장면의 짧은 대사 한 줄 (한국어)",
    "visual_prompt": "Cinematic photography of [주요 대상 영문 묘사], ultra-detailed 8k, sharp focus, RAW photo"
  }
]
"""

def generate_scenes():
    if not os.path.exists(SCRIPT_FILE):
        print(f"❌ 대본 파일을 찾을 수 없습니다: {SCRIPT_FILE}")
        # 기본 예시 대본 주입 (테스트용)
        with open(SCRIPT_FILE, 'w', encoding='utf-8') as f:
            f.write("모기가 당신의 피를 빠는 0.1초 동안 벌어지는 세포 레벨의 물리적 사냥")

    with open(SCRIPT_FILE, 'r', encoding='utf-8') as f:
        script_content = f.read().strip()

    print(f"🚀 [MLX-LM] 애플 실리콘 네이티브 가동 시작... (모델: {MODEL_ID})")
    try:
        model, tokenizer = load(MODEL_ID)
    except Exception as e:
        print(f"❌ 모델 로드 실패: {e}\n💡 'pip install mlx-lm'이 온전히 설치되었는지 확인하세요.")
        return

    # 대화형 템플릿 적용 (Instruct 호환)
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"다음 대본을 4개 장면의 비주얼 연출 프롬프트 객체로 변형해라:\n\n{script_content}"}
    ]
    formatted_prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)

    print("⏳ [MLX-LM] 고퀄리티 비주얼 씬(Scene) 생성 중...")
    try:
        response = generate(
            model, 
            tokenizer, 
            prompt=formatted_prompt, 
            max_tokens=2048, 
            verbose=True
        )
        
        # JSON 블록만 추출
        json_match = response.split('[', 1)
        if len(json_match) > 1:
            json_str = '[' + json_match[1].rsplit(']', 1)[0] + ']'
            parsed_json = json.loads(json_str)
            
            # 파일 자동 저장
            with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
                json.dump(parsed_json, f, indent=2, ensure_ascii=False)
            
            print(f"\n✅ [MLX-LM] 생성 성공! 파일 저장됨: {OUTPUT_JSON}")
            print("👉 이제 귀하의 자동화 코드에 이 파일을 연결해 돌리시면 됩니다.")
        else:
             print(f"❌ 에러: 응답이 JSON 형식이 아닙니다.\n{response}")

    except Exception as e:
        print(f"❌ 생성 실패: {e}")

if __name__ == "__main__":
    generate_scenes()

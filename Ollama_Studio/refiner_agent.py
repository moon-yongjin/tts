import os
import sys
from pathlib import Path
from llm_router import ask_llm

# [설정]
PROJ_ROOT = Path("/Users/a12/projects/tts")
OLLAMA_STUDIO_ROOT = PROJ_ROOT / "Ollama_Studio"

def refine_script(file_path):
    if not os.path.exists(file_path):
        return

    print(f"✨ [Refiner] 제미나이의 공감 능력과 '따뜻한 사연 작가' 스킬로 대본을 교정 중...")
    
    # [스킬 로드]
    skill_path = OLLAMA_STUDIO_ROOT / "skills/warm-story-writer/SKILL.md"
    skill_content = ""
    if skill_path.exists():
        with open(skill_path, "r", encoding="utf-8") as f:
            skill_content = f.read()

    with open(file_path, "r", encoding="utf-8") as f:
        script = f.read()

    prompt = f"""너는 대한민국 실버 세대(60대 이상)의 마음을 가장 잘 이해하는 '최고의 번역가이자 감동 사연 전문 작가'야.
아래의 [영어 초안 대본]을 한국 어르신들이 깊이 공감할 수 있도록 **찰지게 초월 번역 및 교정**해줘.

### 🌸 [초월 번역 및 교정 지침]
1. 단순 번역 금지. 할머니, 할아버지가 들었을 때 눈시울이 붉어지도록 한국적인 정서, 향토적인 단어, 다정한 구어체를 적극 사용해.
2. 부모님, 자식, 이웃 간의 끈끈한 정이 느껴지도록 대사와 지문을 정겹게 다듬어.
3. 자극적이거나 비현실적인 반전(초능력 등)은 모두 제거해.
4. {skill_content}

### [영어 초안 대본]
{script}

⚠️ **주의**: 대본의 총 길이는 공백 포함 **1,000자 이내**로 맞춰주세요. 오직 실제 연기용 '한국어 대본 전문'만 처음부터 끝까지 출력하고, 불필요한 줄거리 요약이나 해설은 절대 출력하지 마세요."""

    refined_script = ask_llm(prompt, role="refiner")
    
    if refined_script and "Error" not in refined_script:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(refined_script)
        print("✅ [Refiner] 제미나이 기반 대본 교정이 완료되었습니다.")
    else:
        print(f"❌ [Refiner] 교정 실패: {refined_raw}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        refine_script(sys.argv[1])
    else:
        print("사용법: python refiner_agent.py [file_path]")

import sys
import os
import random
from pathlib import Path
from llm_router import ask_llm

# [설정]
PROJ_ROOT = Path("/Users/a12/projects/tts/Ollama_Studio")

# [마케팅 아이템 풀]
PPL_ITEMS = [
    {"name": "산삼 장어 진액", "feature": "기력 회복, 30대부터 필수", "target": "중장년층"},
    {"name": "내 차 시세 확인 앱 '차팔자'", "feature": "1분 만에 최고가 견적", "target": "운전자"},
    {"name": "비과세 복리 저축 보험", "feature": "노후 보장, 복리의 마법", "target": "미래 설계"},
    {"name": "프리미엄 한우 선물 세트", "feature": "감사한 마음을 전할 때", "target": "명절/선물"},
    {"name": "초강력 탈모 샴푸 '모발모발'", "feature": "뿌리부터 튼튼하게", "target": "모발 고민"}
]

def add_marketing_and_humor(file_path):
    if not os.path.exists(file_path):
        return

    print(f"💰 [Marketing] '{file_path}'에 PPL과 유머를 딥시크로 찰지게 섞는 중...")
    with open(file_path, "r", encoding="utf-8") as f:
        script = f.read()

    item = random.choice(PPL_ITEMS)
    
    style_example = """
    "자, 다음 이야기는 이 청년이 진짜 실력을 보여줄 때야. 
    '이건 AI가 만든 세상이야, 너는 뭐라고 생각하니?' 
    댓글 2번 눌러서 '파트2'로 들어와! 
    아참, 기력 딸리면 '산삼 장어 진액' 한 잔 들이키고 오라고!"
    """

    prompt = f"""너는 대한민국 최고의 '마케팅 팀장'이자 '감동 드라마 작가'야. 
기존 대본의 마지막에 **따뜻한 권유형 PPL**과 **마음 훈훈해지는 한마디**, 그리고 **시청자 소통**을 추가해줘.

### 📋 마케팅 미션:
1. **PPL 상품**: {item['name']} ({item['feature']})
2. **스타일 지침**: 자극적인 개그가 아닌, 사연의 감동을 이어가며 상품을 따뜻하게 추천해. 
   예: "부모님께 효도하고 싶을 땐 이런 게 참 좋더군요."
3. **규칙**:
   - 기존 대본의 따뜻한 분위기를 해치지 말고 자연스럽게 이어붙여.
   - 이름 태그([누구]:) 사용 금지. 대사만 따옴표("") 처리.
   - 시청자가 자신의 부모님이나 소중한 사람을 떠올리게 하는 문구 삽입.

### 기존 대본:
{script}

설명 없이 수정 및 추가된 **'대본 전체 내용'**만 출력해."""

    try:
        final_script = ask_llm(prompt, role="marketing")
        
        if not final_script or "Error" in final_script:
            print("❌ 마케팅 추가 실패: Ollama 응답 없음")
            return

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(final_script)
            
        print(f"✅ [Marketing Manager] '{item['name']}' PPL과 유머가 추가되었습니다.")
    except Exception as e:
        print(f"❌ 마케팅 추가 실패: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        add_marketing_and_humor(sys.argv[1])
    else:
        print("사용법: python marketing_manager_agent.py [file_path]")

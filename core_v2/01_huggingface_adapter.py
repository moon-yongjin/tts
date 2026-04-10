import os
import sys
from pathlib import Path

# Add project root to path for imports
PROJ_ROOT = Path("/Users/a12/projects/tts")
sys.path.append(str(PROJ_ROOT))

try:
    from Ollama_Studio.llm_router import ask_huggingface
except ImportError:
    print("❌ llm_router import failed.")
    sys.exit(1)

def main():
    script_path = "/Users/a12/Downloads/Shorts_Scrape_0315_2147/nS1gGZz2e_A_120kg_뚱녀와_결혼한_아들을_비웃는_사람들_대본.txt"
    if not os.path.exists(script_path):
        print(f"❌ 파일이 없습니다: {script_path}")
        return

    with open(script_path, "r", encoding="utf-8") as f:
        original_text = f.read().strip()

    print("🧠 Consulting 'Hugging Model' to adapt the script...")
    
    question = f"""
!!! 중요 !!! [필수 조건] !!! 중요 !!!
당신은 한국어 숏폼 대본 전문 작가입니다. 
**답변의 모든 문장(Screen, Narration 포함)과 연출 메모는 100% 한국어(Korean)로만 출력해야 합니다.**
절대로 영어(English)를 혼용하지 마세요.

---
다음은 유튜브 쇼츠로 각색할 신규 사연의 개요입니다.
이 사연을 더 몰입감 넘치고, 시청 이탈률이 낮으며, 결말의 감동과 반전이 극대화되도록 각색주세요.

[사연 기획 개요]
- **초반 갈등**: "평생 걷지 못하는 휠체어 신부"라며 시누이와 하객들이 결혼을 반대하고 비웃음.
- **중반 빌드업**: 아들만 유일하게 그녀의 아픔을 감싸주며 진심으로 사랑함.
- **클라이맥스 (반전)**: 결혼식 직후 또는 시댁 위기 순간에 며느리가 **휠체어에서 벌떡 일어남**.
- **진실**: 다리가 멀쩡하지만, **'내 돈이 아닌 내 휠체어(약점)를 감싸줄 진짜 사랑'**을 시험하기 위해 수년간 연기해 온 수백억대 부자(기업가) 상속녀.

[각색 조건]
1. 숏폼(틱톡, 릴스, 쇼츠) 포맷에 맞게 60초 내로 끝나는 타이트한 호흡
2. 초반 3초에 시청자를 사로잡는 강력한 후킹(Hook) 멘트
3. 중간에 시각적(화면) 상상을 자극하는 간결한 화면 묘사 배치 (예: [화면: ...])
4. 마지막에 여운을 줄 수 있는 뼈 때리는 반전 멘트 보강
5. 모든 나레이션 및 연출 대본은 100% 한국어(Korean)로 작성해 주세요.
"""

    try:
        answer = ask_huggingface(question)
        print("\n📜 --- Hugging Model's Adapted Script ---")
        print(answer)
        print("------------------------------------------\n")
        
        output_path = "/Users/a12/Downloads/Shorts_Scrape_0315_2147/120kg_뚱녀_각색대본_허깅.txt"
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(answer)
        print(f"✅ 각색 대본 저장 완료: {output_path}")
            
    except Exception as e:
        print(f"❌ 각색 요청 실패: {e}")

if __name__ == "__main__":
    main()

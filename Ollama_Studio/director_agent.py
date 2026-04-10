import requests
import json
import sys
import os
from pathlib import Path
from llm_router import ask_llm

# [설정]
PROJ_ROOT = Path("/Users/a12/projects/tts/Ollama_Studio")
STYLE_BIBLE_PATH = PROJ_ROOT / "style_bible.txt"
SKILL_PATH = PROJ_ROOT / "skills/warm-story-writer/SKILL.md"

TELEGRAM_TOKEN = "8515076340:AAHp4TH200xUzO5i9MeSbBSeX9K2hlJbg80"
TELEGRAM_CHAT_ID = "7793202015"

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Telegram Error: {e}")

def review_script(script_text):
    print(f"🧐 [Local Director] LLM Router (다중 모델) 엔진이 대본을 검토 중입니다...")
    
    # 스타일 바이블 및 스킬 읽기
    style_bible = ""
    if STYLE_BIBLE_PATH.exists():
        with open(STYLE_BIBLE_PATH, 'r', encoding='utf-8') as f:
            style_bible = f.read()
            
    skill_content = ""
    if SKILL_PATH.exists():
        with open(SKILL_PATH, 'r', encoding='utf-8') as f:
            skill_content = f.read()

    prompt = f"""너는 대한민국 실버 세대의 마음을 가장 잘 이해하는 베테랑 방송 작가이자 총감독(PD)이야. 
로컬 AI가 작성한 [초안 대본]을 아래 [성공 공식]과 [따뜻한 사연 작가 스킬]을 기준으로 정밀하게 검토해.

### 🌸 [따뜻한 사연 작가 스킬]
{skill_content}

### 📖 [성공 공식 (Style Bible)]
{style_bible}

### 📝 [작가의 대본]
{script_text}

### 📋 검토 및 채점 항목 (각 10점 만점):
1. **감동 지수 (Empathy)**: 사연이 가슴을 울리는가? 무리한 설정 없이 자연스러운가?
2. **현실성 & 공감도 (Relatability)**: 60대 이상 어르신들이 "맞아, 저랬지" 하고 고감할 만한 일상인가?
3. **가독성 & 정겨움 (Format)**: 국장님 전용 요약 포맷을 준수하며 말투가 정겨운가?
4. **여운 (Aftertaste)**: 마지막에 깊은 생각이나 따뜻한 교훈을 남기는가?

### 출력 양식:
1. **[총감독의 따뜻한 성적표]**: 항목별 점수 및 총점 (40점 만점)
2. **[종합 총평]**: 대본의 정서적 깊이와 시장성에 대한 평가.
3. **[필수 수정 사항]**: 더 큰 감동을 주기 위해 딱 한 부분만 더 정겹게 고친다면?

설명 없이 오직 위 양식대로만 출력해."""

    result = ask_llm(prompt, role="director")
    
    print("\n[감독관의 검토 보고서]")
    print(result)

    # 보고서 파일 저장 (통합 결재용)
    with open("director_report.txt", "w", encoding="utf-8") as f:
        f.write(result)

    # 텔레그램 보고 발송
    report_msg = f"🎬 <b>총감독의 대본 검토 보고 (Local/DeepSeek)</b>\n\n{result}\n\n국장님, 대본 검토가 완료되었습니다! 🫡"
    send_telegram(report_msg)
    
    return result

if __name__ == "__main__":
    if len(sys.argv) > 1:
        with open(sys.argv[1], 'r', encoding='utf-8') as f:
            script = f.read()
        review_script(script)
    else:
        print("사용법: python director_agent.py [대본파일.txt]")

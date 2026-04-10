import json
import os
import sys
import time
import random
import re
import requests
from pathlib import Path
from llm_router import ask_llm

# [설정]
PROJ_ROOT = Path("/Users/a12/projects/tts/Ollama_Studio")
OUTPUT_FILE = PROJ_ROOT / "야담과개그_신규대본_1편.txt"
STYLE_BIBLE_PATH = PROJ_ROOT / "style_bible.txt"
HISTORY_FILE = PROJ_ROOT / "script_history.json"

def load_history():
    if HISTORY_FILE.exists():
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except: return []
    return []

def save_history(topic):
    history = load_history()
    history.append({"timestamp": time.strftime("%Y-%m-%d %H:%M:%S"), "topic": topic})
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history[-50:], f, ensure_ascii=False, indent=2)

def clean_text_for_tts(text):
    # DeepSeek 생각 태그 제거 등
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL).strip()
    return text

def brainstorm_topic():
    print("🧠 [Brainstorming] 딥시크가 새로운 감동 소재를 구상 중입니다...")
    history = load_history()
    recent = [h['topic'] for h in history[-5:]]
    exclusion = f"\n(참고: 최근 소재 '{', '.join(recent)}'와 겹치지 않게 할 것)" if recent else ""
    
    prompt = f"""너는 대한민국 최고의 '따뜻한 감동 사연' 기획자야. 
60대 이상 시청자들이 깊이 공감하고 눈물 흘릴만한 **현실적이고 따뜻한 소재**를 하나 추천해줘.
{exclusion}

### 소재 선정 기준:
- 자극적인 반전이나 초능력 금지.
- 부모님, 자식, 이웃, 그리운 고향 등 정겨운 가치 강조.
- 10자 내외의 짧은 제목 형태로 출력해.

추천 소재:"""
    
    topic = ask_llm(prompt, role="brainstorm")
    # 정규식으로 따옴표 등 제거
    topic = re.sub(r'["\']', '', topic).strip()
    return topic

def generate_masterpiece(feedback=""):
    print(f"🎨 [Writer] 다중 모델 엔진으로 고퀄리티 집필을 시작합니다...")
    
    # [따뜻한 사연 작가 스킬 로드]
    skill_path = PROJ_ROOT / "skills/warm-story-writer/SKILL.md"
    skill_content = ""
    if skill_path.exists():
        with open(skill_path, "r", encoding="utf-8") as f:
            skill_content = f.read()

    style_bible = ""
    if STYLE_BIBLE_PATH.exists():
        with open(STYLE_BIBLE_PATH, "r", encoding="utf-8") as f:
            style_bible = f.read()

    # 동적 소재 생성
    topic = brainstorm_topic()
    if not topic: topic = "정체를 숨긴 회장님의 처절한 복수극"
    print(f"💡 선택된 소재: {topic}")

    feedback_instruction = ""
    if feedback:
        feedback_instruction = f"\n\n### [국장님 긴급 지시사항]\n반드시 반영할 것: {feedback}\n"

    prompt = f"""You are the absolute best 'heartwarming script writer'. 
Write a deeply moving script based on the topic: '{topic}'.
Follow the [Warm Story Writer Skill] and [Success Formula] below.

CRITICAL INSTRUCTION: You MUST write the ENTIRE script in ENGLISH. Do not use Korean. 

### 🌸 [Warm Story Writer Skill]
{skill_content}

### [Success Formula]
{style_bible}

{feedback_instruction}

⚠️ **WARNING**: 
- Never output plot summaries or explanations. 
- The total length of the script must be under 300 words. 
- Output ONLY the actual script for acting from start to finish.
- Write in ENGLISH.

Script Start:"""

    script_raw = ask_llm(prompt, role="writer")
    script = clean_text_for_tts(script_raw)
    
    if not script or "Error" in script:
        print(f"❌ 생성 실패: {script}")
        return False

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(script)
    
    # 01-3-8 엔진 호환을 위해 상위 폴더에도 복사
    with open(Path("/Users/a12/projects/tts/대본.txt"), "w", encoding="utf-8") as f:
        f.write(script)
        
    save_history(topic)
    print(f"✨ 마스터피스 대본 탄생: {OUTPUT_FILE}")
    return True

if __name__ == "__main__":
    feedback_str = sys.argv[1] if len(sys.argv) > 1 else ""
    generate_masterpiece(feedback_str)

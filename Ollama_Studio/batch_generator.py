import requests
import time
import os
import random
import re
import json
from pathlib import Path

# 설정
OLLAMA_API = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "deepseek-r1:latest" # 초안 작가
BRAIN_MODEL = "qwen2.5-coder:7b"     # 기획 작가 (브레인스토밍)
PROJ_ROOT = Path("/Users/a12/projects/tts/Ollama_Studio")
DOWNLOADS_DIR = Path.home() / "Downloads"
GEMINI_SH = "/Users/a12/projects/tts/gemini.sh"
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
    history.append({
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "topic": topic
    })
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history[-50:], f, ensure_ascii=False, indent=2)

def clean_script(text):
    if "<think>" in text:
        text = text.split("</think>")[-1].strip()
    text = re.sub(r'[▄▀█─╭╮╰╯│●○]+', '', text)
    text = text.replace("Antigravity to Gemini CLI?", "").replace("Type your message", "").strip()
    return text

def ask_ollama(prompt, model=BRAIN_MODEL):
    """로컬 Ollama API 호출 (requests 방식)"""
    payload = {"model": model, "prompt": prompt, "stream": False}
    try:
        response = requests.post(OLLAMA_API, json=payload, timeout=300)
        return clean_script(response.json().get('response', ''))
    except Exception as e:
        print(f"❌ Ollama API 호출 실패: {e}")
        return ""

def brainstorm_topics(count=3):
    print(f"🧠 [Brainstorming] {BRAIN_MODEL}이(가) 신선한 마라맛 소재를 기획 중입니다...")
    history = load_history()
    recent_topics = [h['topic'] for h in history[-10:]]
    
    exclusion_prompt = ""
    if recent_topics:
        exclusion_prompt = f"\n참고: 최근에 '{', '.join(recent_topics)}'와 비슷한 소재는 이미 사용했으니 절대 중복되지 않게 해줘."

    prompt = f"""너는 대한민국 최고의 막장 드라마 기획자야. 틱톡과 유튜브 쇼츠에서 조회수 100만이 보장되는, 도파민 폭발하는 '쇼킹한 대본 소재'를 {count}개만 제안해줘.
예시: '사실은 친딸이 아니었던 재벌가 며느리의 복수', '죽은 줄 알았던 남편이 헬기 타고 나타난 불륜 현장' 등{exclusion_prompt}

각 소재는 한 줄로 짧고 강렬하게 적어줘. 앞에 숫자(1., 2.)를 붙여서 출력해. 말이나 군더더기 없이 오직 리스트만 출력해."""
    
    suggestions = ask_ollama(prompt)
    topics = re.findall(r'\d\.\s*(.*)', suggestions)
    return topics if topics else ["출생의 비밀과 처절한 복수극"]

def run_batch(num_scripts=2):
    print(f"🚀 [START] 다이나믹 막장 대본 생성 루프 가동 (기획:{BRAIN_MODEL} -> 집필:{OLLAMA_MODEL})")
    
    topics = brainstorm_topics(num_scripts)
    
    for i, topic in enumerate(topics[:num_scripts]):
        print(f"\n🎬 [{i+1}/{num_scripts}] 차례: '{topic}'")
        
        # 1. 초안 생성
        print(f"   - [초안] '{topic}' 주제로 Ollama 집필 중...")
        prompt_raw = f"'{topic}' 주제를 바탕으로 1500자 이상의 한국어 막장 대본을 써줘. 주인공의 굴욕, 반전, 사이다 응징이 포함되어야 해. 1막/2막 소제목을 넣어서 상세하게 묘사해."
        raw_script = ask_ollama(prompt_raw, model=OLLAMA_MODEL)
        
        if not raw_script:
            print("   ⚠️ 초안 생성 실패. 건너뜁니다.")
            continue

        # 2. Gemini 정제
        print(f"   - [정제] Gemini로 대사 톤 강화 중...")
        prompt_refine = (
            "아래 대본에서 소제목을 삭제하고, 실제 한국 드라마 작가가 쓴 것처럼 찰진 대사 위주로 다듬어주세요.\n"
            "마지막에는 시청자의 참여를 유도하는 쇼킹한 질문을 하나 던지세요.\n"
            f"내용:\n{raw_script}"
        )
        try:
            refine_res = subprocess.run([GEMINI_SH, prompt_refine], capture_output=True, text=True, timeout=120)
            final_script = clean_script(refine_res.stdout)
        except:
            print("   ⚠️ Gemini 호출 실패. 초안을 그대로 사용합니다.")
            final_script = raw_script
        
        # 3. 저장
        timestamp = time.strftime("%m%d_%H%M")
        file_path = DOWNLOADS_DIR / f"Dopamine_Masterpiece_{timestamp}_{i+1}.txt"
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(final_script)
            
        save_history(topic)
        print(f"   ✅ [저장 완료] {file_path}")

    print("\n✨ [SUCCESS] 모든 대본이 저장되었습니다!")

if __name__ == "__main__":
    run_batch(2)

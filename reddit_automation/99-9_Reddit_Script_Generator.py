import json
import os
from pathlib import Path
from google import genai

# [설정]
CONFIG_PATH = "/Users/a12/projects/tts/config.json"
SCRAPED_DIR = Path.home() / "Downloads" / "reddit_scraped"
MODEL_NAME = 'gemini-2.0-flash'

def load_gemini_key():
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            config = json.load(f)
            return config.get("Gemini_API_KEY")
    except:
        return None

def generate_haejon_script(title, comments):
    api_key = load_gemini_key()
    if not api_key:
        return "❌ API Key를 찾을 수 없습니다."

    client = genai.Client(api_key=api_key)
    
    prompt = f"""
당신은 지식, 미스터리, 신기한 현상 등을 다루는 유튜브 쇼츠 '해전학전' 채널의 메인 작가야.
제공된 [메타데이터]를 분석해서 한국 시청자를 첫 3초 만에 붙잡는 강력한 쇼츠 내레이션 대본을 작성해.

[작성 규칙]
1. 초강력 훅 (0~3초): 영상의 가장 핵심적인 사실이나 반전을 첫 문장으로 때릴 것.
2. 서론 생략: "안녕하세요", "신기하죠?" 같은 인사말 절대 금지. 바로 본론으로 돌입.
3. 베스트 댓글 활용: 사람들의 반응을 참고해 몰입감을 높일 것.
4. 말투: 건조하고 지적인 '~라고 하네요' 말투 사용.
5. 분량: 40~50초 분량 (공백 포함 300~500자 내외).

[메타데이터]
원본 제목: {title}
베스트 댓글:
{comments}

서론 없이 바로 대본 본문만 출력하세요.
"""

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt
        )
        return response.text.strip()
    except Exception as e:
        return f"에러 발생: {str(e)}"

def main():
    print("🎬 Reddit 영상 기반 '해전학전' 스타일 대본 생성기")
    
    # 1. 특정 파일 선택 (없으면 목록 보여줌)
    target_file = input("📄 대본을 만들 파일명(또는 키워드)을 입력하세요 (엔터 시 목록): ").strip()
    
    files = list(SCRAPED_DIR.glob("*_metadata.txt"))
    
    if target_file:
        selected_files = [f for f in files if target_file in f.name]
    else:
        selected_files = files

    if not selected_files:
        print("❌ 파일을 찾을 수 없습니다.")
        return

    for meta_path in selected_files:
        print(f"\n--- {meta_path.name} 분석 중 ---")
        
        with open(meta_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # 간단한 파싱
        lines = content.split("\n")
        title = lines[0].replace("제목: ", "")
        comments = "\n".join(lines[4:]) # 베스트 댓글 부분

        script = generate_haejon_script(title, comments)
        
        save_path = meta_path.with_name(meta_path.name.replace("_metadata.txt", "_대본.txt"))
        with open(save_path, "w", encoding="utf-8") as f:
            f.write(script)
            
        print(f"✅ 대본 생성 완료!")
        print(f"📄 저장 위치: {save_path}")
        print("-" * 30)
        print(script)
        print("-" * 30)

if __name__ == "__main__":
    main()

import os
import requests
import json
import subprocess
import time
from pathlib import Path
from google import genai

# --- [설정] ---
CONFIG_PATH = "/Users/a12/projects/tts/config.json"
DOWNLOAD_DIR = Path.home() / "Downloads" / "reddit_scraped"
MODEL_NAME = 'gemini-2.0-flash'

def load_gemini_key():
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            config = json.load(f)
            return config.get("Gemini_API_KEY")
    except:
        return None

def download_video(url, output_path):
    print(f"📥 영상 다운로드 중: {url}")
    cmd = [
        "yt-dlp",
        "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "-o", f"{output_path}.mp4",
        url
    ]
    try:
        subprocess.run(cmd, check=True)
        return True
    except Exception as e:
        print(f"❌ 다운로드 실패: {e}")
        return False

def get_metadata(post_url):
    print("🔍 메타데이터 및 댓글 추출 중...")
    # JSON 엔드포인트로 변환 (old.reddit.com 사용)
    json_url = post_url.rstrip('/') + "/.json"
    if "reddit.com" in json_url and "old.reddit.com" not in json_url:
        json_url = json_url.replace("www.reddit.com", "old.reddit.com")
        
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
    
    try:
        response = requests.get(json_url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            post_data = data[0]['data']['children'][0]['data']
            title = post_data['title']
            
            comments_data = data[1]['data']['children']
            comments = []
            for c in comments_data[:5]:
                if 'body' in c['data']:
                    comments.append(c['data']['body'])
            
            return title, "\n".join(comments)
    except Exception as e:
        print(f"❌ 메타데이터 추출 실패: {e}")
    return None, None

def generate_script(title, comments):
    print("✍️ AI 대본 생성 중 (해전학전 스타일)...")
    api_key = load_gemini_key()
    if not api_key: return "API Key 오류"

    client = genai.Client(api_key=api_key)
    prompt = f"""
당신은 유튜브 쇼츠 '해전학전' 채널의 메인 작가야. 
제공된 레딧 데이터로 한국 시청자를 3초 만에 훅킹하는 대본을 만들어.

[작성 규칙]
1. 첫 문장에 핵심이나 반전을 바로 던질 것.
2. 건조하고 지적인 '~라고 하네요' 말투.
3. 인사말, 서론 절대 금지.
4. 40~50초 분량.

[데이터]
제목: {title}
베스트 댓글: {comments}

대본 본문만 출력하세요.
"""
    try:
        response = client.models.generate_content(model=MODEL_NAME, contents=prompt)
        return response.text.strip()
    except Exception as e:
        return f"대본 생성 실패: {e}"

def main():
    if not os.path.exists(DOWNLOAD_DIR):
        os.makedirs(DOWNLOAD_DIR)

    print("\n🚀 [레딧 원스톱 원고 생성기] 실행")
    print("-" * 40)
    url = input("🔗 레딧 링크를 입력하세요: ").strip()
    
    if not url:
        print("URL이 입력되지 않았습니다.")
        return

    # 1. 메타데이터 추출
    title, comments = get_metadata(url)
    if not title:
        print("데이터를 가져올 수 없습니다. 링크를 확인하세요.")
        return

    # 파일명 안전하게 변환
    safe_title = "".join([c for c in title if c.isalnum() or c in (' ', '_', '-')]).rstrip()[:50]
    post_id = url.split('/')[-3] if '/' in url else "video"
    file_base = f"{safe_title}_{post_id}"
    save_path = DOWNLOAD_DIR / file_base

    # 2. 영상 다운로드
    if download_video(url, str(save_path)):
        # 3. 대본 생성
        script = generate_script(title, comments)
        
        # 4. 결과 저장
        with open(f"{save_path}_대본.txt", "w", encoding="utf-8") as f:
            f.write(f"--- 원본 데이터 ---\n제목: {title}\n링크: {url}\n\n--- 생성된 대본 ---\n\n{script}")
            
        print("\n" + "="*40)
        print(f"✅ 모든 작업 완료!")
        print(f"🎬 영상: {save_path}.mp4")
        print(f"📄 원고: {save_path}_대본.txt")
        print("="*40)
        print(f"\n[생성된 대본 맛보기]\n{script[:200]}...")
    else:
        print("실패했습니다.")

if __name__ == "__main__":
    main()

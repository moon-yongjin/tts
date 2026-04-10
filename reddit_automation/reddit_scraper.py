import os
import requests
import json
import subprocess
import time
from datetime import datetime

# --- 설정 ---
SUBREDDITS = [
    "interestingasfuck", "BeAmazed", "NextFuckingLevel", "satisfyingasfuck", 
    "Unexpected", "Damnthatsinteresting", "ScienceCoolStuff", "OddlySatisfying"
]
MIN_SCORE = 2000  # 인기 있는 것만 골라내기 위해 상향
LIMIT = 25        # 각 서브레딧당 더 많이 조회
TIME_FILTER = "month"  # 더 넓은 범위의 '레전드' 영상 수집
DOWNLOAD_DIR = os.path.expanduser("~/Downloads/reddit_scraped")
ARCHIVE_FILE = os.path.join(DOWNLOAD_DIR, "scraped_history.txt")

def download_reddit_video(url, output_path):
    print(f"다운로드 중: {url}")
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
        print(f"다운로드 실패: {e}")
        return False

def get_reddit_posts(subreddit, limit=LIMIT, time_filter=TIME_FILTER):
    url = f"https://old.reddit.com/r/{subreddit}/top/.json?t={time_filter}&limit={limit}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print(f"[{subreddit}] 오류 발생: {response.status_code}")
            return []
        
        data = response.json()
        return data['data']['children']
    except Exception as e:
        print(f"[{subreddit}] 데이터 요청 중 오류: {e}")
        return []

def scrape_metadata(post_url):
    # 포스트의 JSON 데이터를 가져와 베스트 댓글 추출
    url = f"{post_url.rstrip('/')}/.json"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            # data[0]은 포스트 정보, data[1]은 댓글 정보
            comments = data[1]['data']['children']
            top_comments = []
            for comment in comments[:3]: # 상위 3개 댓글
                if 'body' in comment['data']:
                    top_comments.append(comment['data']['body'])
            return top_comments
    except:
        return []
    return []

def run_scraper(subreddits=SUBREDDITS, limit=LIMIT, time_filter=TIME_FILTER):
    if not os.path.exists(DOWNLOAD_DIR):
        os.makedirs(DOWNLOAD_DIR)

    # 이미 다운로드한 목록 로드
    downloaded_ids = set()
    if os.path.exists(ARCHIVE_FILE):
        with open(ARCHIVE_FILE, "r", encoding="utf-8") as f:
            downloaded_ids = set(line.strip() for line in f if line.strip())

    for sub in subreddits:
        print(f"\n--- r/{sub} 수집 시작 ---")
        posts = get_reddit_posts(sub, limit, time_filter)
        
        for post in posts:
            p_data = post['data']
            post_id = p_data['id']
            
            # 중복 체크
            if post_id in downloaded_ids:
                continue

            score = p_data['score']
            is_video = p_data.get('is_video', False) or "v.redd.it" in p_data['url'] or "youtube.com" in p_data['url'] or "youtu.be" in p_data['url']

            if is_video and score >= MIN_SCORE:
                title = p_data['title']
                url = p_data['url']
                full_link = f"https://www.reddit.com{p_data['permalink']}"
                
                safe_title = "".join([c for c in title if c.isalnum() or c in (' ', '_', '-')]).rstrip()[:50]
                file_base_name = f"{sub}_{safe_title}_{post_id}"
                save_path = os.path.join(DOWNLOAD_DIR, file_base_name)
                
                print(f"발견: [{score}] {title}")
                
                if download_reddit_video(full_link, save_path):
                    comments = scrape_metadata(full_link)
                    with open(f"{save_path}_metadata.txt", "w", encoding="utf-8") as f:
                        f.write(f"제목: {title}\n")
                        f.write(f"추천수: {score}\n")
                        f.write(f"원문링크: {full_link}\n\n")
                        f.write("--- 베스트 댓글 ---\n")
                        for idx, c in enumerate(comments):
                            f.write(f"{idx+1}: {c}\n\n")
                    
                    # 히스토리에 추가
                    with open(ARCHIVE_FILE, "a", encoding="utf-8") as f:
                        f.write(f"{post_id}\n")
                    downloaded_ids.add(post_id)
                    
                    print(f"완료: {file_base_name}")
                
                time.sleep(1)

if __name__ == "__main__":
    run_scraper()

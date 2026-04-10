import os
import sys
import time
from pathlib import Path
from reddit_scraper import get_reddit_posts, download_reddit_video, scrape_metadata, DOWNLOAD_DIR, ARCHIVE_FILE

# --- [설정 및 카테고리] ---
CATEGORIES = {
    "1": {"name": "뷰티 & 모델 (PrettyGirls, GentlemanBoners, TikTokVideo)", "subs": ["PrettyGirls", "gentlemanboners", "TikTokVideo", "BetterEveryLoop"]},
    "2": {"name": "패션 & 스타일 (Outfits, Streetwear, Fashion)", "subs": ["outfits", "streetwear", "fashion"]},
    "3": {"name": "코스프레 & 아트 (Cosplay, ArtVideos)", "subs": ["cosplay", "ArtVideos"]},
    "4": {"name": "피트니스 & 역동적 (Fitness, Flexibility, Dance)", "subs": ["fitness", "flexibility", "dance", "OddlySatisfying"]},
    "5": {"name": "직접 검색 (서브레딧명 입력)", "subs": []}
}

TIME_FILTERS = {
    "1": "day",
    "2": "week",
    "3": "month",
    "4": "year",
    "5": "all"
}

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def main_menu():
    clear_screen()
    print("="*50)
    print(" 🎬 [인터랙티브 미디어 피커 v2] 🎬")
    print(" 원하는 카테고리를 선택하고 영상을 골라보세요.")
    print("="*50)
    for key, cat in CATEGORIES.items():
        print(f" [{key}] {cat['name']}")
    print(" [Q] 종료")
    print("-" * 50)
    return input("▶ 선택: ").strip().upper()

def time_menu():
    print("\n⏰ 검색 기간을 선택하세요:")
    print(" [1] 하루 (Day)")
    print(" [2] 이번 주 (Week)")
    print(" [3] 이번 달 (Month)")
    print(" [4] 올해 (Year)")
    print(" [5] 전체 기간 (All Time) - 결과가 가장 많음")
    choice = input("▶ 선택 (기본 5): ").strip() or "5"
    return TIME_FILTERS.get(choice, "all")

def get_target_subs(choice):
    if choice == "5":
        sub = input("🔍 조회할 서브레딧 이름을 입력하세요 (예: kpop): ").strip()
        return [sub] if sub else []
    return CATEGORIES.get(choice, {}).get("subs", [])

def pick_and_download():
    while True:
        choice = main_menu()
        if choice == 'Q':
            break
        
        subs = get_target_subs(choice)
        if not subs:
            print("❌ 유효하지 않은 선택입니다.")
            time.sleep(1)
            continue

        time_filter = time_menu()

        try:
            limit = int(input("🔢 몇 개의 게시물을 조회할까요? (기본 50): ") or 50)
        except ValueError:
            limit = 50

        all_posts = []
        print(f"\n🔍 r/{', '.join(subs)} ({time_filter}) 에서 데이터를 불러오는 중...")
        
        for sub in subs:
            posts = get_reddit_posts(sub, limit=limit, time_filter=time_filter)
            found_in_sub = 0
            for p in posts:
                p_data = p['data']
                url = p_data['url']
                # 비디오/움짤/외부 링크 확장 체크
                is_video = (
                    p_data.get('is_video', False) or 
                    any(ext in url for ext in ["v.redd.it", "youtube.com", "youtu.be", "gfycat.com", "giphy.com", "mp4", "gifv"])
                )
                if is_video:
                    all_posts.append({
                        "id": p_data['id'],
                        "title": p_data['title'],
                        "score": p_data['score'],
                        "url": url,
                        "permalink": f"https://www.reddit.com{p_data['permalink']}",
                        "subreddit": sub
                    })
                    found_in_sub += 1
            print(f"   - r/{sub}: {found_in_sub}개 발견")

        if not all_posts:
            print("❌ 조건에 맞는 영상 게시물을 찾지 못했습니다. 기간을 더 넓혀보세요.")
            input("\n엔터를 누르면 메뉴로 돌아갑니다...")
            continue

        # 중복 제거 및 점수순 정렬
        unique_posts_dict = {}
        for p in all_posts:
            if p['id'] not in unique_posts_dict:
                unique_posts_dict[p['id']] = p
        
        sorted_posts = sorted(unique_posts_dict.values(), key=lambda x: x['score'], reverse=True)

        clear_screen()
        print(f"✅ 총 {len(sorted_posts)}개의 다양한 영상을 발견했습니다! (기간: {time_filter})")
        print("-" * 60)
        # 상위 N개만 표시 (너무 많으면 스크롤 힘드니까)
        display_limit = min(limit, len(sorted_posts))
        for i, post in enumerate(sorted_posts[:display_limit]):
            print(f" [{i+1:2d}] 🔥{post['score']:5d} | {post['title'][:60]}")
            print(f"      (r/{post['subreddit']})")
        
        if len(sorted_posts) > display_limit:
            print(f"\n... 그 외 {len(sorted_posts) - display_limit}개의 결과가 더 있습니다.")
            
        print("-" * 60)
        print(" 다운로드할 번호들을 입력하세요 (예: 1, 3, 5 또는 'all')")
        print(" [B] 뒤로가기")
        
        selection = input("\n▶ 입력: ").strip().lower()
        if selection == 'b':
            continue
        
        target_indices = []
        if selection == 'all':
            target_indices = range(len(sorted_posts[:display_limit]))
        else:
            try:
                target_indices = [int(x.strip()) - 1 for x in selection.split(',') if x.strip()]
            except ValueError:
                print("⚠️ 올바른 번호를 입력해주세요.")
                time.sleep(1)
                continue

        # 다운로드 실행
        download_count = 0
        if not os.path.exists(DOWNLOAD_DIR):
            os.makedirs(DOWNLOAD_DIR)

        # 히스토리 로드
        downloaded_ids = set()
        if os.path.exists(ARCHIVE_FILE):
            with open(ARCHIVE_FILE, "r", encoding="utf-8") as f:
                downloaded_ids = set(line.strip() for line in f if line.strip())

        for idx in target_indices:
            if 0 <= idx < len(sorted_posts):
                post = sorted_posts[idx]
                
                # 중복 다운로드 체크 (연속 작업 편의를 위해 중복은 스킵하거나 자동 처리)
                if post['id'] in downloaded_ids:
                    print(f"⏩ 스킵 (이미 존재): {post['id']}")
                    continue

                safe_title = "".join([c for c in post['title'] if c.isalnum() or c in (' ', '_', '-')]).rstrip()[:50]
                file_base_name = f"{post['subreddit']}_{safe_title}_{post['id']}"
                save_path = os.path.join(DOWNLOAD_DIR, file_base_name)

                print(f"\n📥 [{idx+1}] 다운로드 중: {post['title']}")
                if download_reddit_video(post['permalink'], save_path):
                    comments = scrape_metadata(post['permalink'])
                    with open(f"{save_path}_metadata.txt", "w", encoding="utf-8") as f:
                        f.write(f"제목: {post['title']}\n")
                        f.write(f"추천수: {post['score']}\n")
                        f.write(f"원문링크: {post['permalink']}\n\n")
                        f.write("--- 베스트 댓글 ---\n")
                        for c_idx, c in enumerate(comments):
                            f.write(f"{c_idx+1}: {c}\n\n")
                    
                    # 히스토리에 기록
                    with open(ARCHIVE_FILE, "a", encoding="utf-8") as f:
                        f.write(f"{post['id']}\n")
                    
                    download_count += 1
                    print(f"✅ 완료: {file_base_name}")
                
        print(f"\n🎉 총 {download_count}개의 영상 다운로드 처리가 완료되었습니다.")
        input("\n엔터를 누르면 메뉴로 돌아갑니다...")

if __name__ == "__main__":
    try:
        pick_and_download()
    except KeyboardInterrupt:
        print("\n👋 프로그램을 종료합니다.")
        sys.exit(0)

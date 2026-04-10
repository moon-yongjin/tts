import os
from googleapiclient.discovery import build
import pandas as pd
from datetime import datetime, timedelta

# 🚨 사용법 안내:
# 1. Google Cloud Console에서 'YouTube Data API v3'를 활성화하고 API 키를 발급받으세요.
# 2. 아래 API_KEY 변수에 입력하시면 바로 현재 시장 상황을 크롤링할 수 있습니다.

API_KEY = "AIzaSyA38fzctz9x7OIKYHVB35hCoONOl8T80x8" # 👈기에 본인의 API 키를 넣으세요
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"

def get_trending_channels(keyword="사연드라마", max_results=20):
    if API_KEY == "YOUR_YOUTUBE_API_KEY":
        print("⚠️ 에러: API_KEY를 설정해야 스크립트가 작동합니다.")
        return

    youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=API_KEY)

    # 1. 최근 30일 이내 업로드된 영상 중 조회수가 높은 동영상 검색
    print(f"🔍 '{keyword}' 키워드로 급상승 중인 영상 검색 중...")
    
    # 30일 전 날짜 포맷팅 (RFC 3339)
    date_30_days_ago = (datetime.utcnow() - timedelta(days=30)).strftime('%Y-%m-%dT%H:%M:%SZ')

    search_response = youtube.search().list(
        q=keyword,
        part="snippet",
        type="video",
        order="viewCount",  # 조회수 높은 순
        publishedAfter=date_30_days_ago,
        maxResults=max_results,
        regionCode="KR"
    ).execute()

    channel_stats = []
    
    for item in search_response.get("items", []):
        video_title = item["snippet"]["title"]
        channel_id = item["snippet"]["channelId"]
        channel_title = item["snippet"]["channelTitle"]

        # 2. 개별 채널의 상세 스탯(구독자 수 등) 가져오기
        channel_response = youtube.channels().list(
            part="statistics,snippet",
            id=channel_id
        ).execute()

        for c_item in channel_response.get("items", []):
            stats = c_item["statistics"]
            subscribers = int(stats.get("subscriberCount", 0))
            views = int(stats.get("viewCount", 0))
            video_count = int(stats.get("videoCount", 0))

            # 3. '떡상' 채널 감지 룰 (구독자는 적은데 최근 조회수가 비정상적으로 높음)
            # 예: 구독자 5만 이하인데 이번 달 조회수 폭발 중인 곳
            if 1000 <= subscribers <= 100000:  # 소형~중형 채널로 한정
                channel_stats.append({
                    "채널명": channel_title,
                    "구독자수": f"{subscribers:,}명",
                    "누적조회수": f"{views:,}회",
                    "영상수": video_count,
                    "대표영상": video_title,
                    "채널링크": f"https://www.youtube.com/channel/{channel_id}"
                })

    # 4. 판다스 데이터프레임으로 깔끔하게 출력
    if channel_stats:
        df = pd.DataFrame(channel_stats)
        # 중복 채널 제거 (여러 영상이 걸렸을 때)
        df = df.drop_duplicates(subset=["채널명"])
        print("\n" + "="*80)
        print(f"📡 [최근 30일] '{keyword}' 분야 떡상(급상승) 예상 채널 리스트")
        print("="*80)
        print(df.to_string(index=False))
        print("="*80)
    else:
        print("\n⚠️ 조건에 맞는 떡상 채널을 찾지 못했습니다.")

if __name__ == "__main__":
    # 타겟 카테고리 설정 (예: 사연드라마, 숏드라마, 썰툰 등)
    get_trending_channels(keyword="사연드라마", max_results=15)

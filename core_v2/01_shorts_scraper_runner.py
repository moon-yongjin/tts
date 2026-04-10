import os
import subprocess
import json
import time
import datetime
from pathlib import Path

# [경로 설정]
CHANNEL_URL = "https://www.youtube.com/@%ED%95%98%EC%96%80%EB%B6%80%EC%97%89%EC%9D%B4%EC%82%AC%EC%97%B0/shorts"
DOWNLOADS_DIR = Path.home() / "Downloads"
OUTPUT_DIR = DOWNLOADS_DIR / f"Shorts_Scrape_{datetime.datetime.now().strftime('%m%d_%H%M')}"

# 조회수 필터 기준 (1만회)
VIEW_COUNT_THRESHOLD = 10000

def get_popular_shorts():
    print(f"🔍 [yt-dlp] 채널에서 조회수 {VIEW_COUNT_THRESHOLD}회 이상 영상 수집 중 (스트리밍)...")
    
    cmd = [
        "yt-dlp",
        "--match-filter", f"view_count > {VIEW_COUNT_THRESHOLD}",
        "--dump-json",
        CHANNEL_URL
    ]
    
    videos = []
    try:
        # Popen 사용 실시간 스트리밍 처리
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        # 실시간 라인 읽기
        for line in iter(process.stdout.readline, ""):
            if not line.strip(): continue
            try:
                data = json.loads(line)
                title = data.get("title", "No Title")
                view_count = data.get("view_count", 0)
                url = data.get("webpage_url", "")
                video_id = data.get("id", "")
                
                print(f"   💡 발견: {title[:20]}... ({view_count:,}회)")
                videos.append({
                    "title": title,
                    "view_count": view_count,
                    "url": url,
                    "id": video_id
                })
            except Exception:
                continue

        process.wait()
        if process.returncode != 0:
             # 에러 출력 소량만
             err = process.stderr.read()
             print(f"⚠️ 에러 로그: {err[:100]}")

        print(f"✅ 조건 만족 영상 총 {len(videos)}개 발견!")
        return videos
        
    except Exception as e:
        print(f"❌ 영상 수집 중 에러: {e}")
        return []

def download_audio(url, output_path):
    print(f"📥 다운로드 중: {url}")
    # 오디오만 최적 WAV 24000hz 한 채널로 뽑기
    cmd = [
        "yt-dlp",
        "-x", "--audio-format", "wav",
        "--audio-quality", "0",
        "--postprocessor-args", "ffmpeg: -ar 24000 -ac 1",
        "-o", output_path,
        url
    ]
    try:
         res = subprocess.run(cmd, capture_output=True, text=True)
         if res.returncode == 0:
              print(f"   ✅ 다운로드 성공")
              return True
         else:
              # 간혹 yt-dlp 가 wav 후처리 실패 시 .m4a 나 .wav 가 있는지 확인
              print(f"   ⚠️ yt-dlp 후처리 경고: {res.stderr[:200]}")
         return False
    except Exception as e:
         print(f"❌ 다운로드 에러: {e}")
         return False

def transcribe_all(videos):
    if not videos: return

    # 모델은 맥에서 가장 빠른 whisper-base-mlx-8bit 이용
    import mlx_whisper 
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"\n📂 결과 저장 폴더: {OUTPUT_DIR}\n")

    for i, vid in enumerate(videos):
        print(f"--- 🎬 [{i+1}/{len(videos)}] {vid['title']} (조회수: {vid['view_count']:,}회) ---")
        
        # 파일명 정제 (특수기호 제거)
        safe_title = "".join([c for c in vid['title'] if c.isalnum() or c in (' ', '_')]).rstrip()
        safe_title = safe_title.replace(" ", "_")
        
        audio_name = f"{vid['id']}_{safe_title}.wav"
        audio_path = os.path.join(OUTPUT_DIR, audio_name)
        txt_path = os.path.join(OUTPUT_DIR, f"{vid['id']}_{safe_title}_대본.txt")

        # 1. 오디오 다운로드
        if download_audio(vid['url'], audio_path):
            # 후처리 완료된 .wav 파일 경로 검증 (yt-dlp 가 .wav.wav 등 다중 생성하는 버그 대비)
            actual_audio_path = audio_path
            # 만약 그냥 다운로드가 비정형화되어 있다면 보정
            if not os.path.exists(actual_audio_path):
                 if os.path.exists(audio_path + ".wav"): actual_audio_path = audio_path + ".wav"

            if os.path.exists(actual_audio_path):
                 # 2. Transcribe
                 print(f"⏳ 대본 추출(Transcribe) 구동 중...")
                 try:
                     result = mlx_whisper.transcribe(
                         actual_audio_path,
                         path_or_hf_repo="mlx-community/whisper-base-mlx-8bit",
                         language="ko"
                     )
                     text = result.get("text", "").strip()
                     if text:
                          with open(txt_path, "w", encoding="utf-8") as f:
                              f.write(text)
                          print(f"✅ 대본 저장 완료: {os.path.basename(txt_path)}")
                     else:
                          print("⚠️ 녹취된 텍스트가 없습니다.")
                 except Exception as e:
                      print(f"❌ 녹취 실패: {e}")
            else:
                 print(f"❌ 오디오 파일을 찾을 수 없습니다: {actual_audio_path}")
        else:
            print(f"❌ 다운로드 스킵됨.")

def main():
    videos = get_popular_shorts()
    if videos:
         # 최대 속도 5개만 먼저 돌려봅니다 등의 한도 필요 시 slicing 가능
         # videos = videos[:5] 
         transcribe_all(videos)
         print(f"\n🎉 전체 작업 완료! 저장 위치: {OUTPUT_DIR}")
    else:
         print("💡 조건에 맞는 영상이 없습니다.")

if __name__ == "__main__":
    main()

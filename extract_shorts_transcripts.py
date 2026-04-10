import os
import glob
from pathlib import Path
import mlx_whisper

# [설정]
SOURCE_DIR = "/Users/a12/Desktop/youtube_shorts_이해불가"
print(f"🔍 Searching in: {SOURCE_DIR}")
OUTPUT_BASE_DIR = os.path.expanduser("~/Downloads/이해불가_대본_추출")

def transcribe_and_organize():
    # 1. 대상 파일 목록 (MP4 + WEBM)
    video_files = glob.glob(os.path.join(SOURCE_DIR, "*.mp4")) + glob.glob(os.path.join(SOURCE_DIR, "*.webm"))
    
    if not video_files:
        print("❌ 대상 폴더에 파일이 없습니다.")
        return

    # 2. 결과 저장 기본 폴더 생성
    if not os.path.exists(OUTPUT_BASE_DIR):
        os.makedirs(OUTPUT_BASE_DIR)
        print(f"📂 결과 저장 폴더 생성: {OUTPUT_BASE_DIR}")

    for video_path in video_files:
        video_name = Path(video_path).stem
        video_folder = os.path.join(OUTPUT_BASE_DIR, video_name)
        
        # 각 영상별 폴더 생성
        if not os.path.exists(video_folder):
            os.makedirs(video_folder)
        
        output_txt = os.path.join(video_folder, f"{video_name}.txt")
        
        if os.path.exists(output_txt) and os.path.getsize(output_txt) > 0:
            print(f"⏭️ {video_name} 이미 추출됨. 스킵.")
            continue

        print(f"🎙️ '{video_name}' 대본 추출 시작 (Python API)...")
        
        try:
            # mlx_whisper Python API 사용
            result = mlx_whisper.transcribe(
                video_path,
                model="mlx-community/whisper-large-v3-turbo", # 허깅페이스 레포 ID 명시가 더 나을 수 있음
                language="ko"
            )
            
            transcript_text = result.get("text", "").strip()
            
            if transcript_text:
                with open(output_txt, "w", encoding="utf-8") as f:
                    f.write(transcript_text)
                print(f"✅ '{video_name}' 추출 완료! (내용: {len(transcript_text)}자)")
            else:
                print(f"⚠️ '{video_name}' 추출된 텍스트가 없습니다.")
            
        except Exception as e:
            print(f"❌ '{video_name}' 오류 발생: {e}")
            # 만약 모델 ID가 문제면 whisper-large-v3-turbo (단축어) 시도
            if "Repository Not Found" in str(e):
                try:
                    print("🔄 모델 ID 재시도 (large-v3-turbo)...")
                    result = mlx_whisper.transcribe(
                        video_path,
                        model="large-v3-turbo",
                        language="ko"
                    )
                    transcript_text = result.get("text", "").strip()
                    if transcript_text:
                        with open(output_txt, "w", encoding="utf-8") as f:
                            f.write(transcript_text)
                        print(f"✅ '{video_name}' 추출 완료! (내용: {len(transcript_text)}자)")
                except Exception as e2:
                    print(f"❌ '{video_name}' 재시도 실패: {e2}")

if __name__ == "__main__":
    transcribe_and_organize()

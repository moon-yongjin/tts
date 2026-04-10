import os
import mlx_whisper

# --- [설정] ---
# 형님이 지정해주신 파일 경로
VIDEO_PATH = "/Users/a12/Downloads/Screen_Recording_20260326_191730_YouTube.mp4"
OUTPUT_PATH = "/Users/a12/Downloads/Screen_Recording_20260326_191730_transcript.txt"
MODEL_PATH = "mlx-community/whisper-large-v3-turbo"

def transcribe():
    print(f"🎙️ 비디오 분석 시작: {os.path.basename(VIDEO_PATH)}")
    
    if not os.path.exists(VIDEO_PATH):
        print(f"❌ 파일이 존재하지 않습니다: {VIDEO_PATH}")
        return

    try:
        print(f"⏳ MLX-Whisper ({MODEL_PATH}) 로드 및 변환 중...")
        result = mlx_whisper.transcribe(
            VIDEO_PATH,
            path_or_hf_repo=MODEL_PATH,
            language="ko"
        )
        
        transcript = result["text"].strip()
        
        # 결과 저장
        with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
            f.write(transcript)
            
        print("\n" + "="*50)
        print("✅ 추출된 텍스트:")
        print(transcript)
        print("="*50)
        print(f"\n📂 저장 완료: {OUTPUT_PATH}")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")

if __name__ == "__main__":
    transcribe()

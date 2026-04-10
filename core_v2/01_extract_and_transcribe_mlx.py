import os
import subprocess
import time
import mlx_whisper

# [경로 설정]
VIDEO_PATH = "/Users/a12/Downloads/Screen_Recording_20260316_173013_YouTube.mp4"
OUTPUT_DIR = "/Users/a12/projects/tts/voices/Reference_Audios"
AUDIO_OUTPUT = os.path.join(OUTPUT_DIR, "extracted_ref.wav")
TRANSCRIPT_OUTPUT = os.path.join(OUTPUT_DIR, "extracted_ref_transcript.txt")

def extract_audio():
    if not os.path.exists(VIDEO_PATH):
        print(f"❌ 비디오 파일을 찾을 수 없습니다: {VIDEO_PATH}")
        return False

    print(f"🎙️ [Extract] {os.path.basename(VIDEO_PATH)} 에서 오디오 추출 중...")
    
    # ffmpeg 사용 오디오 추출 (WAV 24000Hz 1ch mono 로 맞춰서 추출)
    cmd = [
        "ffmpeg", "-y", "-i", VIDEO_PATH, 
        "-vn", "-acodec", "pcm_s16le", "-ar", "24000", "-ac", "1", 
        AUDIO_OUTPUT
    ]
    
    try:
        # 오버헤드 억제
        result = subprocess.run(cmd, capture_output=True, text=True)
        if os.path.exists(AUDIO_OUTPUT):
            print(f"   ✅ 오디오 추출 완료: {AUDIO_OUTPUT}")
            return True
        else:
             print(f"❌ 오디오 추출 실패\n {result.stderr}")
             return False
    except Exception as e:
        print(f"❌ ffmpeg 에러: {e}")
        return False

def transcribe_audio():
    if not os.path.exists(AUDIO_OUTPUT):
        print(f"❌ 오디오 파일이 없습니다.")
        return

    print(f"⏳ [MLX-Whisper] 한국어 녹취(Transcribe) 중... (모델: base)")
    # mlx-whisper 의 transcribe 호출 (기본 base 모델 사용 혹은 다소 높은 모델 권장)
    try:
         # mlx-whisper.transcribe() 는 path 를 받음
         result = mlx_whisper.transcribe(
             AUDIO_OUTPUT, 
             path_or_hf_repo="mlx-community/whisper-base-mlx-8bit", # 맥에서 가장 빠른 구조
             language="ko",
             verbose=True
         )
         
         text = result.get("text", "").strip()
         if text:
             with open(TRANSCRIPT_OUTPUT, "w", encoding="utf-8") as f:
                 f.write(text)
             # 출력
             print(f"\n✅ [MLX-Whisper] 녹취 성공! 파일 저장됨: {TRANSCRIPT_OUTPUT}")
             print("\n--- 📜 녹취 텍스트 스니펫 ---")
             print(text[:200] + ("..." if len(text) > 200 else ""))
             print("--------------------------\n")
         else:
              print("⚠️ 녹취된 텍스트가 없습니다.")
    except Exception as e:
        print(f"❌ 녹취 실패: {e}")

if __name__ == "__main__":
    if extract_audio():
        transcribe_audio()

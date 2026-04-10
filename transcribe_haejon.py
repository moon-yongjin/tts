import os
import glob
import mlx_whisper

# --- [설정] ---
TARGET_DIR = os.path.expanduser("~/Downloads/해전학전")
OUTPUT_FILE = os.path.expanduser("~/Downloads/해전학전_대본모음.txt")

# MLX 최적화 모델 경로 (huggingface에서 자동 다운로드)
MODEL_PATH = "mlx-community/whisper-large-v3-turbo"

def transcribe_with_mlx(file_path):
    print(f"  진행 중: MLX-Whisper로 영상 분석 중... ({os.path.basename(file_path)})")
    try:
        # mlx_whisper.transcribe 
        result = mlx_whisper.transcribe(
            file_path, 
            path_or_hf_repo=MODEL_PATH,
            language="ko"  # 한국어로 된 영상이므로 우선 한국어 지정
        )
        return result["text"].strip()
    except Exception as e:
        print(f"  ❌ MLX 변환 실패: {e}")
        return f"[MLX 변환 실패: {e}]"

def main():
    print("--- 해전학전 영상 대본 자동 추출 시작 (MLX-Whisper) ---")
    video_files = sorted(glob.glob(os.path.join(TARGET_DIR, "*.mp4")))
    
    # 이미 처리된 파일 목록 불러오기
    processed_files = []
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
            # 예: [1] 영상제목.mp4 형식 파싱
            import re
            processed_files = re.findall(r'\[\d+\] ([\w\.\s가-힣-]+\.mp4)', content)
    
    # 새로운 파일만 필터링
    new_video_files = [f for f in video_files if os.path.basename(f) not in processed_files]
    
    print(f"전체 {len(video_files)}개 중 {len(new_video_files)}개의 새로운 영상을 처리합니다.")
    
    if not new_video_files:
        print("새롭게 처리할 영상이 없습니다.")
        return

    # 'a' 모드로 열어서 기존 파일에 추가
    with open(OUTPUT_FILE, 'a', encoding='utf-8') as f:
        start_idx = len(processed_files) + 1
        for i, video_path in enumerate(new_video_files):
            filename = os.path.basename(video_path)
            print(f"\n({i+1}/{len(new_video_files)}) 처리 중...: {filename}")
            
            transcript = transcribe_with_mlx(video_path)
            print(f"  ✅ 대본 추출 완료 (길이: {len(transcript)}자)")
            
            f.write(f"[{start_idx + i}] {filename}\n")
            f.write(f"대본: {transcript}\n")
            f.write("-" * 50 + "\n\n")
            
    print(f"\n🎉 모든 처리가 완료되었습니다! 결과 저장: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()

import os
import sys
import subprocess
import shutil
from pathlib import Path
from datetime import timedelta
import mlx_whisper

# ffmpeg 경로 강제 추가
os.environ["PATH"] += os.pathsep + "/opt/homebrew/bin"
os.environ["PATH"] += os.pathsep + "/Applications/CapCut.app/Contents/Resources"

# --- [설정] ---
# 결과물이 저장될 기본 폴더
BASE_OUTPUT_DIR = Path.home() / "Downloads" / "extracted_assets"
# MLX Whisper 모델
WHISPER_MODEL = "mlx-community/whisper-large-v3-turbo"

def run_command(cmd, description):
    print(f"🚀 {description} 중...")
    try:
        subprocess.run(cmd, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 에러 발생 ({description}): {e}")
        return False

def extract_vocals(video_path, output_dir):
    """Demucs를 사용하여 보컬(음성)만 추출 (배경음 제거)"""
    print(f"🎵 배경음 제거 및 보컬 추출 시작...")
    
    # demucs 실행 (고품질 모델 htdemucs_ft 사용)
    # --two-stems=vocals 옵션을 쓰면 vocals.wav와 no_vocals.wav만 나옴
    cmd = [
        sys.executable, "-m", "demucs", 
        "-n", "htdemucs_ft",
        "--two-stems", "vocals",
        "-o", str(output_dir),
        str(video_path)
    ]
    
    if run_command(cmd, "보컬 분리"):
        # demucs는 output_dir/htdemucs_ft/파일명/vocals.wav 경로에 저장함
        video_name = Path(video_path).stem
        src_path = output_dir / "htdemucs_ft" / video_name / "vocals.wav"
        dest_path = output_dir / f"{video_name}_vocals.wav"
        
        if src_path.exists():
            shutil.move(str(src_path), str(dest_path))
            # 임시 생성된 htdemucs_ft 폴더 삭제
            shutil.rmtree(output_dir / "htdemucs_ft")
            return dest_path
    return None

def format_timestamp(seconds):
    """지초를 SRT 타임스탬프 형식(00:00:00,000)으로 변환"""
    td = timedelta(seconds=seconds)
    total_seconds = int(td.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60
    milliseconds = int(td.microseconds / 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{milliseconds:03d}"

def transcribe_video(video_path, output_dir):
    """MLX Whisper를 사용하여 자막(텍스트 및 SRT) 추출"""
    print(f"📝 자막 추출 및 받아쓰기 시작...")
    video_name = Path(video_path).stem
    
    try:
        result = mlx_whisper.transcribe(
            str(video_path), 
            path_or_hf_repo=WHISPER_MODEL,
            language="ko"
        )
        
        # 1. 일반 텍스트 저장
        text_path = output_dir / f"{video_name}_대본.txt"
        with open(text_path, "w", encoding="utf-8") as f:
            f.write(result["text"].strip())
            
        # 2. SRT 자막 파일 생성
        srt_path = output_dir / f"{video_name}.srt"
        with open(srt_path, "w", encoding="utf-8") as f:
            for i, segment in enumerate(result.get("segments", []), 1):
                start = format_timestamp(segment["start"])
                end = format_timestamp(segment["end"])
                text = segment["text"].strip()
                f.write(f"{i}\n{start} --> {end}\n{text}\n\n")
            
        return text_path, srt_path
    except Exception as e:
        print(f"❌ 자막 추출 실패: {e}")
        return None, None

def main():
    import argparse
    parser = argparse.ArgumentParser(description="에셋 추출기 (음성 분리 및 자막 생성)")
    parser.add_argument("video_path", help="영상 파일 경로")
    parser.add_argument("--fast", action="store_true", help="고속 모드 (보컬 분리 건너뜀)")
    
    args = parser.parse_args()
    video_path = Path(args.video_path).resolve()
    
    if not video_path.exists():
        print(f"❌ 파일을 찾을 수 없습니다: {video_path}")
        return

    # 출력 폴더 준비
    video_name = video_path.stem
    output_dir = BASE_OUTPUT_DIR / video_name
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n--- [{video_name}] 에셋 추출 작업 시작 {'(고속 모드)' if args.fast else ''} ---")

    # 1. 보컬 추출 (고속 모드일 경우 건너뜀)
    vocal_file = None
    if not args.fast:
        vocal_file = extract_vocals(video_path, output_dir)
    else:
        print("⚡ 고속 모드: 보컬 분리를 건너뜁니다.")
    
    # 2. 자막 추출
    transcript_file, srt_file = transcribe_video(video_path, output_dir)

    print("\n" + "="*40)
    print("✅ 모든 작업 완료!")
    if vocal_file: print(f"🎙️ 깨끗한 음성: {vocal_file.name}")
    if transcript_file: print(f"📄 추출 대본: {transcript_file.name}")
    if srt_file: print(f"🎬 자막 파일: {srt_file.name}")
    print(f"📂 저장 폴더: {output_dir}")
    print("="*40)
    
    # 폴더 열기
    subprocess.run(["open", str(output_dir)])

if __name__ == "__main__":
    main()

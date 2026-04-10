import os
import sys
import subprocess
from pathlib import Path
from pydub import AudioSegment
from pydub.silence import split_on_silence

# [설정]
BASE_OUTPUT_DIR = Path.home() / "Downloads" / "extracted_assets"

def run_command(cmd, description):
    print(f"🚀 {description} 중...")
    try:
        subprocess.run(cmd, check=True, capture_output=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 에러 발생 ({description}): {e.stderr.decode()}")
        return False

def extract_full_audio(video_path, output_dir):
    """영상에서 전체 오디오를 고품질 wav로 추출"""
    video_name = Path(video_path).stem
    temp_wav = output_dir / f"{video_name}_temp_full.wav"
    
    print(f"🎵 전체 오디오 추출 시작: {video_name}")
    cmd = [
        "ffmpeg", "-y", "-i", str(video_path),
        "-vn", "-acodec", "pcm_s16le", "-ar", "44100", "-ac", "2",
        str(temp_wav)
    ]
    
    if run_command(cmd, "오디오 추출"):
        return temp_wav
    return None

def trim_silence(input_path, output_path):
    """무음 구간을 탐색하여 삭제 (음성 밀도 최적화)"""
    if not input_path.exists():
        return False

    print(f"✂️ 무음 구간 제거 중 (기준: -45dBFS, 500ms)...")
    try:
        audio = AudioSegment.from_wav(str(input_path))
        
        # 무음 구간 기준으로 분할 (0.5초 이상의 무음을 찾아 0.25초 여유만 남김)
        chunks = split_on_silence(
            audio, 
            min_silence_len=500, 
            silence_thresh=-45, 
            keep_silence=250
        )
        
        if not chunks:
            print("⚠️ 유효한 음성 구간을 찾지 못했습니다. 원본을 유지합니다.")
            return False
            
        print(f"🎙️ 총 {len(chunks)}개의 음성 마디 발견. 결합 중...")
        combined = AudioSegment.empty()
        for chunk in chunks:
            combined += chunk
            
        combined.export(str(output_path), format="wav")
        print(f"✅ 무음 제거 완료: {output_path.name}")
        return True
    except Exception as e:
        print(f"❌ 무음 제거 중 오류 발생: {e}")
        return False

def main():
    if len(sys.argv) < 2:
        input_path = input("📄 분석할 영상 파일(.mp4) 혹은 폴더 경로를 입력하세요: ").strip()
        if not input_path: return
    else:
        input_path = sys.argv[1]

    path = Path(input_path).resolve()
    
    # 폴더인 경우 내부에 .mp4 파일 하나 선택 (편의성)
    if path.is_dir():
        files = list(path.glob("*.mp4"))
        if not files:
            print("❌ 폴더 내에 영상 파일(.mp4)이 없습니다.")
            return
        video_path = files[0]
        output_dir = path
    else:
        video_path = path
        output_dir = video_path.parent

    # 1. 고품질 오디오 추출
    temp_wav = extract_full_audio(video_path, output_dir)
    
    if temp_wav:
        # 2. 무음 제거
        final_output = output_dir / f"{video_path.stem}_Full_NoSilence.wav"
        success = trim_silence(temp_wav, final_output)
        
        # 임시 파일 삭제
        if temp_wav.exists():
            os.remove(temp_wav)
            
        if success:
            print("\n" + "="*40)
            print("✨ 모든 작업이 완료되었습니다!")
            print(f"📂 결과물: {final_output.name}")
            print(f"📍 위치: {output_dir}")
            print("="*40)
            os.system(f"open {output_dir}")
        else:
            print("❌ 최종 파일 생성에 실패했습니다.")

if __name__ == "__main__":
    main()

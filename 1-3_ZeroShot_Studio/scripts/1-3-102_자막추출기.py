import tkinter as tk
from tkinter import filedialog
import os
import mlx_whisper
import time
import subprocess
import shutil
from pathlib import Path

# --- 설정 (맥 실리콘 최적화) ---
PYTHON_PATH = "/Users/a12/miniforge3/bin/python"
DEMUCS_PATH = "/Users/a12/miniforge3/bin/demucs"
FFMPEG_PATH = "/Users/a12/miniforge3/bin/ffmpeg"
WHISPER_MODEL = "mlx-community/whisper-large-v3-turbo"

def format_time(seconds):
    """초를 SRT 형식(HH:MM:SS,mmm)으로 변환"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds - int(seconds)) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

def preprocess_audio(file_path):
    """오디오 추출 및 볼륨 정규화 (작은 목소리 키우기)"""
    print("\n🔊 [Step 0] 오디오 최적화 중 (볼륨 정규화)...")
    temp_wav = Path("tmp_normalized.wav")
    
    if temp_wav.exists():
        temp_wav.unlink()
    
    try:
        # loudnorm 필터를 사용하여 전체적인 볼륨을 평준화하고 작은 소리를 키움
        # -ar 16000 -ac 1 은 Whisper 인식률에 최적화된 포맷
        cmd = [
            FFMPEG_PATH, "-y", "-i", file_path,
            "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
            "-ar", "16000", "-ac", "1",
            str(temp_wav)
        ]
        # stdout/stderr를 캡처하여 오류 메시지 확인 가능하게 함
        subprocess.run(cmd, check=True, capture_output=True)
        return str(temp_wav)
    except Exception as e:
        print(f"⚠️ 오디오 최적화 중 주의: {e}")
        print("💡 원본 파일로 계속 진행합니다.")
        return file_path

def separate_vocals(file_path):
    """Demucs를 사용하여 보컬과 배경음 분리"""
    
    # 0단계: 오디오 최적화 우선 수행
    optimized_path = preprocess_audio(file_path)
    
    print("\n🎸 [Step 1] 음원 분리 중 (보컬 vs 배경음)...")
    print("💡 이 작업은 AI가 노래를 분석하므로 1~3분 정도 소요될 수 있습니다.")
    
    # 임시 출력 폴더 설정
    output_dir = Path("tmp_separated")
    if output_dir.exists():
        shutil.rmtree(output_dir)
    
    try:
        # Demucs 실행 (htdemucs 모델 사용)
        cmd = [DEMUCS_PATH, "-n", "htdemucs", "--out", str(output_dir), optimized_path]
        subprocess.run(cmd, check=True)
        
        # 분리된 보컬 파일 경로 찾기
        # preprocess_audio 결과가 tmp_normalized.wav 이므로 stem은 'tmp_normalized'
        file_name = Path(optimized_path).stem
        vocals_path = output_dir / "htdemucs" / file_name / "vocals.wav"
        
        if vocals_path.exists():
            print("✅ 음원 분리 성공! 보컬 트랙을 사용합니다.")
            return str(vocals_path)
        else:
            print("⚠️ 보컬 파일을 찾을 수 없습니다. 최적화된 파일로 진행합니다.")
            return optimized_path
            
    except Exception as e:
        print(f"❌ 음원 분리 중 오류 발생: {e}")
        print("💡 최적화된 파일(또는 원본)로 자막 추출을 시도합니다.")
        return optimized_path

def main():
    # 파일 선택 창
    root = tk.Tk()
    root.withdraw()  
    root.call('wm', 'attributes', '.', '-topmost', True)
    
    file_path = filedialog.askopenfilename(
        title="자막을 추출할 노래 또는 영상 파일을 선택하세요",
        filetypes=[
            ("지원 파일", "*.mp3 *.wav *.m4a *.mp4 *.mkv *.avi *.mov *.flv *.webm *.ogg")
        ]
    )

    if not file_path:
        print("파일 선택을 취소했습니다.")
        return

    print(f"🎬 선택된 파일: {file_path}")

    # 🎤 1단계: 보컬 분리 (노래일 경우 필수)
    processing_file = separate_vocals(file_path)

    # 🎙️ 2단계: 자막 추출 (MLX-Whisper)
    print(f"\n🤖 [Step 2] 자막 생성 중... (모델: {WHISPER_MODEL})")
    start_time_total = time.time()
    
    try:
        # mlx_whisper.transcribe 실행
        result = mlx_whisper.transcribe(
            processing_file,
            path_or_hf_repo=WHISPER_MODEL,
            language="ko"
        )
        
        segments = result.get("segments", [])
        
        # SRT 및 TXT 파일 저장 (원본 고유 이름 유지)
        base_name = os.path.splitext(file_path)[0]
        srt_path = f"{base_name}_자막.srt"
        txt_path = f"{base_name}_대본.txt"

        # SRT 저장
        with open(srt_path, "w", encoding="utf-8-sig") as f:
            for i, segment in enumerate(segments, start=1):
                start_s = format_time(segment["start"])
                end_s = format_time(segment["end"])
                text = segment["text"].strip()
                f.write(f"{i}\n{start_s} --> {end_s}\n{text}\n\n")

        # TXT(대본) 저장
        full_text = result.get("text", "").strip()
        with open(txt_path, "w", encoding="utf-8-sig") as f:
            f.write(full_text)

        elapsed_time = time.time() - start_time_total
        print(f"\n✨ 모든 작업 완료! (총 소요 시간: {elapsed_time:.1f}초)")
        print(f"📁 생성된 자막: {srt_path}")
        print(f"📄 생성된 대본: {txt_path}")
        
    except Exception as e:
        print(f"❌ 자막 추출 중 오류 발생: {e}")

    # 임시 폴더 삭제 (선택 사항)
    # if Path("tmp_separated").exists(): shutil.rmtree("tmp_separated")

if __name__ == "__main__":
    main()

import os
import glob
from pathlib import Path
from pydub import AudioSegment
from pydub.silence import split_on_silence

def trim_wav_silence(input_path):
    if not os.path.exists(input_path):
        print(f"❌ 파일을 찾을 수 없습니다: {input_path}")
        return

    print(f"📂 파일 로딩 중: {input_path}")
    audio = AudioSegment.from_wav(input_path)

    print("✂️ 무음 구간 탐색 및 분할 중 (기준: -45dBFS, 500ms)...")
    chunks = split_on_silence(
        audio, 
        min_silence_len=500, 
        silence_thresh=-45, 
        keep_silence=250 # 문장 간 여유 250ms
    )

    if not chunks:
        print("⚠️ 유효한 음성 구간을 찾지 못했습니다. 설정을 확인하세요.")
        return

    print(f"🎙️ 총 {len(chunks)}개의 유효 구간 발견. 결합 중...")
    combined = AudioSegment.empty()
    for chunk in chunks:
        combined += chunk

    output_path = str(input_path).replace(".wav", "_Trimmed.wav")
    print(f"📤 결과 저장 중: {output_path}")
    combined.export(output_path, format="wav")
    print(f"✅ 완료! 파일 크기 변화: {os.path.getsize(input_path)//1024}KB -> {os.path.getsize(output_path)//1024}KB")

if __name__ == "__main__":
    downloads_path = Path.home() / "Downloads"
    # 가장 최근에 생성된 ZeroShot 관련 파일 찾기
    files = glob.glob(str(downloads_path / "Full_ZeroShot_*.wav"))
    
    if not files:
        print(f"📍 {downloads_path}에서 'Full_ZeroShot_*.wav' 파일을 찾을 수 없습니다.")
        # 일반 wav 파일이라도 있는지 확인
        files = glob.glob(str(downloads_path / "*.wav"))
        
    if files:
        # 가장 최근 파일 선택
        latest_file = max(files, key=os.path.getctime)
        print(f"🔍 가장 최근 파일을 처리합니다: {os.path.basename(latest_file)}")
        trim_wav_silence(latest_file)
    else:
        print("❌ 처리할 .wav 파일이 다운로드 폴더에 없습니다.")

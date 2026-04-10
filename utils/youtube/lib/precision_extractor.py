import os
import json
import subprocess
from pathlib import Path
from pydub import AudioSegment

def extract_and_merge_speaker_audio(segments, video_source, speaker_name, output_audio_path):
    """특정 화자의 구간만 추출하여 하나의 오디오 파일로 합침"""
    print(f"🎵 '{speaker_name}'의 목소리만 모으는 중...")
    
    # 원본 오디오 로드 (ffmpeg로 먼저 wav 변환)
    temp_full_wav = output_audio_path.parent / "temp_full_for_extract.wav"
    subprocess.run([
        "ffmpeg", "-y", "-i", str(video_source),
        "-vn", "-acodec", "pcm_s16le", "-ar", "44100", "-ac", "2",
        str(temp_full_wav)
    ], capture_output=True)
    
    full_audio = AudioSegment.from_wav(str(temp_full_wav))
    combined = AudioSegment.empty()
    
    target_segments = [s for s in segments if s.get("speaker") == speaker_name]
    
    if not target_segments:
        print(f"⚠️ '{speaker_name}' 화자의 세그먼트를 찾을 수 없습니다.")
        return False

    for s in target_segments:
        start_ms = int(s["start"] * 1000)
        end_ms = int(s["end"] * 1000)
        chunk = full_audio[start_ms:end_ms]
        combined += chunk
        # 문장 간 아주 짧은 여백 (100ms) 추가
        combined += AudioSegment.silent(duration=100)
        
    combined.export(str(output_audio_path), format="wav")
    
    # 임시 파일 삭제
    if temp_full_wav.exists():
        os.remove(temp_full_wav)
        
    return True

def extract_speaker_text(segments, speaker_name, output_txt_path):
    """특정 화자의 대사만 텍스트로 추출"""
    target_segments = [s for s in segments if s.get("speaker") == speaker_name]
    
    with open(output_txt_path, "w", encoding="utf-8") as f:
        f.write(f"=== {speaker_name} 발언 통합 대본 ===\n\n")
        for s in target_segments:
            f.write(f"[{s['start']:.2f}s] {s['text']}\n")
    return True

if __name__ == "__main__":
    # 이 스크립트는 라이브러리로도 사용되지만, 단독 실행 시 특정 작업을 수행하도록 구성
    import sys
    if len(sys.argv) < 4:
        print("Usage: python extract_speaker_segments.py [json_path] [video_path] [speaker_name]")
        sys.exit(1)
        
    json_p = Path(sys.argv[1])
    video_p = Path(sys.argv[2])
    speaker = sys.argv[3]
    
    with open(json_p, "r", encoding="utf-8") as f:
        segs = json.load(f)
        
    out_dir = json_p.parent
    audio_out = out_dir / f"{speaker}_merged_voice.wav"
    text_out = out_dir / f"{speaker}_script_final.txt"
    
    if extract_and_merge_speaker_audio(segs, video_p, speaker, audio_out):
        print(f"✅ 오디오 추출 완료: {audio_out.name}")
        
    if extract_speaker_text(segs, speaker, text_out):
        print(f"✅ 텍스트 추출 완료: {text_out.name}")

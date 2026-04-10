import json
import subprocess
from pathlib import Path
from google import genai
from google.genai import types

def generate_shorts_from_manual_segments(segments, video_source_path, output_dir):
    """사용자가 선택한 세그먼트들을 결합하여 최종 쇼츠 에셋 생성"""
    if not segments:
        return None, None
        
    print(f"🎬 {len(segments)}개의 선택된 세그먼트로 쇼츠 구성을 시작합니다...")
    
    # 1. 합쳐진 대본 저장
    combined_text = "\n".join([s.get('text', '') for s in segments])
    script_path = output_dir / "Shorts_Script_Manual.txt"
    with open(script_path, "w", encoding="utf-8") as f:
        f.write(combined_text)
        
    # 2. 오디오 결합 (각 세그먼트를 컷팅해서 합침)
    audio_path = output_dir / "Shorts_Voice_Manual.wav"
    
    # 임시 폴더 생성
    tmp_dir = output_dir / "tmp_segments"
    tmp_dir.mkdir(exist_ok=True)
    
    segment_files = []
    for i, s in enumerate(segments):
        start = s.get('start', 0)
        end = s.get('end', 0)
        dur = end - start
        if dur <= 0: continue
        
        seg_file = tmp_dir / f"seg_{i:03d}.wav"
        cmd = [
            "ffmpeg", "-y", "-ss", str(start), "-t", str(dur),
            "-i", str(video_source_path), "-vn", "-acodec", "pcm_s16le", "-ar", "44100", "-ac", "2",
            str(seg_file)
        ]
        subprocess.run(cmd, capture_output=True, check=True)
        segment_files.append(seg_file)
        
    if not segment_files:
        return None, None

    # 오디오 컨캣
    list_path = tmp_dir / "list.txt"
    with open(list_path, "w", encoding="utf-8") as f:
        for f_path in segment_files:
            f.write(f"file '{f_path.name}'\n")
            
    concat_cmd = [
        "ffmpeg", "-y", "-f", "concat", "-i", str(list_path),
        "-c", "copy", str(audio_path)
    ]
    subprocess.run(concat_cmd, cwd=str(tmp_dir), capture_output=True, check=True)
    
    return script_path, audio_path

def generate_golden_shorts(api_key, segments, video_source_path, output_dir):
    """자막 데이터를 기반으로 최고의 1분을 선정하고 대본 및 음성 추출 (AI 자동 모드)"""
    if not api_key:
        print("⚠️ Gemini Key가 없어 쇼츠 생성 로직을 건너뜁니다.")
        return None, None
        
    print("🎬 Gemini가 최고의 1분 구간을 선정하고 대본을 구성 중입니다...")
    # ... (기존 로직 유지)
    client = genai.Client(api_key=api_key)
    
    # 자막 텍스트 구성 (시간 정보 포함)
    full_text = "\n".join([
        f"[{s.get('start', 0):.1f}s] {s.get('speaker', '?')}: {s.get('text', '')}" 
        for s in segments
    ])
    
    prompt = f"""
다음 화자 분리 대본에서 1분 쇼츠로 만들기에 가장 감동적이거나 핵심적인 구간을 선정해 주세요.

**작업 내용:**
1. **쇼츠 대본**: 사연자 1인칭 시점의 따뜻하고 감성적인 나레이션으로 1분 분량(300~400자) 각색.
2. **골든 타임**: 위 대본 내용과 일치하는 원본 영상의 '시작 시간'과 '종료 시간'을 초 단위로 정확히 반환.

대본 데이터:
{full_text}

---
**출력 형식 (JSON):**
{{
  "script": "1인칭 각색 대본 내용...",
  "start_sec": 120,
  "end_sec": 180
}}
"""
    try:
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=prompt,
            config=types.GenerateContentConfig(response_mime_type="application/json")
        )
        res = json.loads(response.text.strip())
        
        # 1. 대본 저장
        script_path = output_dir / "Shorts_Script_V4.txt"
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(res["script"])
            
        # 2. 고품질 오디오 컷팅 (44.1kHz, Stereo)
        audio_path = output_dir / "Shorts_Voice_Golden.wav"
        print(f"✂️ 골든 타임 컷팅 중: {res['start_sec']}s ~ {res['end_sec']}s")
        
        cmd = [
            "ffmpeg", "-y", 
            "-ss", str(res["start_sec"]), 
            "-to", str(res["end_sec"]),
            "-i", str(video_source_path), 
            "-vn", "-acodec", "pcm_s16le", "-ar", "44100", "-ac", "2",
            str(audio_path)
        ]
        subprocess.run(cmd, capture_output=True, check=True)
        
        return script_path, audio_path
        
    except Exception as e:
        print(f"❌ 골든 쇼츠 생성 실패: {e}")
        return None, None

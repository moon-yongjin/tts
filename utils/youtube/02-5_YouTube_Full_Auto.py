import os
import sys
import subprocess
import re
import json
import time
from pathlib import Path
from google import genai
from google.genai import types

# OpenCV가 없을 경우를 대비한 체크
try:
    import cv2
    import numpy as np
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False

# [설정]
PYTHON_EXE = sys.executable
PROJECT_ROOT = Path(__file__).parent.parent.parent
EXTRACTOR_SCRIPT = PROJECT_ROOT / "extract_assets.py"
DOWNLOADS_DIR = Path.home() / "Downloads"
CONFIG_PATH = PROJECT_ROOT / "config.json"

def load_gemini_key():
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            config = json.load(f)
            return config.get("Gemini_API_KEY")
    except:
        return None

def run_command(cmd, description=None):
    if description:
        print(f"🚀 {description} 중...")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"❌ 에러 발생: {e.stderr}")
        return None

def get_video_metadata(url):
    print("🔍 영상 정보를 분석하는 중...")
    cmd = ["yt-dlp", "--get-title", "--get-description", "--skip-download", url]
    output = run_command(cmd)
    if not output: return None, []
    
    lines = output.split('\n')
    title = lines[0].strip()
    description = '\n'.join(lines[1:])
    
    ts_pattern = re.compile(r'(\d{1,2}:\d{2}(?::\d{2})?)\s*(?:[-:.\s])\s*(.+)')
    timestamps = ts_pattern.findall(description)
    
    unique_ts = []
    seen_times = set()
    for ts, name in timestamps:
        if ts not in seen_times:
            unique_ts.append((ts, name.strip()))
            seen_times.add(ts)
            
    return title, unique_ts

def parse_vtt_time(vtt_time):
    return vtt_time.split('.')[0]

def get_full_transcript_list(url):
    print("🎬 유튜브 자막(CC) 데이터를 가져오는 중...")
    temp_prefix = "temp_subs_full"
    cmd = [
        "yt-dlp", "--write-auto-subs", "--skip-download", 
        "--sub-langs", "ko", "-o", temp_prefix, url
    ]
    run_command(cmd)
    
    vtt_file = list(Path('.').glob(f"{temp_prefix}*.vtt"))
    if not vtt_file: return []
    
    full_transcript_list = []
    try:
        with open(vtt_file[0], 'r', encoding='utf-8') as f:
            content = f.read()
            blocks = content.split('\n\n')
            for block in blocks:
                if '-->' in block:
                    lines = block.split('\n')
                    time_info = lines[0].split(' --> ')[0]
                    text = ' '.join(lines[1:]).strip()
                    if text:
                        full_transcript_list.append({
                            "time": parse_vtt_time(time_info),
                            "text": text
                        })
    finally:
        for f in vtt_file: os.remove(f)
        
    return full_transcript_list

def get_timestamps_from_visual(video_path):
    if not HAS_CV2:
        print("ℹ️ OpenCV가 설치되지 않아 시각 분석을 건너뜁니다.")
        return []

    print("🖼️ 좌상단 제목 변화를 시각적으로 감지하는 중 (정밀 분석)...")
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        return []

    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    # 5초 간격으로 샘플링
    interval = int(fps * 5)
    
    detected_ts = []
    prev_roi = None
    
    for fno in range(0, total_frames, interval):
        cap.set(cv2.CAP_PROP_POS_FRAMES, fno)
        ret, frame = cap.read()
        if not ret: break
        
        # 좌상단 영역 (제목이 나오는 곳 - 1280x720 기준 약 0:300, 0:100 영역)
        # 영상 크기에 따라 비율로 설정 (좌상단 25% 영역)
        h, w = frame.shape[:2]
        roi = frame[int(h*0.05):int(h*0.15), int(w*0.05):int(w*0.35)]
        gray_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        
        if prev_roi is not None:
            # 이미지 차이 계산
            diff = cv2.absdiff(gray_roi, prev_roi)
            score = np.sum(diff) / (roi.size)
            
            # 변화가 크면 (제목이 바뀌었을 가능성)
            if score > 15: # 임계값은 실험적 수치
                sec = int(fno / fps)
                m, s = divmod(sec, 60)
                h_val, m = divmod(m, 60)
                ts_str = f"{h_val:02d}:{m:02d}:{s:02d}" if h_val > 0 else f"{m:02d}:{s:02d}"
                detected_ts.append(ts_str)
        
        prev_roi = gray_roi
    
    cap.release()
    return detected_ts

def refine_timestamps_with_gemini(transcript_list, visual_ts_list):
    api_key = load_gemini_key()
    if not api_key: return []
    
    print("🧠 시각적 변화와 자막 맥락을 결합하여 최적의 사연 목차를 생성 중...")
    client = genai.Client(api_key=api_key)
    
    # 전체 자막 요약 (토큰 절약을 위해 띄엄띄엄 추출)
    sample_size = 2000
    step = max(1, len(transcript_list) // sample_size)
    sampled_text = "\n".join([f"[{item['time']}] {item['text']}" for item in transcript_list[::step]])
    
    visual_info = ", ".join(visual_ts_list)
    
    prompt = f"""
유튜브 영상의 자막 샘플과 '시각적 제목 변경 예상 지점' 리스트입니다.
이 정보를 종합하여 100분 영상 속의 '진짜 사연'들이 시작되는 지점만 골라주세요.

**참고 사항:**
1. 시각적 변화 감지 지점: {visual_info} (이 근처에서 제목이 바뀔 확률이 높음)
2. 자막 샘플을 참고하여 실제 이야기의 맥락이 바뀌는 '정확한 시간'과 '사연 제목'을 확정하세요.
3. 너무 잘게 나누지 말고, 큼직큼직하게(하나의 사연 단위로) 5~10개 내외로 나눠주세요.

**출력 형식 (JSON 배열만 출력할 것):**
[
  {{"time": "00:00:00", "title": "사연 제목1"}},
  {{"time": "00:15:30", "title": "사연 제목2"}}
]

**자막 샘플:**
{sampled_text}
"""
    try:
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=prompt,
            config=types.GenerateContentConfig(response_mime_type="application/json")
        )
        raw_text = response.text.strip()
        if raw_text.startswith("```"):
            raw_text = re.sub(r'```(?:json)?\n?|```', '', raw_text)
        
        data = json.loads(raw_text)
        return [(item['time'], item['title']) for item in data]
    except Exception as e:
        print(f"❌ Gemini 정제 실패: {e}")
        return []

def download_full_video(url, title):
    safe_title = re.sub(r'[^\w\s-]', '', title).strip().replace(' ', '_')
    output_path = DOWNLOADS_DIR / f"{safe_title}_full.mp4"
    
    if output_path.exists():
        print(f"ℹ️ 이미 원본 파일이 존재합니다: {output_path.name}")
        return output_path
        
    print(f"📥 전체 영상 다운로드 시작: {title}")
    cmd = [
        "yt-dlp",
        "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "-o", str(output_path),
        url
    ]
    subprocess.run(cmd)
    return output_path

def split_video(full_path, timestamps):
    video_name = full_path.stem.replace('_full', '')
    split_dir = DOWNLOADS_DIR / f"{video_name}_clips"
    split_dir.mkdir(parents=True, exist_ok=True)
    
    clips = []
    print(f"\n✂️ 총 {len(timestamps)}개의 구간으로 정밀 분할을 시작합니다...")
    
    for i in range(len(timestamps)):
        start_time = timestamps[i][0]
        end_time = timestamps[i+1][0] if i + 1 < len(timestamps) else None
        
        info_text = timestamps[i][1]
        safe_info = re.sub(r'[^\w\s-]', '', info_text).strip().replace(' ', '_')[:30]
        output_filename = f"{i+1:02d}_{safe_info}.mp4"
        output_path = split_dir / output_filename
        
        cmd = ["ffmpeg", "-y", "-ss", start_time]
        if end_time: cmd += ["-to", end_time]
        cmd += ["-i", str(full_path), "-c", "copy", "-avoid_negative_ts", "1", str(output_path)]
        
        print(f"   [{i+1}/{len(timestamps)}] 분할 완료: {output_filename}")
        subprocess.run(cmd, capture_output=True)
        clips.append(output_path)
    
    return clips

def main():
    print("==========================================")
    print("📺 유튜브 전체 다운로드 & 시각 기반 지능형 분할(V3)")
    print("==========================================")
    
    url = input("🔗 유튜브 URL을 입력하세요: ").strip()
    if not url: return

    title, timestamps_desc = get_video_metadata(url)
    if not title: return

    # 1. 원본 다운로드 (시각 분석을 위해 먼저 필요함)
    full_path = download_full_video(url, title)
    if not full_path or not full_path.exists(): return

    # 2. 목차가 설명란에 없으면 시각 분석 실시
    if not timestamps_desc:
        print("ℹ️ 설명란 정보가 부족합니다. 좌상단 제목 변화를 감지합니다.")
        visual_ts = get_timestamps_from_visual(full_path)
        transcript_list = get_full_transcript_list(url)
        
        if visual_ts and transcript_list:
            timestamps = refine_timestamps_with_gemini(transcript_list, visual_ts)
        else:
            timestamps = []
    else:
        timestamps = timestamps_desc

    if not timestamps:
        print("❌ 분할할 구간을 찾지 못했습니다.")
        return

    # 사용자 확인 단계
    print("\n📍 시각적 변화를 반영한 정밀 목차:")
    for i, (ts, desc) in enumerate(timestamps, 1):
        print(f"{i}) {ts} - {desc}")
    
    if input("\n👉 이 목차대로 사연별 분할을 진행하시겠습니까? (Y/n): ").lower() == 'n':
        return

    # 3. 구간 분할
    clips = split_video(full_path, timestamps)
    
    # 4. 각 클립별 에셋 추출
    print(f"\n🎙️ 분할된 {len(clips)}개 사연에서 음성/자막을 바로 추출할까요?")
    print("   1) 고속 추출 (음성 분리 생략, 자막만 생성)")
    print("   2) 고품질 추출 (음성 분리 포함, 10~20분 소요)")
    print("   n) 나중에 하기")
    
    extract_choice = input("👉 선택하세요 (1/2/n): ").strip().lower()
    
    if extract_choice in ['1', '2']:
        is_fast = extract_choice == '1'
        for i, clip in enumerate(clips):
            print(f"\n🚀 [{i+1}/{len(clips)}] 에셋 추출 중 {'(고속)' if is_fast else ''}: {clip.name}")
            cmd = [PYTHON_EXE, str(EXTRACTOR_SCRIPT), str(clip)]
            if is_fast:
                cmd.append("--fast")
            subprocess.run(cmd)

    print("\n" + "="*40)
    print("✨ 모든 작업이 성공적으로 완료되었습니다!")
    print(f"📂 결과물 확인: {full_path.parent}")
    print("="*40)
    os.system(f"open {full_path.parent}")

if __name__ == "__main__":
    main()

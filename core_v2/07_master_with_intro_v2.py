import os
import subprocess
import re
import sys
import time
import json

# [설정] FFmpeg 및 작업 경로
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if os.path.basename(SCRIPT_DIR) == "core_v2":
    ROOT_DIR = os.path.dirname(SCRIPT_DIR)
    CORE_DIR = SCRIPT_DIR
else:
    ROOT_DIR = SCRIPT_DIR
    CORE_DIR = os.path.join(ROOT_DIR, "core_v2")

BASE_DIR = CORE_DIR

conda_ffmpeg = os.path.join(os.path.dirname(sys.executable), "ffmpeg")
FFMPEG_EXE = conda_ffmpeg if os.path.exists(conda_ffmpeg) else "ffmpeg"
DOWNLOADS_DIR = os.path.join(os.path.expanduser("~"), "Downloads")

INTRO_DURATION = 8.0  # 인트로 길이 (초)

def get_latest_folder():
    folders = [os.path.join(DOWNLOADS_DIR, d) for d in sorted(os.listdir(DOWNLOADS_DIR)) 
               if os.path.isdir(os.path.join(DOWNLOADS_DIR, d)) and (d.startswith("무협_생성_") or d.startswith("무협_로컬생성_") or d.startswith("무협_세로_") or d.startswith("다이어리_세로_"))]
    if not folders: return None
    return max(folders, key=os.path.getmtime)

def get_latest_srt():
    srt_files = [os.path.join(DOWNLOADS_DIR, f) for f in os.listdir(DOWNLOADS_DIR) 
                 if f.lower().endswith(".srt") and "_Full_Merged" in f]
    if not srt_files: return None
    return max(srt_files, key=os.path.getmtime)

def get_master_audio():
    candidates = [os.path.join(DOWNLOADS_DIR, f) for f in os.listdir(DOWNLOADS_DIR) 
                  if ("_V3-9_SFX_ONLY_" in f or "_V3-8_SRTInterval_" in f or "_V3-7_TimeInterval_" in f) and f.lower().endswith(".mp3")]
    if candidates:
        return max(candidates, key=os.path.getmtime)
    candidates = [os.path.join(DOWNLOADS_DIR, f) for f in os.listdir(DOWNLOADS_DIR) 
                  if "_Full_Merged" in f and f.lower().endswith(".mp3")]
    if candidates:
        return max(candidates, key=os.path.getmtime)
    return None

def srt_time_to_seconds(srt_time_str):
    h, m, s_ms = srt_time_str.split(':')
    s, ms = s_ms.split(',')
    return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000.0

def seconds_to_ass(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h}:{m:02d}:{s:05.2f}"

def parse_srt_and_shift(srt_path, shift_sec):
    if not srt_path or not os.path.exists(srt_path): return []
    events = []
    try:
        with open(srt_path, 'r', encoding='utf-8-sig') as f:
            content = f.read()
        pattern = re.compile(r'(\d+)\n(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})\n(.*?)(?=\n\d+\n|\Z)', re.DOTALL)
        matches = pattern.findall(content)
        for m in matches:
            idx, start_srt, end_srt, text = m
            start_sec = srt_time_to_seconds(start_srt) + shift_sec
            end_sec = srt_time_to_seconds(end_srt) + shift_sec
            events.append({
                'start': seconds_to_ass(start_sec),
                'end': seconds_to_ass(end_sec),
                'text': text.strip()
            })
        print(f"✅ SRT 파싱 및 {shift_sec}초 시프트 완료: {len(events)}개 자막")
    except Exception as e:
        print(f"⚠️ SRT 파싱 중 오류: {e}")
    return events

def smart_wrap(text, max_len=14):
    text = text.replace('\\N', ' ').replace('\n', ' ').replace('.', '').strip()
    words = text.split()
    lines = []
    current_line = []
    current_length = 0
    for word in words:
        if current_length + len(word) + (1 if current_line else 0) <= max_len:
            current_line.append(word)
            current_length += len(word) + (1 if current_line else 0)
        else:
            if current_line: lines.append(" ".join(current_line))
            current_line = [word]
            current_length = len(word)
    if current_line: lines.append(" ".join(current_line))
    return "\\N".join(lines[:2])

def run_integrated_render():
    print("\n🏆 [STEP 07] 인트로 통합 마스터 렌더링")
    target_dir = get_latest_folder()
    if not target_dir: print("❌ 폴더 없음"); return
    
    dir_name = os.path.basename(target_dir)
    is_vertical = "세로_" in dir_name
    srt_file = get_latest_srt()
    master_audio = get_master_audio()
    
    if not master_audio: print("❌ 오디오 없음"); return

    video_files = [f for f in sorted(os.listdir(target_dir)) if f.lower().endswith(".mp4") and "합본" not in f]
    def natural_keys(text): return [int(c) if c.isdigit() else c for c in re.split(r'(\d+)', text)]
    video_files.sort(key=natural_keys)

    mylist_path = os.path.join(target_dir, "mylist.txt")
    with open(mylist_path, "w", encoding="utf-8") as f:
        for v in video_files:
            safe_v = v.replace("'", "'\\''")
            f.write(f"file '{safe_v}'\n")

    srt_events = parse_srt_and_shift(srt_file, INTRO_DURATION)
    ass_path = os.path.join(target_dir, "final.ass")
    
    res_x, res_y = (1080, 1920) if is_vertical else (1280, 720)
    font_size = 180 if is_vertical else 80
    max_len = 12 if is_vertical else 20

    ass_header = f"[Script Info]\nScriptType: v4.00+\nPlayResX: {res_x}\nPlayResY: {res_y}\n\n[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\nStyle: Default,Arial,{font_size},&H0000FFFF,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,3,5,2,10,10,100,1\n\n[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
    with open(ass_path, "w", encoding="utf-8") as f:
        f.write(ass_header)
        for ev in srt_events:
            content = smart_wrap(ev['text'], max_len=max_len)
            if content: f.write(f"Dialogue: 0,{ev['start']},{ev['end']},Default,,0,0,0,,{content}\n")

    shifted_audio = os.path.join(target_dir, "master_shifted.mp3")
    print("⏳ 오디오 8초 시프트 중...")
    try:
        subprocess.run([FFMPEG_EXE, "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo", "-i", master_audio, 
                        "-filter_complex", "[0:a][1:a]concat=n=2:v=0:a=1", "-t", "500", shifted_audio], check=True, capture_output=True)
    except: pass # t 값은 넉넉하게

    output_name = f"무협_인트로합본_{int(time.time())%1000:03d}.mp4"
    current_cwd = os.getcwd()
    os.chdir(target_dir)
    
    # FFmpeg: Concat video from mylist, use shifted audio, add subtitles
    cmd = [FFMPEG_EXE, "-y", "-f", "concat", "-safe", "0", "-i", "mylist.txt", "-i", "master_shifted.mp3",
           "-filter_complex", "[0:v]subtitles=filename='final.ass'[vout]", "-map", "[vout]", "-map", "1:a",
           "-c:v", "libx264", "-preset", "ultrafast", "-b:v", "5000k", output_name]
    
    print(f"🎬 최종 렌더링 시작...")
    subprocess.run(cmd, check=True)
    print(f"✨ 완성! {os.path.join(target_dir, output_name)}")
    os.chdir(current_cwd)

if __name__ == "__main__":
    run_integrated_render()

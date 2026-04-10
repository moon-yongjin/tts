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
    # 0. SFX ONLY 또는 최신 통합 오디오 파일 우선
    candidates = [os.path.join(DOWNLOADS_DIR, f) for f in os.listdir(DOWNLOADS_DIR) 
                  if ("_V3-9_SFX_ONLY_" in f or "_V3-8_SRTInterval_" in f or "_V3-7_TimeInterval_" in f) and f.lower().endswith(".mp3")]
    if candidates:
        return max(candidates, key=os.path.getmtime)
    
    # 1. Fallback: 일반 합본
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
    # ASS 형식: H:MM:SS.CC (Centiseconds)
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
        print(f"✅ SRT {shift_sec}초 시프트 완료")
    except Exception as e:
        print(f"⚠️ SRT 파싱 오류: {e}")
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

def run_render_intro_fix():
    print("\n🚀 [FINAL] 인트로 통합 마스터 렌더링 (폰트/싱크 수정본)")
    
    target_dir = get_latest_folder()
    if not target_dir: print("❌ 폴더 없음"); return
    
    is_vertical = "세로_" in os.path.basename(target_dir)
    srt_file = get_latest_srt()
    master_audio = get_master_audio()
    if not master_audio: print("❌ 오디오 없음"); return

    # 1. 자막 설정 로드 (사용자 설정 준수)
    conf_path = os.path.join(ROOT_DIR, "core_v2", "subtitle_config.json")
    sub_conf = {}
    if os.path.exists(conf_path):
        with open(conf_path, "r", encoding="utf-8") as f:
            full_conf = json.load(f)
            sub_conf = full_conf.get("vertical" if is_vertical else "horizontal", {})
    
    font_size = sub_conf.get("font_size", 80)
    margin_v = sub_conf.get("margin_v", 450 if is_vertical else 40)
    outline = sub_conf.get("outline", 4)
    shadow = sub_conf.get("shadow", 2)
    max_len = sub_conf.get("max_len", 35 if is_vertical else 20)
    alignment = sub_conf.get("alignment", 2)
    res_x, res_y = (1080, 1920) if is_vertical else (1280, 720)

    print(f"⚙️ 폰트 크기: {font_size}, 세로 여백: {margin_v}")

    # 2. 비디오 파일 목록 구성 (000_intro.mp4 포함 여부 확인)
    video_files = [f for f in sorted(os.listdir(target_dir)) if f.lower().endswith(".mp4") and "합본" not in f]
    def natural_keys(text): return [int(c) if c.isdigit() else c for c in re.split(r'(\d+)', text)]
    video_files.sort(key=natural_keys)

    mylist_path = os.path.join(target_dir, "mylist.txt")
    with open(mylist_path, "w", encoding="utf-8") as f:
        for v in video_files:
            safe_v = v.replace("'", "'\\''")
            f.write(f"file '{safe_v}'\n")

    # 3. 자막 ASS 생성 (8초 시프트)
    srt_events = parse_srt_and_shift(srt_file, INTRO_DURATION)
    ass_path = os.path.join(target_dir, "final_fix.ass")
    ass_header = f"[Script Info]\nScriptType: v4.00+\nPlayResX: {res_x}\nPlayResY: {res_y}\n\n[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\nStyle: Default,Arial,{font_size},&H0000FFFF,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,{outline},{shadow},{alignment},10,10,{margin_v},1\n\n[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
    with open(ass_path, "w", encoding="utf-8") as f:
        f.write(ass_header)
        for ev in srt_events:
            content = smart_wrap(ev['text'], max_len=max_len)
            if content: f.write(f"Dialogue: 0,{ev['start']},{ev['end']},Default,,0,0,0,,{content}\n")

    # 4. 오디오 시프트 (인트로 오디오 8초 + 메인 오디오)
    shifted_audio = os.path.join(target_dir, "master_shifted_fix.mp3")
    print("⏳ 인트로 오디오와 메인 오디오 합성 중...")
    intro_mp4 = os.path.join(target_dir, "000_intro.mp4")
    
    # [수정] 인트로 영상의 오디오를 8초간 사용하고, 메인 오디오는 8초 뒤에 시작하게 합성
    cmd_audio = [FFMPEG_EXE, "-y", "-i", intro_mp4, "-i", master_audio,
                 "-filter_complex", 
                 f"[0:a]atrim=0:{INTRO_DURATION},asetpts=PTS-STARTPTS[intro_a];"
                 f"[1:a]adelay={int(INTRO_DURATION*1000)}|{int(INTRO_DURATION*1000)}[story_a];"
                 f"[intro_a][story_a]amix=inputs=2:duration=longest:dropout_transition=0", 
                 shifted_audio]
    subprocess.run(cmd_audio, check=True, capture_output=True)

    # 5. 최종 렌더링
    output_name = f"무협_인트로최종_{int(time.time())%1000:03d}.mp4"
    current_cwd = os.getcwd()
    os.chdir(target_dir)

    # 오디오 길이 확인 (트리밍용)
    try:
        audio_dur_cmd = [FFMPEG_EXE, "-i", "master_shifted_fix.mp3", "-show_entries", "format=duration", "-v", "quiet", "-of", "csv=p=0"]
        total_audio_duration = float(subprocess.check_output(audio_dur_cmd).decode().strip())
        print(f"🎵 최종 오디오 길이: {total_audio_duration}초")
    except:
        total_audio_duration = 200 # Fallback

    cmd_render = [FFMPEG_EXE, "-y", "-f", "concat", "-safe", "0", "-i", "mylist.txt", "-i", "master_shifted_fix.mp3",
                  "-filter_complex", "[0:v]subtitles=filename='final_fix.ass'[vout]", "-map", "[vout]", "-map", "1:a",
                  "-c:v", "libx264", "-preset", "ultrafast", "-crf", "24", "-b:v", "5000k", "-shortest", "-t", str(total_audio_duration), output_name]
    
    print(f"🎬 최종 렌더링 시작 ({output_name})")
    subprocess.run(cmd_render, check=True)
    print(f"✅ 완성! {os.path.join(target_dir, output_name)}")
    os.chdir(current_cwd)

if __name__ == "__main__":
    run_render_intro_fix()

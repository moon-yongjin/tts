import os
import subprocess
import re
import sys

# [설정] FFmpeg 및 작업 경로
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FFMPEG_DIR = os.path.join(BASE_DIR, "ffmpeg", "ffmpeg-2026-01-07-git-af6a1dd0b2-essentials_build", "bin")
FFMPEG_EXE = "ffmpeg"
FFPROBE_EXE = "ffprobe"
DOWNLOADS_DIR = os.path.join(os.path.expanduser("~"), "Downloads")

def get_latest_folder():
    folders = [os.path.join(DOWNLOADS_DIR, d) for d in os.listdir(DOWNLOADS_DIR) 
               if os.path.isdir(os.path.join(DOWNLOADS_DIR, d)) and d.startswith("무협_생성_")]
    if not folders:
        return None
    return max(folders, key=os.path.getmtime)

def get_latest_srt():
    srt_files = [os.path.join(DOWNLOADS_DIR, f) for f in os.listdir(DOWNLOADS_DIR) 
                 if f.lower().endswith(".srt")]
    if not srt_files:
        return None
    return max(srt_files, key=os.path.getmtime)

def get_latest_mp3():
    mp3_files = [os.path.join(DOWNLOADS_DIR, f) for f in os.listdir(DOWNLOADS_DIR) 
                 if f.lower().endswith(".mp3")]
    if not mp3_files:
        return None
    return max(mp3_files, key=os.path.getmtime)

def srt_time_to_ass(srt_time_str):
    h, m, s_ms = srt_time_str.split(':')
    s, ms = s_ms.split(',')
    return f"{int(h)}:{m}:{s}.{ms[:2]}"

def parse_srt(srt_path):
    if not srt_path or not os.path.exists(srt_path):
        return []
    events = []
    with open(srt_path, 'r', encoding='utf-8-sig') as f:
        content = f.read()
    blocks = re.split(r'\n\s*\n', content.strip())
    for block in blocks:
        lines = block.splitlines()
        if len(lines) >= 3:
            times = re.findall(r'(\d{2}:\d{2}:\d{2},\d{3})', lines[1])
            if len(times) >= 2:
                start = srt_time_to_ass(times[0])
                end = srt_time_to_ass(times[1])
                text = " ".join(lines[2:])
                events.append({'start': start, 'end': end, 'text': text})
    return events

def smart_wrap(text, max_len=14):
    text = text.replace('\\N', ' ').replace('\n', ' ').replace('.', '').strip()
    if len(text) > max_len:
        text = text[:max_len].strip()
    return text

def run_integrated_render():
    print("🚀 [Mu-hyup Master Full] 영상 + 자막 + 음성 통합 렌더링을 시작합니다...")
    
    # 1. 최신 폴더 및 파일 찾기
    target_dir = get_latest_folder()
    if not target_dir:
        print("❌ '무협_생성_'으로 시작하는 폴더를 찾을 수 없습니다.")
        return
    
    srt_file = get_latest_srt()
    mp3_file = get_latest_mp3()
    
    print(f"📂 대상 비디오 폴더: {target_dir}")
    if srt_file: print(f"📄 사용 자막 파일: {os.path.basename(srt_file)}")
    if mp3_file: print(f"🎵 사용 음성 파일: {os.path.basename(mp3_file)}")

    # 2. 비디오 파일 목록 구성 및 정렬
    video_files = [f for f in os.listdir(target_dir) if f.lower().endswith(".mp4") and "합본" not in f]
    def natural_keys(text):
        return [int(c) if c.isdigit() else c for c in re.split(r'(\d+)', text)]
    video_files.sort(key=natural_keys)
    
    if not video_files:
        print("❌ 합칠 수 있는 MP4 파일이 없습니다.")
        return

    # 3. 자막 파싱 및 ASS 생성
    srt_events = parse_srt(srt_file) if srt_file else []
    
    mylist_path = os.path.join(target_dir, "mylist.txt")
    with open(mylist_path, "w", encoding="utf-8") as f:
        for video in video_files:
            safe_name = video.replace("'", "'\\''")
            f.write(f"file '{safe_name}'\n")

    ass_path = os.path.join(target_dir, "final.ass")
    ass_header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Cafe24 Ohsquare,180,&H00FFFFFF,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,3,5,2,10,10,100,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    with open(ass_path, "w", encoding="utf-8") as f:
        f.write(ass_header)
        for ev in srt_events:
            content = smart_wrap(ev['text'], 14)
            if content:
                # \fax-0.1 태그로 미세 기울기 적용
                f.write(f"Dialogue: 0,{ev['start']},{ev['end']},Default,,0,0,0,,{{\\fax-0.1}}{content}\n")

    # 4. 카운팅 로직
    counter_file = os.path.join(BASE_DIR, "global_counter.txt")
    if os.path.exists(counter_file):
        with open(counter_file, "r") as f:
            try: count = int(f.read().strip()) + 1
            except: count = 1
    else: count = 1
    with open(counter_file, "w") as f: f.write(str(count))

    output_file = os.path.join(target_dir, f"무협_최종_합본_자막_음성_{count:03d}.mp4")
    ass_path_fixed = os.path.abspath(ass_path).replace('\\', '/').replace(':', '\\:')
    fonts_dir = BASE_DIR.replace('\\', '/').replace(':', '\\:')

    # 5. FFmpeg 실행 (병합 + 자막 + 음성 합치기)
    cmd = [
        FFMPEG_EXE, "-f", "concat", "-safe", "0", "-i", mylist_path
    ]
    
    # 음성 파일이 있으면 입력을 추가
    if mp3_file:
        cmd.extend(["-i", mp3_file])
    
    # 필터 및 맵핑 설정
    cmd.extend([
        "-vf", f"subtitles='{ass_path_fixed}':fontsdir='{fonts_dir}'",
    ])
    
    if mp3_file:
        # 0번 입력(비디오 CONCAT)에서 비디오 가져오고, 1번 입력(MP3)에서 오디오 가져오기
        # -shortest: 더 짧은 쪽에 맞춰 종료 (보통 음성 기준)
        cmd.extend(["-map", "0:v", "-map", "1:a", "-shortest"])
    else:
        # 음성 없으면 그냥 영상만
        cmd.extend(["-c:a", "aac", "-b:a", "192k"])

    cmd.extend([
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "28", "-b:v", "3000k",
        "-y", output_file
    ])
    
    print(f"🎬 통합 렌더링 진행 중... (Output: {os.path.basename(output_file)})")
    try:
        subprocess.run(cmd, check=True, cwd=target_dir)
        print(f"✨ 완성! 결과물: {output_file}")
        os.remove(mylist_path)
    except subprocess.CalledProcessError as e:
        print(f"❌ 렌더링 실패: {e}")

if __name__ == "__main__":
    run_integrated_render()

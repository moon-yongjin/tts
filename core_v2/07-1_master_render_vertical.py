import os
import subprocess
import re
import math
import glob
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

# [변경] FFmpeg 경로 자동식별 (Conda 환경 내 ffmpeg 사용)
conda_ffmpeg = os.path.join(os.path.dirname(sys.executable), "ffmpeg")
if os.path.exists(conda_ffmpeg):
    FFMPEG_EXE = conda_ffmpeg
else:
    FFMPEG_EXE = "ffmpeg"

DOWNLOADS_DIR = os.path.join(os.path.expanduser("~"), "Downloads")

def get_latest_folder():
    folders = [os.path.join(DOWNLOADS_DIR, d) for d in sorted(os.listdir(DOWNLOADS_DIR)) 
               if os.path.isdir(os.path.join(DOWNLOADS_DIR, d)) and (d.startswith("무협_생성_") or d.startswith("무협_로컬생성_") or d.startswith("무협_세로_"))]
    if not folders: return None
    return max(folders, key=os.path.getmtime)

def get_latest_srt():
    srt_files = [os.path.join(DOWNLOADS_DIR, f) for f in os.listdir(DOWNLOADS_DIR) 
                 if f.lower().endswith(".srt") and "_Full_Merged" in f]
    if not srt_files: return None
    return max(srt_files, key=os.path.getmtime)

def get_master_audio():
    """ 최종 마스터 오디오(AI SFX 또는 효과음합본) 하나만 찾기 """
    # 0. AI Time-Based Director 통합 파일 (V3-7 신규)
    candidates = [os.path.join(DOWNLOADS_DIR, f) for f in os.listdir(DOWNLOADS_DIR) 
                  if ("_V3-9_SFX_ONLY_" in f or "_V3-8_SRTInterval_" in f or "_V3-7_TimeInterval_" in f) and f.lower().endswith(".mp3")]
    if candidates:
        return max(candidates, key=os.path.getmtime)

    # 1. 효과음합본 (V3-3 구버전)
    candidates = [os.path.join(DOWNLOADS_DIR, f) for f in os.listdir(DOWNLOADS_DIR) 
                  if "_효과음합본" in f and f.lower().endswith(".mp3")]
    if candidates:
        return max(candidates, key=os.path.getmtime)
        
    # 2. 없다면 일반 합본 (Fallback)
    candidates = [os.path.join(DOWNLOADS_DIR, f) for f in os.listdir(DOWNLOADS_DIR) 
                  if "_Full_Merged" in f and f.lower().endswith(".mp3")]
    if candidates:
        return max(candidates, key=os.path.getmtime)
    
    return None
    
def get_audio_duration_ffprobe(audio_path):
    """ ffprobe를 사용하여 오디오의 정확한 초 단위 길이를 가져옵니다. """
    try:
        ffprobe_exe = FFMPEG_EXE.replace("ffmpeg", "ffprobe")
        cmd = [
            ffprobe_exe, "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", audio_path
        ]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        return float(result.stdout.strip())
    except:
        return None

def srt_to_seconds(srt_time_str):
    h, m, s_ms = srt_time_str.split(':')
    s, ms = s_ms.split(',')
    return int(h)*3600 + int(m)*60 + int(s) + int(ms)/1000

def seconds_to_ass(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h}:{m:02d}:{s:05.2f}"

def parse_srt(srt_path):
    if not srt_path or not os.path.exists(srt_path): return []
    events = []
    try:
        with open(srt_path, 'r', encoding='utf-8-sig') as f:
            content = f.read()
        
        # 정규표현식으로 각 블록 추출 (인덱스 \n 시간 \n 텍스트)
        pattern = re.compile(r'(\d+)\n(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})\n(.*?)(?=\n\d+\n|\Z)', re.DOTALL)
        matches = pattern.findall(content)
        
        for m in matches:
            idx, start_srt, end_srt, text = m
            text = text.strip()
            if text:
                events.append({
                    'start': seconds_to_ass(srt_to_seconds(start_srt) + 0.5),
                    'end': seconds_to_ass(srt_to_seconds(end_srt) + 0.5),
                    'text': text
                })
        print(f"✅ SRT 파싱 완료: {len(events)}개의 자막 블록 로드됨")
    except Exception as e:
        print(f"⚠️ SRT 파싱 중 오류: {e}")
    return events

def smart_wrap(text, max_len=14):
    """ 자막을 자르지 않고 여러 줄(\\N)로 나눕니다. """
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
            if current_line:
                lines.append(" ".join(current_line))
            current_line = [word]
            current_length = len(word)
    
    if current_line:
        lines.append(" ".join(current_line))
    
    # 01-3에서 이미 쪼개왔으므로, 여기서는 다 보여주되 안전하게 2줄까지만 리턴
    return "\\N".join(lines[:2])

def run_integrated_render():
    print("\n" + "="*50)
    print("🏆 [STEP 07] 마스터 통합 렌더링 (지능형 가로/세로 감지)")
    print("="*50)
    
    # 1. 파일 찾기
    target_dir = get_latest_folder()
    if not target_dir: 
        print("❌ 작업 폴더를 찾을 수 없습니다."); return
    
    dir_name = os.path.basename(target_dir)
    is_vertical = "무협_세로_" in dir_name
    
    srt_file = get_latest_srt()
    
    master_audio = get_master_audio()
    
    print(f"📂 대상 비디오: {dir_name} ({'세로' if is_vertical else '가로'} 모드)")
    
    if master_audio:
        print(f"🎙️ 오디오 소스: {os.path.basename(master_audio)}")
    else:
        print("❌ 사용할 오디오 파일을 찾을 수 없습니다.")
        return

    # 2. 비디오 파일 목록 구성
    video_files = [f for f in sorted(os.listdir(target_dir)) if f.lower().endswith(".mp4") and "합본" not in f]
    def natural_keys(text): return [int(c) if c.isdigit() else c for c in re.split(r'(\d+)', text)]
    video_files.sort(key=natural_keys)
    
    if not video_files: print("❌ 비디오 파일이 없습니다."); return

    # 3. CONCAT 리스트 및 ASS 자막 생성
    mylist_path = os.path.join(target_dir, "mylist.txt")
    with open(mylist_path, "w", encoding="utf-8") as f:
        for v in video_files:
            safe_v = v.replace("'", "'\\''")
            f.write(f"file '{safe_v}'\n")

    srt_events = parse_srt(srt_file)
    ass_path = os.path.join(target_dir, "final.ass")
    
    # 자막 설정 로드
    conf_path = os.path.join(BASE_DIR, "subtitle_config.json")
    sub_conf = {}
    if os.path.exists(conf_path):
        try:
            with open(conf_path, "r", encoding="utf-8") as f:
                full_conf = json.load(f)
                sub_conf = full_conf.get("vertical" if is_vertical else "horizontal", {})
                print(f"⚙️ 자막 설정 로드됨 ({'세로' if is_vertical else '가로'})")
        except: pass

    # 해상도 및 자막 스타일 지능적 전환 (Config 기반)
    if is_vertical:
        res_x, res_y = 1080, 1920
        font_size = sub_conf.get("font_size", 180)
        margin_v = sub_conf.get("margin_v", 100)
    else:
        res_x, res_y = 1280, 720
        font_size = sub_conf.get("font_size", 80)
        margin_v = sub_conf.get("margin_v", 40)

    margin_l = sub_conf.get("margin_l", 10)
    margin_r = sub_conf.get("margin_r", 10)
    alignment = sub_conf.get("alignment", 2)
    outline = sub_conf.get("outline", 3)
    shadow = sub_conf.get("shadow", 5)
    max_len = sub_conf.get("max_len", 12 if is_vertical else 20)

    # 자막 스타일 설정 (Cafe24 단정해 + 가벼운 그림자)
    # 그림자 감소: Shadow=1
    ass_header = f"[Script Info]\nScriptType: v4.00+\nPlayResX: {res_x}\nPlayResY: {res_y}\n\n[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\nStyle: Default,Cafe24 Danjeonghae,{font_size},&H00FFFFFF,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,2,1,2,60,60,{margin_v},1\n\n[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
    
    with open(ass_path, "w", encoding="utf-8") as f:
        f.write(ass_header)
        for ev in srt_events:
            content = smart_wrap(ev['text'], max_len=max_len)
            if content: f.write(f"Dialogue: 0,{ev['start']},{ev['end']},Default,,0,0,0,,{content}\n")

    # 4. 결과 파일명 설정 (완전 별개 이름으로 생성하여 착각 방지)
    output_name = f"PREMIUM_VERTICAL_FINAL_{int(time.time())%1000:03d}.mp4"
    output_file = os.path.join(target_dir, output_name)
    ass_path_fixed = os.path.abspath(ass_path).replace('\\', '/').replace(':', '\\:')
    fonts_dir = BASE_DIR.replace('\\', '/').replace(':', '\\:')

    # 5. FFmpeg 실행 (작업 디렉토리를 이동하여 상대 경로로 처리 - Mac/Linux 호환성 최상)
    # [중요] 절대경로의 콜론(:) 문제로 인해 자막이 안 나오는 경우가 많음. 상대경로가 정답.
    current_cwd = os.getcwd()
    os.chdir(target_dir)

    # 마스터 오디오도 상대 경로로 변환 (같은 폴더면 파일명만, 아니면 절대)
    rel_audio = os.path.relpath(master_audio, target_dir)

    cmd = [FFMPEG_EXE, "-y", "-f", "concat", "-safe", "0", "-i", "mylist.txt"]
    cmd.extend(["-i", rel_audio])
    
    # [초극강 보안] Mac FFmpeg용 특수 경로 처리 (Escaping)
    # 절대경로의 콜론(:)을 완벽하게 탈출시켜야 자막이 화상에 입혀집니다.
    abs_ass = os.path.abspath("final.ass").replace(":", "\\:").replace("'", "'\\\\\\''")
    # [Pad Fix] 시작/끝 0.5초 블랙 패딩 + 자막 입히기
    # [Pad Fix] 시작/끝 0.5초 블랙 패딩 + 자막 입히기
    v_filter = f"[0:v]tpad=start_duration=0.5:stop_duration=0.5:color=black,subtitles=filename='{abs_ass}'[vout]"
    # [Sync Fix]adelay=500:all=1 은 모든 채널에 공통 딜레이 적용 (Mono/Stereo 호환)
    a_filter = "[1:a]adelay=500:all=1[aout]"
    
    cmd.extend(["-filter_complex", f"{v_filter};{a_filter}", "-map", "[vout]", "-map", "[aout]"])

    bitrate = "6000k" if is_vertical else "4000k"
    cmd.extend([
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "24", "-b:v", bitrate
    ])
    
    # [Sync Fix] 오디오 길이에 +1초(앞뒤 패딩) 맞춰 강제 종료
    duration = get_audio_duration_ffprobe(master_audio)
    if duration:
        final_duration = duration + 1.0
        print(f"⚖️ 최종 동기화 설정: {final_duration:.2f}초로 영상 길이 고정 (패딩 1초 포함)")
        cmd.extend(["-t", str(final_duration)])
    
    cmd.append(output_name) # 로컬 파일명만 사용
    
    print(f"🎬 마스터 렌더링 시작 (상대경로 모드 / {bitrate})")
    try:
        subprocess.run(cmd, check=True)
        print(f"✨ 완성! 결과물: {os.path.join(target_dir, output_name)}")
        if os.path.exists("mylist.txt"): os.remove("mylist.txt")
    except Exception as e:
        print(f"❌ 렌더링 실패: {e}")
    finally:
        os.chdir(current_cwd)

if __name__ == "__main__":
    run_integrated_render()

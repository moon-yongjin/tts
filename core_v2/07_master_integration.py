import os
import subprocess
import re
import sys
import time
import json
import unicodedata

# [설정] FFmpeg 및 작업 경로
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if os.path.basename(SCRIPT_DIR) == "core_v2":
    ROOT_DIR = os.path.dirname(SCRIPT_DIR)
    CORE_DIR = SCRIPT_DIR
else:
    ROOT_DIR = SCRIPT_DIR
    CORE_DIR = os.path.join(ROOT_DIR, "core_v2")

BASE_DIR = CORE_DIR

# [기존 FFmpeg 탐지 로직 보강] - 자막 필터 지원 여부 확인
def get_best_ffmpeg():
    # 1. imageio_ffmpeg 시도 (가장 호환성 좋음)
    try:
        import imageio_ffmpeg
        exe = imageio_ffmpeg.get_ffmpeg_exe()
        if os.path.exists(exe): return exe
    except ImportError: pass

    # 2. Conda/Venv 내부 시도
    conda_ffmpeg = os.path.join(os.path.dirname(sys.executable), "ffmpeg")
    if os.path.exists(conda_ffmpeg): return conda_ffmpeg

    # 3. 시스템 기본
    return "/opt/homebrew/bin/ffmpeg" if sys.platform == "darwin" else "ffmpeg"

FFMPEG_EXE = get_best_ffmpeg()

DOWNLOADS_DIR = os.path.join(os.path.expanduser("~"), "Downloads")

def normalize_name(n):
    return unicodedata.normalize('NFC', n)

def get_latest_folder():
    search_prefixes = ("무협_생성_", "무협_로컬생성_", "무협_세로_", "다이어리_세로_", "틱톡_", "시나리오_", "막장_")
    
    subdirs = []
    for d in os.listdir(DOWNLOADS_DIR):
        full_path = os.path.join(DOWNLOADS_DIR, d)
        if not os.path.isdir(full_path):
            continue
            
        norm_d = normalize_name(d)
        if any(norm_d.startswith(p) for p in search_prefixes):
            subdirs.append(full_path)
            
    if not subdirs: return None
    # 최신 수정된 폴더 반환
    return max(subdirs, key=os.path.getmtime)

def get_srt_file(target_dir):
    """ 자막 파일을 폴더 내부에서 먼저 찾고, 없으면 외부에서 찾음 """
    # 1. 폴더 내부 검색 (audio.srt, final.srt 등 혹은 유일한 srt)
    for name in ["audio.srt", "final.srt", "subtitles.srt"]:
        path = os.path.join(target_dir, name)
        if os.path.exists(path): return path

    # 폴더 내 유일한 srt
    internal_srts = [os.path.join(target_dir, f) for f in os.listdir(target_dir) if f.lower().endswith(".srt")]
    if len(internal_srts) == 1: return internal_srts[0]

    # 4. 다운로드 루트 폴더 Fallback (기존 방식)
    # [변경] 'Azure+Sohee' 추가 및 필터 완화
    root_srts = [os.path.join(DOWNLOADS_DIR, f) for f in os.listdir(DOWNLOADS_DIR) 
                 if f.lower().endswith(".srt") and ("_Full_Merged" in f or "audio" in f.lower() or "azure+sohee" in f.lower())]
    if root_srts:
        return max(root_srts, key=os.path.getmtime)

    # 5. [신규] 정말 아무것도 못 찾았을 때, 가장 최근에 생성된 모든 .srt 중 하나라도 가져오기 (마지막 보루)
    all_srts = [os.path.join(DOWNLOADS_DIR, f) for f in os.listdir(DOWNLOADS_DIR) if f.lower().endswith(".srt")]
    if all_srts:
        latest_srt = max(all_srts, key=os.path.getmtime)
        print(f"   ℹ️ 이름 매칭되는 자막이 없어 가장 최신 자막을 선택합니다: {os.path.basename(latest_srt)}")
        return latest_srt

    return None

def get_master_audio(target_dir):
    """ 최종 마스터 오디오를 폴더 내부에서 먼저 찾고, 없으면 외부에서 찾음 """
    # 1. 폴더 내부 검색 (audio.mp3, final.mp3 등 혹은 유일한 mp3)
    for name in ["audio.mp3", "final.mp3", "mixed_audio.mp3", "master.mp3"]:
        path = os.path.join(target_dir, name)
        if os.path.exists(path): return path

    # 폴더 내 유일한 mp3 (합본 제외)
    internal_mp3s = [os.path.join(target_dir, f) for f in os.listdir(target_dir) 
                     if f.lower().endswith(".mp3") and "합본" not in f]
    if len(internal_mp3s) == 1: return internal_mp3s[0]

    # 2. 외부(Downloads 루트) 검색 (기존 방식)
    # 0. AI Time-Based Director 통합 파일 (V3-7 신규)
    candidates = [os.path.join(DOWNLOADS_DIR, f) for f in os.listdir(DOWNLOADS_DIR) 
                  if ("_V3-9_" in f or "_V3-8_" in f or "_V3-7_" in f or "audio" in f.lower()) and f.lower().endswith(".mp3")]
    if candidates:
        return max(candidates, key=os.path.getmtime)

    # 1. 효과음합본 (V3-3 구버전)
    candidates = [os.path.join(DOWNLOADS_DIR, f) for f in os.listdir(DOWNLOADS_DIR) 
                  if "_효과음합본" in f and f.lower().endswith(".mp3")]
    if candidates:
        return max(candidates, key=os.path.getmtime)
        
    # 2. 일반 합본 (Fallback)
    candidates = [os.path.join(DOWNLOADS_DIR, f) for f in os.listdir(DOWNLOADS_DIR) 
                  if ("_Full_Merged" in f or "final" in f.lower()) and f.lower().endswith(".mp3")]
    if candidates:
        return max(candidates, key=os.path.getmtime)
    
    return None

def srt_time_to_ass(srt_time_str):
    h, m, s_ms = srt_time_str.split(':')
    s, ms = s_ms.split(',')
    return f"{int(h)}:{m}:{s}.{ms[:2]}"

def ass_to_ms(ass_time):
    # H:MM:SS.cs -> ms
    h, m, s_cs = ass_time.split(':')
    s, cs = s_cs.split('.')
    return (int(h) * 3600 + int(m) * 60 + int(s)) * 1000 + int(cs) * 10

def ms_to_ass(ms):
    # ms -> H:MM:SS.cs
    h = int(ms // 3600000)
    m = int((ms % 3600000) // 60000)
    s = int((ms % 60000) // 1000)
    cs = int((ms % 1000) // 10)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"

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
                    'start': srt_time_to_ass(start_srt),
                    'end': srt_time_to_ass(end_srt),
                    'text': text
                })
        print(f"✅ SRT 파싱 완료: {len(events)}개의 자막 블록 로드됨")
    except Exception as e:
        print(f"⚠️ SRT 파싱 중 오류: {e}")
    return events

def smart_wrap(text, max_len=14):
    """ 자막을 자르지 않고 여러 줄(\\N)로 나눕니다. (2줄씩 뭉친 리스트 반환) """
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
    
    # 2줄씩 묶어서 리턴
    chunks = []
    for i in range(0, len(lines), 2):
        chunks.append("\\N".join(lines[i:i+2]))
    return chunks

def run_integrated_render():
    print("\n" + "="*50)
    print("🏆 [STEP 07] 마스터 통합 렌더링 (지능형 가로/세로 감지)")
    print("="*50)
    
    # 1. 파일 찾기
    target_dir = get_latest_folder()

    if not target_dir or not os.path.exists(target_dir): 
        print("❌ 작업 폴더를 찾을 수 없습니다."); return
    
    dir_name = os.path.basename(target_dir)
    # [NFC/NFD 통합 대응] 폴더명 정규화 후 체크
    norm_dir_name = normalize_name(dir_name)
    is_vertical = any(p in norm_dir_name for p in ["세로_", "틱톡_", "시나리오_", "막장_"])
    
    srt_file = get_srt_file(target_dir)
    master_audio = get_master_audio(target_dir)
    
    print(f"📂 대상 비디오: {norm_dir_name} ({'세로' if is_vertical else '가로'} 모드)")
    
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

    # 자막 스타일 설정 (노란색으로 시인성 확보)
    ass_header = f"[Script Info]\nScriptType: v4.00+\nPlayResX: {res_x}\nPlayResY: {res_y}\n\n[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\nStyle: Default,Arial,{font_size},&H0000FFFF,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,{outline},{shadow},{alignment},{margin_l},{margin_r},{margin_v},1\n\n[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
    
    with open(ass_path, "w", encoding="utf-8") as f:
        f.write(ass_header)
        for ev in srt_events:
            chunks = smart_wrap(ev['text'], max_len=max_len)
            if not chunks: continue
            
            # 시간 분할 (텍스트 길이에 비례해서 쪼개기)
            total_chars = sum(len(c.replace('\\N', ' ')) for c in chunks)
            start_ms = ass_to_ms(ev['start'])
            end_ms = ass_to_ms(ev['end'])
            duration = end_ms - start_ms
            
            accum_ms = start_ms
            for chunk in chunks:
                chunk_text_len = len(chunk.replace('\\N', ' '))
                if total_chars > 0:
                    chunk_duration = (chunk_text_len / total_chars) * duration
                else:
                    chunk_duration = duration / len(chunks)
                    
                chunk_end = accum_ms + chunk_duration
                f.write(f"Dialogue: 0,{ms_to_ass(accum_ms)},{ms_to_ass(chunk_end)},Default,,0,0,0,,{chunk}\n")
                accum_ms = chunk_end

    # 4. 결과 파일명 설정
    output_name = f"무협_최종_합본_마스터_{int(time.time())%1000:03d}.mp4"
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
    
    # fontsdir 제거 (시스템 폰트 사용 시 불필요하며 충돌 원인)
    v_filter = f"[0:v]subtitles=filename='final.ass'[vout]"
    cmd.extend(["-filter_complex", v_filter, "-map", "[vout]", "-map", "1:a"])

    bitrate = "5000k" if is_vertical else "4000k"
    cmd.extend([
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "24", "-b:v", bitrate,
        output_name # 로컬 파일명만 사용
    ])
    
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

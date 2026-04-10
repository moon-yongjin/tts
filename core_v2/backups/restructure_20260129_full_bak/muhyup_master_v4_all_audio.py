import os
import subprocess
import re
import sys

# [설정] FFmpeg 및 작업 경로
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FFMPEG_DIR = os.path.join(BASE_DIR, "ffmpeg", "ffmpeg-2026-01-07-git-af6a1dd0b2-essentials_build", "bin")
FFMPEG_EXE = "ffmpeg"
DOWNLOADS_DIR = os.path.join(os.path.expanduser("~"), "Downloads")
SFX_DIR = os.path.join(BASE_DIR, "sfx")

def get_latest_folder():
    folders = [os.path.join(DOWNLOADS_DIR, d) for d in os.listdir(DOWNLOADS_DIR) 
               if os.path.isdir(os.path.join(DOWNLOADS_DIR, d)) and d.startswith("무협_생성_")]
    if not folders: return None
    return max(folders, key=os.path.getmtime)

def get_latest_srt():
    srt_files = [os.path.join(DOWNLOADS_DIR, f) for f in os.listdir(DOWNLOADS_DIR) 
                 if f.lower().endswith(".srt")]
    if not srt_files: return None
    return max(srt_files, key=os.path.getmtime)

def get_latest_mp3():
    mp3_files = [os.path.join(DOWNLOADS_DIR, f) for f in os.listdir(DOWNLOADS_DIR) 
                 if f.lower().endswith(".mp3") and "sfxtemp" not in f.lower()]
    if not mp3_files: return None
    # 마스터 합본 등을 피하기 위해 크기나 이름으로 필터링 가능
    return max(mp3_files, key=os.path.getmtime)

def srt_time_to_ass(srt_time_str):
    h, m, s_ms = srt_time_str.split(':')
    s, ms = s_ms.split(',')
    return f"{int(h)}:{m}:{s}.{ms[:2]}"

def srt_time_to_seconds(srt_time_str):
    h, m, s_ms = srt_time_str.split(':')
    s, ms = s_ms.split(',')
    return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000

def parse_srt_with_sfx(srt_path):
    if not srt_path or not os.path.exists(srt_path): return [], []
    events = []
    sfx_events = []
    with open(srt_path, 'r', encoding='utf-8-sig') as f:
        content = f.read()
    blocks = re.split(r'\n\s*\n', content.strip())
    
    # SFX 파일 목록 미리 로드 (매칭용)
    available_sfx = {}
    if os.path.exists(SFX_DIR):
        for f in os.listdir(SFX_DIR):
            name_no_ext = os.path.splitext(f)[0].lower()
            available_sfx[name_no_ext] = f

    for block in blocks:
        lines = block.splitlines()
        if len(lines) >= 3:
            times = re.findall(r'(\d{2}:\d{2}:\d{2},\d{3})', lines[1])
            if len(times) >= 2:
                start_ass = srt_time_to_ass(times[0])
                end_ass = srt_time_to_ass(times[1])
                start_sec = srt_time_to_seconds(times[0])
                raw_text = " ".join(lines[2:])
                
                # SFX 태그 추출 [SFX: 이름]
                tags = re.findall(r'\[SFX:\s*([^\]]+)\]', raw_text)
                for tag in tags:
                    tag_clean = tag.strip().lower()
                    # 비슷하거나 일치하는 파일 찾기
                    found_file = None
                    for sfx_key, sfx_file in available_sfx.items():
                        if tag_clean in sfx_key or sfx_key in tag_clean:
                            found_file = sfx_file
                            break
                    if found_file:
                        sfx_events.append({'time': start_sec, 'file': found_file})
                
                # 자막용 텍스트 (SFX 태그 제거)
                clean_text = re.sub(r'\[SFX:[^\]]+\]', '', raw_text).strip()
                events.append({'start': start_ass, 'end': end_ass, 'text': clean_text})
    return events, sfx_events

def smart_wrap(text, max_len=14):
    text = text.replace('\\N', ' ').replace('\n', ' ').replace('.', '').strip()
    if len(text) > max_len: text = text[:max_len].strip()
    return text

def run_v4_render():
    print("🚀 [Mu-hyup V4] 영상 + 자막 + 음성 + SFX + Ambience 통합 렌더링...")
    
    target_dir = get_latest_folder()
    if not target_dir:
        print("❌ 작업 폴더를 찾을 수 없습니다.")
        return
    
    srt_file = get_latest_srt()
    voice_file = get_latest_mp3()
    
    # 앰비언스 설정 (기본값: night_ambi.mp3 또는 wind_storm.mp3)
    ambi_file = os.path.join(SFX_DIR, "night_ambi.mp3")
    if not os.path.exists(ambi_file):
        ambi_file = os.path.join(SFX_DIR, "wind_storm.mp3")
    
    print(f"📂 폴더: {target_dir}")
    print(f"📄 자막: {os.path.basename(srt_file) if srt_file else '없음'}")
    print(f"🎵 음성: {os.path.basename(voice_file) if voice_file else '없음'}")
    print(f"🌿 환경음: {os.path.basename(ambi_file) if os.path.exists(ambi_file) else '없음'}")

    video_files = [f for f in os.listdir(target_dir) if f.lower().endswith(".mp4") and "합본" not in f]
    video_files.sort(key=lambda x: [int(c) if c.isdigit() else c for c in re.split(r'(\d+)', x)])
    
    if not video_files: return

    # 1. 자막 및 SFX 분석
    srt_events, sfx_events = parse_srt_with_sfx(srt_file)
    print(f"🔊 감지된 SFX 포인트: {len(sfx_events)}개")

    # 2. 파일들 준비
    mylist_path = os.path.join(target_dir, "mylist.txt")
    with open(mylist_path, "w", encoding="utf-8") as f:
        for video in video_files: f.write(f"file '{video.replace(\"'\", \"'\\\\''\")}'\n")

    ass_path = os.path.join(target_dir, "final.ass")
    ass_header = f"""[Script Info]\nScriptType: v4.00+\nPlayResX: 1080\nPlayResY: 1920\nScaledBorderAndShadow: yes\n\n[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\nStyle: Default,Cafe24 Ohsquare,180,&H00FFFFFF,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,3,5,2,10,10,100,1\n\n[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"""
    with open(ass_path, "w", encoding="utf-8") as f:
        f.write(ass_header)
        for ev in srt_events:
            content = smart_wrap(ev['text'], 14)
            if content: f.write(f"Dialogue: 0,{ev['start']},{ev['end']},Default,,0,0,0,,{{\\fax-0.1}}{content}\n")

    # 3. 카운팅
    counter_file = os.path.join(BASE_DIR, "global_counter.txt")
    if os.path.exists(counter_file):
        with open(counter_file, "r") as f:
            try: count = int(f.read().strip()) + 1
            except: count = 1
    else: count = 1
    with open(counter_file, "w") as f: f.write(str(count))

    output_file = os.path.join(target_dir, f"무협_최종_합본_V4_Full_{count:03d}.mp4")
    ass_path_fixed = os.path.abspath(ass_path).replace('\\', '/').replace(':', '\\:')
    fonts_dir = BASE_DIR.replace('\\', '/').replace(':', '\\:')

    # 4. FFmpeg 복합 필터 구성 (핵심)
    # 입력 순서: 0:비디오(concat), 1:성우음성, 2:앰비언스, 3~:SFX들
    cmd = [FFMPEG_EXE, "-f", "concat", "-safe", "0", "-i", mylist_path] # [0] 비디오
    if voice_file: cmd.extend(["-i", voice_file]) # [1] 음성
    if os.path.exists(ambi_file): cmd.extend(["-stream_loop", "-1", "-i", ambi_file]) # [2] 앰비언스
    
    # SFX 파일들 입력 추가
    for sfx in sfx_events:
        cmd.extend(["-i", os.path.join(SFX_DIR, sfx['file'])])
    
    # 복합 오디오 필터 (amix/adelay)
    # [1:a] - 성우
    # [2:a] - 앰비언스 (볼륨 조절 필수)
    # [i+3:a] - 각 SFX (타이밍 조절 필수)
    filter_complex = []
    
    # 앰비언스 볼륨 낮추기 (배경음처럼)
    if os.path.exists(ambi_file):
        filter_complex.append(f"[2:a]volume=0.3[amb];")
    
    # 각 SFX 지연(delay) 설정
    sfx_labels = []
    for i, sfx in enumerate(sfx_events):
        delay_ms = int(sfx['time'] * 1000)
        label = f"sfx{i}"
        filter_complex.append(f"[{i+3}:a]adelay={delay_ms}|{delay_ms}[{label}];")
        sfx_labels.append(f"[{label}]")
    
    # 모든 오디오 합치기
    audio_inputs = []
    if voice_file: audio_inputs.append("[1:a]")
    if os.path.exists(ambi_file): audio_inputs.append("[amb]")
    audio_inputs.extend(sfx_labels)
    
    if audio_inputs:
        filter_complex.append(f"{''.join(audio_inputs)}amix=inputs={len(audio_inputs)}:duration=first:dropout_transition=2[mixed_audio]")

    cmd.extend([
        "-filter_complex", "".join(filter_complex),
        "-vf", f"subtitles='{ass_path_fixed}':fontsdir='{fonts_dir}'"
    ])
    
    if audio_inputs:
        cmd.extend(["-map", "0:v", "-map", "[mixed_audio]"])
    else:
        cmd.extend(["-map", "0:v", "-c:a", "aac"])

    cmd.extend([
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "23",
        "-shortest", "-y", output_file
    ])
    
    print(f"🎬 통합 믹싱 및 렌더링 진행 중...")
    try:
        subprocess.run(cmd, check=True, cwd=target_dir)
        print(f"✨ 완성! 결과물: {output_file}")
        os.remove(mylist_path)
    except subprocess.CalledProcessError as e:
        print(f"❌ 렌더링 실패 (SFX 개수가 너무 많으면 명령 줄 길이가 초과될 수 있습니다): {e}")

if __name__ == "__main__":
    run_v4_render()

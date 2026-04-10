import os
import subprocess
import re
import sys

# [설정] FFmpeg 및 작업 경로
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if os.path.basename(SCRIPT_DIR) == "core_v2":
    ROOT_DIR = os.path.dirname(SCRIPT_DIR)
    CORE_DIR = SCRIPT_DIR
else:
    ROOT_DIR = SCRIPT_DIR
    CORE_DIR = os.path.join(ROOT_DIR, "core_v2")

BASE_DIR = CORE_DIR
# 전용 환경에 설치된 자막 지원 FFmpeg 사용
FFMPEG_EXE = "/Users/a12/miniforge3/envs/qwen-tts/bin/ffmpeg"
if not os.path.exists(FFMPEG_EXE):
    FFMPEG_EXE = "ffmpeg"

DOWNLOADS_DIR = os.path.join(os.path.expanduser("~"), "Downloads")

def get_latest_folder():
    folders = [os.path.join(DOWNLOADS_DIR, d) for d in sorted(os.listdir(DOWNLOADS_DIR)) 
               if os.path.isdir(os.path.join(DOWNLOADS_DIR, d)) and (d.startswith("무협_생성_") or d.startswith("무협_로컬생성_"))]
    if not folders: return None
    return max(folders, key=os.path.getmtime)

def get_latest_srt():
    srt_files = [os.path.join(DOWNLOADS_DIR, f) for f in os.listdir(DOWNLOADS_DIR) 
                 if f.lower().endswith(".srt") and "_Full_Merged" in f]
    if not srt_files: return None
    return max(srt_files, key=os.path.getmtime)

def get_audio_layers():
    """ narration, bgm_mix, sfx_layer 3종 세트 찾기 """
    # 1. 순수 목소리 (Narration)
    voice = None
    voice_candidates = [os.path.join(DOWNLOADS_DIR, f) for f in os.listdir(DOWNLOADS_DIR) 
                        if "_Full_Merged.mp3" in f]
    if voice_candidates:
        voice = max(voice_candidates, key=os.path.getmtime)

    # 2. 4번 공정 결과물 (Voice + BGM Mix)
    bgm_mix = None
    bgm_candidates = [os.path.join(DOWNLOADS_DIR, f) for f in os.listdir(DOWNLOADS_DIR) 
                      if re.search(r"_Full_Merged(-\d+|-(final|reverted)).*\.mp3$", f)]
    if bgm_candidates:
        bgm_mix = max(bgm_candidates, key=os.path.getmtime)

    # 3. 5번 공정 결과물 (Pure SFX Layer)
    sfx_layer = None
    sfx_candidates = [os.path.join(DOWNLOADS_DIR, f) for f in os.listdir(DOWNLOADS_DIR) 
                      if "_배경_효과음_레이어" in f]
    if sfx_candidates:
        sfx_layer = max(sfx_candidates, key=os.path.getmtime)

    return voice, bgm_mix, sfx_layer

def srt_time_to_ass(srt_time_str):
    h, m, s_ms = srt_time_str.split(':')
    s, ms = s_ms.split(',')
    return f"{int(h)}:{m}:{s}.{ms[:2]}"

def parse_srt(srt_path):
    if not srt_path or not os.path.exists(srt_path): return []
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
    if len(text) > max_len: text = text[:max_len].strip()
    return text

def run_integrated_render():
    print("\n" + "="*50)
    print("🏆 [STEP 07] 마스터 통합 렌더링 (다중 오디오 레이어)")
    print("="*50)
    
    # 1. 파일 찾기
    target_dir = get_latest_folder()
    if not target_dir: 
        print("❌ 작업 폴더를 찾을 수 없습니다."); return
    
    srt_file = get_latest_srt()
    v_voice, v_bgm, v_sfx = get_audio_layers()
    
    print(f"📂 대상 비디오: {os.path.basename(target_dir)}")
    
    # 오디오 결정 우선순위
    # 1. BGM_MIX(Voice+BGM) 가 있으면 그것을 기본으로 SFX를 얹음
    # 2. BGM_MIX가 없으면 VOICE(Narration)을 기본으로 SFX를 얹음
    
    main_audio = v_bgm if v_bgm else v_voice
    extra_audio = v_sfx if v_sfx else None
    
    if main_audio: print(f"🎙️ 메인 오디오: {os.path.basename(main_audio)}")
    if extra_audio: print(f"🎹 추가 레이어: {os.path.basename(extra_audio)}")

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
    ass_header = "[Script Info]\nScriptType: v4.00+\nPlayResX: 1080\nPlayResY: 1920\n\n[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\nStyle: Default,Cafe24 Ohsquare,180,&H00FFFFFF,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,3,5,2,10,10,100,1\n\n[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
    with open(ass_path, "w", encoding="utf-8") as f:
        f.write(ass_header)
        for ev in srt_events:
            content = smart_wrap(ev['text'])
            if content: f.write(f"Dialogue: 0,{ev['start']},{ev['end']},Default,,0,0,0,,{{\\\\fax-0.1}}{content}\n")

    # 4. 결과 파일명 설정
    output_file = os.path.join(target_dir, f"무협_최종_합본_마스터_{int(time.time())%1000:03d}.mp4")
    ass_path_fixed = os.path.abspath(ass_path).replace('\\', '/').replace(':', '\\:')
    fonts_dir = BASE_DIR.replace('\\', '/').replace(':', '\\:')

    # 5. FFmpeg 실행 (다중 오디오 믹싱)
    cmd = [FFMPEG_EXE, "-y", "-f", "concat", "-safe", "0", "-i", mylist_path]
    
    inputs_count = 1
    if main_audio: 
        cmd.extend(["-i", main_audio])
        main_idx = inputs_count; inputs_count += 1
    if extra_audio: 
        cmd.extend(["-i", extra_audio])
        extra_idx = inputs_count; inputs_count += 1
    
    # 필터 설정 - 라벨을 명시해야 에러가 안 납니다.
    v_filter = f"[0:v]subtitles=filename='{ass_path_fixed}':fontsdir='{fonts_dir}'[vout]"
    
    if main_audio and extra_audio:
        # 두 오디오 레이어 믹스 (세미콜론으로 구분)
        filter_complex = f"{v_filter};[1:a][2:a]amix=inputs=2:duration=first:dropout_transition=2[aout]"
        cmd.extend(["-filter_complex", filter_complex, "-map", "[vout]", "-map", "[aout]"])
    elif main_audio:
        # 비디오 라벨 처리 + 단일 오디오 매핑
        cmd.extend(["-filter_complex", v_filter, "-map", "[vout]", "-map", "1:a"])
    else:
        # 비디오 라벨 처리 + 오디오 무음처리
        cmd.extend(["-filter_complex", v_filter, "-map", "[vout]", "-c:a", "aac", "-b:a", "192k"])

    cmd.extend([
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "24", "-b:v", "5000k",
        "-shortest", output_file
    ])
    
    print(f"🎬 마스터 렌더링 중... (비디오 + 다중 오디오 레이어)")
    try:
        subprocess.run(cmd, check=True)
        print(f"✨ 완성! 결과물: {output_file}")
        if os.path.exists(mylist_path): os.remove(mylist_path)
    except Exception as e:
        print(f"❌ 렌더링 실패: {e}")

if __name__ == "__main__":
    import time
    run_integrated_render()

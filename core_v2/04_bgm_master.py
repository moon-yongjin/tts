import os
import json
import re
import sys
import time
import subprocess
from pydub import AudioSegment, effects

# [설정]
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# 시스템 PATH의 ffmpeg 사용 (Windows 호환)
AudioSegment.converter = "ffmpeg"
AudioSegment.ffprobe = "ffprobe"

# [경로 설정]
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if os.path.basename(SCRIPT_DIR) == "core_v2":
    ROOT_DIR = os.path.dirname(SCRIPT_DIR)
    CORE_DIR = SCRIPT_DIR
else:
    ROOT_DIR = SCRIPT_DIR
    CORE_DIR = os.path.join(ROOT_DIR, "core_v2")

LIB_DIR = os.path.join(CORE_DIR, "Library")
BGM_DIR = os.path.join(LIB_DIR, "bgm")
SFX_DIR = os.path.join(LIB_DIR, "sfx")
DOWNLOADS_DIR = os.path.join(os.path.expanduser("~"), "Downloads")

# [AI SFX Logic removed from here - moved to Step 5]

def time_to_ms(time_str):
    try:
        parts = time_str.split(':')
        if len(parts) == 2: return (int(parts[0]) * 60 + int(parts[1])) * 1000
        if len(parts) == 3: return (int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])) * 1000
    except: return 0
    return 0

def srt_time_to_ms(srt_time_str):
    try:
        h, m, s_ms = srt_time_str.split(':')
        s, ms = s_ms.split(',')
        return (int(h) * 3600 + int(m) * 60 + int(s)) * 1000 + int(ms)
    except: return 0

def parse_srt(srt_path):
    if not os.path.exists(srt_path): return []
    try:
        with open(srt_path, "r", encoding="utf-8-sig") as f:
            content = f.read().strip()
        entries = []
        blocks = re.split(r'\n\n', content)
        for block in blocks:
            lines = block.splitlines()
            if len(lines) >= 3:
                times = re.findall(r'(\d{2}:\d{2}:\d{2},\d{3})', lines[1])
                if len(times) >= 2:
                    start = srt_time_to_ms(times[0])
                    end = srt_time_to_ms(times[1])
                    text = " ".join(lines[2:])
                    entries.append({'start': start, 'end': end, 'text': text})
        return entries
    except: return []

# SFX find logic removed (Step 4 now focused on BGM)

def apply_ai_sfx_and_bgm(plan_file="bgm_plan.json"):
    start_time_all = time.time()
    print("🚀 [BGM Master] 지능형 AI 모드 활성화 (Auto SFX Matching)...")
    
    # 1. 대상 찾기 (확장된 검색 로직)
    # _Full_Merged 또는 대본_...Full... 포함
    # 제외 키워드: -final-, -master, -reverted, _배경_효과음_레이어, _효과음합본
    excludes = ["-final-", "-master", "-reverted", "_배경_효과음_레이어", "_효과음합본"]
    
    mp3s = []
    for f in os.listdir(DOWNLOADS_DIR):
        if not f.lower().endswith(".mp3"): continue
        if any(x in f for x in excludes): continue
        
        # 조건: "Full"과 "Merged"가 들어가거나, "대본_"으로 시작하고 "Full"이 들어간 경우
        if ("Full" in f and "Merged" in f) or (f.startswith("대본_") and "Full" in f):
            mp3s.append(os.path.join(DOWNLOADS_DIR, f))

    if not mp3s:
        print("❌ 처리할 MP3 파일이 없습니다.")
        return

    mp3s.sort(key=os.path.getmtime, reverse=True)
    mp3_path = mp3s[0]
    srt_path = mp3_path.replace(".mp3", ".srt")
    srt_entries = parse_srt(srt_path)
    
    print(f"📂 대상: {os.path.basename(mp3_path)}")

    # 2. 대본 분석 (자동 태깅 제외)
    script_file = os.path.join(ROOT_DIR, "대본.txt")
    full_script_text = ""
    if os.path.exists(script_file):
        with open(script_file, "r", encoding="utf-8") as f:
            full_script_text = f.read()

    # [3. 믹싱 진행]
    final_audio = AudioSegment.from_mp3(mp3_path)
    audio_duration_ms = len(final_audio)

    # SFX mixing logic removed to prevent overlap with Step 5.

    # BGM 믹싱 (bgm_plan.json 기준)
    plan_path = os.path.join(ROOT_DIR, plan_file)
    if not os.path.exists(plan_path):
        plan_path = os.path.join(CORE_DIR, plan_file)
        
    if os.path.exists(plan_path):
        with open(plan_path, "r", encoding="utf-8") as f:
            config = json.load(f)
            if config:
                actions = config[0].get("actions", [])
                for action in actions:
                    bgm_file = action.get("bgm_file")
                    bgm_path = os.path.join(BGM_DIR, bgm_file)
                    if os.path.exists(bgm_path):
                        print(f"🎵 BGM 오버레이: {bgm_file}")
                        bgm = AudioSegment.from_mp3(bgm_path) + action.get("volume", -25)
                        final_audio = final_audio.overlay(bgm, position=time_to_ms(action.get("start_time", "00:00")), loop=action.get("loop", True))

    # 저장 [사용자 요청: 타임스탬프 적용]
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    print(f"📊 최종 오디오 볼륨: {final_audio.dBFS:.2f} dBFS")
    if final_audio.dBFS == -float('inf'):
        print("⚠️ 경고: 최종 결과물이 무음(Silence)입니다! 입력 파일이나 코덱을 확인하세요.")

    final_audio = final_audio.normalize(headroom=0.1)
    base_name = os.path.basename(mp3_path).replace(".mp3", "")
    output_path = os.path.join(DOWNLOADS_DIR, f"{base_name}-reverted-{timestamp}.mp3")
    
    final_audio.export(output_path, format="mp3", bitrate="192k")
    print(f"🏁 완료: {output_path}")

if __name__ == "__main__":
    apply_ai_sfx_and_bgm()

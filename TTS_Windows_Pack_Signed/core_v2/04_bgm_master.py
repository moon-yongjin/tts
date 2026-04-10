import os
import json
import re
import sys
import time
import subprocess
from pydub import AudioSegment, effects

# [설정]
# 전용 환경의 FFmpeg 사용
AudioSegment.converter = "/Users/a12/miniforge3/envs/qwen-tts/bin/ffmpeg"
AudioSegment.ffprobe = "/Users/a12/miniforge3/envs/qwen-tts/bin/ffprobe"
if not os.path.exists(AudioSegment.converter):
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

# [Import AI SFX Logic]
sys.path.append(os.path.join(CORE_DIR, "engine"))
import sfx_generator

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

def find_time_for_sfx(srt_entries, target_text):
    if not target_text or not isinstance(target_text, str): return None
    target_clean = re.sub(r'[^a-zA-Z가-힣0-9]', '', target_text)
    for entry in srt_entries:
        entry_clean = re.sub(r'[^a-zA-Z가-힣0-9]', '', entry['text'])
        if target_clean in entry_clean:
            return entry['start']
    return None

def apply_ai_sfx_and_bgm(plan_file="bgm_plan.json"):
    start_time_all = time.time()
    print("🚀 [BGM Master] 안정화 모드 복구 (AI 자동 생성 최소화)...")
    
    # 1. 대상 찾기
    mp3s = [os.path.join(DOWNLOADS_DIR, f) for f in os.listdir(DOWNLOADS_DIR) 
            if f.endswith(".mp3") and "_Full_Merged" in f and not any(x in f for x in ["-final-", "-master", "-1"])]
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

    # sfx_review.txt에서 태그 읽기 (자동 생성 X)
    review_file = os.path.join(ROOT_DIR, "sfx_review.txt")
    tagged_script = ""
    if os.path.exists(review_file):
        with open(review_file, "r", encoding="utf-8") as f:
            tagged_script = f.read()
    else:
        tagged_script = full_script_text

    # 3. 믹싱 진행
    final_audio = AudioSegment.from_mp3(mp3_path)
    audio_duration_ms = len(final_audio)

    # SFX 믹싱
    print("🔊 효과음 믹싱 중...")
    sfx_count = 0
    if tagged_script:
        for match in re.finditer(r'\[SFX:([^\]]+)\]', tagged_script):
            sfx_name = match.group(1).strip()
            sfx_file = os.path.join(SFX_DIR, f"{sfx_name}.mp3")
            if os.path.exists(sfx_file):
                ratio = match.start() / len(tagged_script)
                found_time = int(ratio * audio_duration_ms)
                sfx_audio = AudioSegment.from_mp3(sfx_file) - 10
                final_audio = final_audio.overlay(sfx_audio, position=found_time)
                sfx_count += 1
    print(f"✅ {sfx_count}개 효과음 믹스 완료")

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

    # 저장
    final_audio = final_audio.normalize(headroom=0.1)
    output_path = os.path.join(DOWNLOADS_DIR, os.path.basename(mp3_path).replace(".mp3", "-reverted.mp3"))
    final_audio.export(output_path, format="mp3", bitrate="192k")
    print(f"🏁 완료: {output_path}")

if __name__ == "__main__":
    apply_ai_sfx_and_bgm()

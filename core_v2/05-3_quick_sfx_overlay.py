import os
import re
import json
import time
from pydub import AudioSegment
import google.generativeai as genai
from pathlib import Path

# [설정]
PROJ_ROOT = Path("/Users/a12/projects/tts")
CORE_V2 = PROJ_ROOT / "core_v2"
DOWNLOADS_DIR = Path.home() / "Downloads"
SFX_DIR = CORE_V2 / "Library" / "sfx"
CONFIG_PATH = PROJ_ROOT / "config.json"

def load_gemini_key():
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                config = json.load(f)
                return config.get("Gemini_API_KEY")
        except: pass
    return None

def get_latest_files():
    # 검색할 디렉토리 목록
    search_dirs = [
        PROJ_ROOT / "remotion-hello-world" / "public",
        DOWNLOADS_DIR,
        CORE_V2
    ]
    
    all_wavs = []
    for d in search_dirs:
        if d.exists():
            # '_SFX_Applied'가 포함된 파일은 제외
            all_wavs.extend([f for f in d.glob("*.wav") if "_SFX_Applied" not in f.name])
    
    if not all_wavs: return None, None
    
    # 가장 최근 수정된 wav 파일 선택
    latest_wav = max(all_wavs, key=os.path.getmtime)
    
    # 동일한 이름의 srt를 같은 폴더에서 찾거나, 가장 최근 srt를 찾음
    latest_srt = latest_wav.with_suffix(".srt")
    
    if not latest_srt.exists():
        all_srts = []
        for d in search_dirs:
            if d.exists():
                all_srts.extend(list(d.glob("*.srt")))
        if all_srts:
            latest_srt = max(all_srts, key=os.path.getmtime)
        else:
            return latest_wav, None
            
    return latest_wav, latest_srt

def parse_srt(srt_path):
    if not srt_path or not srt_path.exists(): return []
    events = []
    with open(srt_path, 'r', encoding='utf-8-sig') as f:
        content = f.read()
    blocks = re.split(r'\n\s*\n', content.strip())
    for block in blocks:
        lines = block.splitlines()
        if len(lines) >= 3:
            times = re.findall(r'(\d{2}:\d{2}:\d{2},\d{3})', lines[1])
            if len(times) >= 2:
                h, m, s_ms = times[0].split(':')
                s, ms = s_ms.split(',')
                start_ms = (int(h)*3600 + int(m)*60 + int(s))*1000 + int(ms)
                events.append({'start_ms': start_ms, 'text': " ".join(lines[2:])})
    return events

def pick_sfx_ai(model, text_chunk, sfx_list):
    if not text_chunk.strip() or not sfx_list: return None
    names = ", ".join([os.path.splitext(f)[0] for f in sfx_list])
    prompt = f"지문: \"{text_chunk}\"\n목록: {names}\n가장 어울리는 효과음 하나만 확장자 없이 답변하세요. 없으면 'None'."
    try:
        response = model.generate_content(prompt)
        choice = response.text.strip().lower()
        if "none" in choice: return None
        for f in sfx_list:
            if os.path.splitext(f)[0].lower() in choice: return f
    except: pass
    return None

def run_quick_overlay():
    print("🚀 [Quick SFX Overlay] 기존 음성에 효과음만 입히기 시작...")
    
    wav_path, srt_path = get_latest_files()
    if not wav_path:
        print("❌ 음성 파일을 찾을 수 없습니다."); return
    
    print(f"🎵 대상 음성: {wav_path}")
    print(f"📝 대상 자막: {srt_path if srt_path else '없음'}")
    
    gemini_key = load_gemini_key()
    if not gemini_key:
        print("❌ API Key가 필요합니다."); return
    
    genai.configure(api_key=gemini_key)
    model = genai.GenerativeModel('gemini-2.0-flash')
    
    audio = AudioSegment.from_file(wav_path)
    sfx_files = [f for f in os.listdir(SFX_DIR) if f.lower().endswith(('.mp3', '.wav'))]
    
    events = parse_srt(srt_path)
    if not events:
        print("⚠️ 자막 정보가 없어 효과음을 넣을 수 없습니다. (SRT 파일 확인 필요)")
        return

    last_sfx_time = -10000
    sfx_count = 0
    
    for event in events:
        current_time = event['start_ms']
        if current_time - last_sfx_time >= 10000:
            sfx_file = pick_sfx_ai(model, event['text'], sfx_files)
            if sfx_file:
                try:
                    sfx_path = SFX_DIR / sfx_file
                    sfx_audio = AudioSegment.from_file(sfx_path).normalize() - 15
                    if len(sfx_audio) > 5000: sfx_audio = sfx_audio[:5000].fade_out(1000)
                    audio = audio.overlay(sfx_audio, position=current_time)
                    print(f"   🔔 SFX: {sfx_file} @ {current_time/1000:.1f}s")
                    sfx_count += 1
                    last_sfx_time = current_time
                except: pass

    output_path = wav_path.parent / f"{wav_path.stem}_SFX_Applied.wav"
    audio.export(output_path, format="wav")
    print(f"\n✨ 완성: {output_path} (효과음 {sfx_count}개 삽입)")

if __name__ == "__main__":
    run_quick_overlay()

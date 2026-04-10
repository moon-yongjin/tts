import os
import json
import re
import sys
import time
from pydub import AudioSegment, effects

# [설정]
FFMPEG_PATH = r"C:\Users\moori\Downloads\ffmpeg-2026-01-07-git-af6a1dd0b2-essentials_build\ffmpeg-2026-01-07-git-af6a1dd0b2-essentials_build\bin\ffmpeg"
FFMPEG_DIR = os.path.dirname(FFMPEG_PATH)
AudioSegment.converter = FFMPEG_PATH
AudioSegment.ffprobe = os.path.join(FFMPEG_DIR, "ffprobe")
os.environ["PATH"] += os.pathsep + FFMPEG_DIR

# [경로 설정]
ENGINE_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(ENGINE_DIR)
LIB_DIR = os.path.join(BASE_DIR, "Library")
BGM_DIR = os.path.join(LIB_DIR, "bgm")
SFX_DIR = os.path.join(LIB_DIR, "sfx")
DOWNLOADS_DIR = os.path.join(os.path.expanduser("~"), "Downloads")

# [Import AI SFX Logic]
sys.path.append(ENGINE_DIR)
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
    print("🚀 [BGM Master] AI 음향 감독 모드 가동 (자막 데이터 기반)...")
    
    # 1. Downloads에서 최근 MP3 및 SRT 세트 찾기 (5분 이내)
    mp3s = [os.path.join(DOWNLOADS_DIR, f) for f in os.listdir(DOWNLOADS_DIR) if f.endswith(".mp3") and not f.endswith("-1.mp3")]
    if not mp3s:
        print("❌ Downloads 폴더에 처리할 MP3 파일이 없습니다.")
        return

    mp3s.sort(key=os.path.getmtime, reverse=True)
    latest_time = os.path.getmtime(mp3s[0]) if mp3s else 0
    targets = [f for f in mp3s if (latest_time - os.path.getmtime(f)) < 300]
    
    print(f"📂 총 {len(targets)}개의 파일 세트를 처리합니다.")

    # 2. 모든 자막에서 텍스트 추출 (Gemini 분석용 전체 대본 구성)
    full_script_text = ""
    target_data = [] # (mp3_path, srt_entries) 리스트
    
    for mp3_path in reversed(targets): # 오래된 파트부터 대본 구성
        srt_path = mp3_path.rsplit('.', 1)[0] + ".srt"
        srt_entries = parse_srt(srt_path)
        if srt_entries:
            part_text = " ".join([e['text'] for e in srt_entries])
            full_script_text += part_text + " "
            target_data.append((mp3_path, srt_entries))
        else:
            print(f"⚠️ {os.path.basename(mp3_path)}의 자막(.srt)이 없어 대본 분석에서 제외됩니다.")
            target_data.append((mp3_path, []))

    if not full_script_text.strip():
        print("⚠️ 자막(.srt)에서 텍스트를 추출할 수 없어 '대본.txt'를 확인합니다.")
        script_file = os.path.join(BASE_DIR, "대본.txt")
        if os.path.exists(script_file):
            with open(script_file, "r", encoding="utf-8") as f:
                full_script_text = f.read()
            print("✅ '대본.txt'에서 전체 대본을 읽어왔습니다.")
        else:
            print("❌ 자막 파일도 없고 '대본.txt'도 찾을 수 없습니다.")
            return

    # 3. AI SFX 분석 및 사용자 검토
    print("🤖 [AI Sound Director] 자막 텍스트 분석 및 효과음 구성 중...")
    tagged_script = sfx_generator.process_script_sfx(full_script_text, output_dir=SFX_DIR)
    
    # [사용자 리뷰 단계 추가]
    review_file = os.path.join(BASE_DIR, "sfx_review.txt")
    if tagged_script:
        with open(review_file, "w", encoding="utf-8") as f:
            f.write(tagged_script)
        
        print("\n" + "!"*50)
        print("🔍 [음향 구성 검토] AI가 제안한 효과음 배치를 확인해주세요.")
        print(f"📄 파일 위치: {review_file}")
        print("💡 팁: 파일을 열어 [SFX:...] 내용을 직접 수정하거나 삭제할 수 있습니다.")
        print("💡 수정을 마친 후 저장하고, 'Enter'를 누르면 작업을 계속합니다.")
        print("!"*50 + "\n")
        
        os.startfile(review_file) # 전용 에디터로 열기 (윈도우 전용)
        input("👉 수정을 마치셨나요? (Enter를 누르세요): ")
        
        # 수정된 내용 다시 읽기
        with open(review_file, "r", encoding="utf-8") as f:
            tagged_script = f.read()
    
    # 4. BGM 계획 로드 (한 번만)
    plan_path = os.path.join(BASE_DIR, plan_file)
    bgm_actions = []
    if os.path.exists(plan_path):
        with open(plan_path, "r", encoding="utf-8") as f:
            config = json.load(f)
            if config: bgm_actions = config[0].get("actions", [])

    # 5. 각 파일별 실제 믹싱 진행
    for mp3_path, srt_entries in target_data:
        voice_filename = os.path.basename(mp3_path)
        print(f"\n──────────────────────────────────────────────────")
        print(f"🎧 '{voice_filename}' 믹싱 작업을 시작합니다...")
        
        # --- A. AI SFX 믹싱 ---
        sfx_start = time.time()
        final_audio = AudioSegment.from_mp3(mp3_path)
        
        if tagged_script:
            # [수정] re.finditer를 사용하여 각 태그의 나타나는 시점을 추적
            total_script_len = len(tagged_script)
            audio_duration_ms = len(final_audio)

            for match in re.finditer(r'\[SFX:([^\]]+)\]\s*([^\s\]]+)?', tagged_script):
                sfx_name = match.group(1)
                follow_text = match.group(2)
                
                sfx_file = os.path.join(SFX_DIR, f"{sfx_name}.mp3")
                if os.path.exists(sfx_file):
                    found_time = None
                    if srt_entries and follow_text:
                        found_time = find_time_for_sfx(srt_entries, follow_text)
                    
                    if found_time is None: # 자막에서 못 찾았거나, 자막이 없거나, 뒤따르는 텍스트가 없을 때
                        ratio = match.start() / total_script_len
                        found_time = int(ratio * audio_duration_ms)
                        
                    if found_time is not None:
                        print(f"   🔊 SFX 추가: {sfx_name} @ {found_time/1000:.1f}s")
                        sfx_audio = AudioSegment.from_mp3(sfx_file) - 10
                        final_audio = final_audio.overlay(sfx_audio, position=found_time)
                else:
                    print(f"   ⚠️ SFX 누락: {sfx_name} (파일을 찾을 수 없음)")
        print(f"   ⏱️ SFX 믹싱 소요 시간: {time.time() - sfx_start:.2f}초")

        # --- B. 배경음악(BGM) 믹싱 ---
        for action in bgm_actions:
            bgm_file = action.get("bgm_file")
            start_time = action.get("start_time", "00:00")
            volume = action.get("volume", -25)
            fade_in = action.get("fade_in", 3000)
            fade_out = action.get("fade_out", 3000)
            loop = action.get("loop", True)

            bgm_path = os.path.join(BGM_DIR, bgm_file)
            if os.path.exists(bgm_path):
                print(f"   🎵 BGM 오버레이: {bgm_file} @ {start_time}")
                bgm = AudioSegment.from_mp3(bgm_path) + volume
                if fade_in > 0: bgm = bgm.fade_in(fade_in)
                if fade_out > 0: bgm = bgm.fade_out(fade_out)
                final_audio = final_audio.overlay(bgm, position=time_to_ms(start_time), loop=loop)
        
        # --- C. 최종 엔진 최적화 (가장 오래 걸리는 구간) ---
        post_start = time.time()
        print(f"   ⚙️ 최종 밸런싱 및 인코딩 중... (약 잠시만 기다려주세요)")
        
        # [최적화] 품질 저하 없이 속도를 위해 Compressor 설정을 약간 완화하거나 필요시에만 적용
        # final_audio = effects.compress_dynamic_range(final_audio, threshold=-20.0, ratio=4.0)
        final_audio = final_audio.normalize(headroom=0.1) # 훨씬 빠름 (단순 노멀라이즈)

        # 저장 (번호 자동 증가: 캡컷 인식 문제 해결)
        base_name = voice_filename.rsplit('.', 1)[0]
        counter = 1
        while True:
            output_filename = f"{base_name}-{counter}.mp3"
            output_path = os.path.join(DOWNLOADS_DIR, output_filename)
            if not os.path.exists(output_path):
                break
            counter += 1
            
        final_audio.export(output_path, format="mp3", bitrate="192k") # 비트레이트 지정으로 인코딩 속도 최적화
        print(f"✅ 완성: {output_path} (파트 소요: {time.time() - post_start:.2f}초)")

    elapsed = time.time() - start_time_all
    mins = int(elapsed // 60)
    secs = int(elapsed % 60)
    print(f"\n==================================================")
    print(f"✨ 모든 작업 완료! (총 소요 시간: {mins}분 {secs}초)")
    print(f"==================================================")

if __name__ == "__main__":
    apply_ai_sfx_and_bgm()

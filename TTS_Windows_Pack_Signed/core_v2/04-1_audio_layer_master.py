import os
import json
import re
import sys
import time
from pydub import AudioSegment, effects

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

# [Import AI Audio Logic]
sys.path.append(os.path.join(CORE_DIR, "engine"))
import sfx_generator

# [설정]
AudioSegment.converter = "/Users/a12/miniforge3/envs/qwen-tts/bin/ffmpeg"
AudioSegment.ffprobe = "/Users/a12/miniforge3/envs/qwen-tts/bin/ffprobe"

MOOD_KEYWORDS = {
    "Tense": ["검", "혈", "죽음", "습격", "위기", "긴장", "전투", "적", "공격", "혈투", "자객", "살기", "비명", "대결", "일격"],
    "Sad": ["눈물", "이별", "그리움", "슬픔", "아픔", "고통", "무덤", "통곡", "사라진", "애절", "한숨", "망령", "후회"],
    "Heroic": ["영웅", "승리", "도약", "희망", "기상", "웅장", "군대", "진격", "광명", "전설", "천하", "패기", "강림", "신화"],
    "Mystery": ["안개", "비밀", "동굴", "심연", "어둠", "미궁", "기괴", "비급", "은둔", "비기", "환영", "귀기", "지옥"],
    "Calm": ["바람", "숲", "평화", "잔잔", "명상", "찻잔", "자연", "산책", "고요", "햇살", "호수", "대화", "미소", "평온"]
}

def time_to_ms(time_str):
    try:
        parts = time_str.split(':')
        if len(parts) == 2: return (int(parts[0]) * 60 + int(parts[1])) * 1000
        if len(parts) == 3: return (int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])) * 1000
    except: return 0
    return 0

def srt_time_to_ms(srt_time_str):
    try:
        # 00:00:00,000 -> ms
        h, m, s_ms = srt_time_str.split(':')
        s, ms = s_ms.split(',')
        return (int(h) * 3600 + int(m) * 60 + int(s)) * 1000 + int(ms)
    except: return 0

def parse_srt(srt_path):
    """SRT 파일을 파싱하여 리스트로 반환"""
    if not os.path.exists(srt_path): return []
    try:
        with open(srt_path, "r", encoding="utf-8-sig") as f:
            content = f.read().strip()
        entries = []
        # 빈 줄 기준으로 블록 분리
        blocks = re.split(r'\n\s*\n', content)
        for block in blocks:
            lines = block.strip().splitlines()
            if len(lines) >= 3:
                # 시간 타임스태프 추출 (00:00:00,000 --> 00:00:00,000)
                times = re.findall(r'(\d{2}:\d{2}:\d{2},\d{3})', lines[1])
                if len(times) >= 2:
                    start = srt_time_to_ms(times[0])
                    end = srt_time_to_ms(times[1])
                    text = " ".join(lines[2:])
                    entries.append({'start': start, 'end': end, 'text': text})
        return entries
    except Exception as e:
        print(f"⚠️ SRT 파싱 오류: {e}")
        return []

def analyze_mood(script_text):
    """키워드 기반 분위기 분석"""
    mood_scores = {mood: 0 for mood in MOOD_KEYWORDS}
    clean_text = re.sub(r'[^\w\s]', '', script_text)
    for mood, keywords in MOOD_KEYWORDS.items():
        for kw in keywords:
            count = len(re.findall(re.escape(kw), clean_text))
            mood_scores[mood] += count
    
    sorted_moods = sorted(mood_scores.items(), key=lambda x: x[1], reverse=True)
    best_mood = sorted_moods[0][0] if sorted_moods[0][1] > 0 else "Calm"
    
    prompts = {
        "Tense": "Tense and dark Korean martial arts battle music, cinematic orchestra, traditional drums, 120bpm",
        "Sad": "Sad and emotional traditional Korean flute and cello music, melancholic, slow tempo",
        "Heroic": "Grand and heroic Korean martial arts theme, epic orchestral, powerful brass, traditional percussion",
        "Mystery": "Mysterious and spooky atmosphere with low drone and traditional instruments",
        "Calm": "Peaceful and calm traditional Korean orientation music, bamboo flute and string, Zen atmosphere"
    }
    return best_mood, prompts.get(best_mood, prompts["Calm"])

def run_unified_audio_master():
    print("\n" + "="*50)
    print("🚀 [Step 04-1] 통합 오디오 레이어 마스터 (SRT + AI)")
    print("="*50 + "\n")

    # 1. 대상 목소리 파일 및 자막(SRT) 찾기
    voice_candidates = sorted([f for f in os.listdir(DOWNLOADS_DIR) 
                                if f.endswith(".mp3") and any(x in f for x in ["_Full_Merged", "_Hybrid_Final", "_SmartHybrid"])],
                                key=lambda x: os.path.getmtime(os.path.join(DOWNLOADS_DIR, x)), reverse=True)
    
    if not voice_candidates:
        # 서브디렉토리에서도 검색 시도
        for sub in os.listdir(DOWNLOADS_DIR):
            sub_path = os.path.join(DOWNLOADS_DIR, sub)
            if os.path.isdir(sub_path):
                hits = [os.path.join(sub, f) for f in os.listdir(sub_path) 
                        if f.endswith(".mp3") and any(x in f for x in ["_Full_Merged", "_Hybrid_Final", "_SmartHybrid"])]
                voice_candidates.extend(hits)
        
        if not voice_candidates:
            print("❌ 믹싱할 목소리 합본 파일을 찾을 수 없습니다. (Downloads 폴더를 확인해 주세요)")
            return
        
        # 다시 정렬
        voice_candidates.sort(key=lambda x: os.path.getmtime(os.path.join(DOWNLOADS_DIR, x)), reverse=True)
    
    voice_path = os.path.join(DOWNLOADS_DIR, voice_candidates[0])
    srt_path = voice_path.replace(".mp3", ".srt")
    
    print(f"🎙️ 목소리 파일 로드: {os.path.basename(voice_path)}")
    voice_audio = AudioSegment.from_mp3(voice_path)
    audio_duration_ms = len(voice_audio)

    srt_entries = []
    if os.path.exists(srt_path):
        print(f"📄 자막 파일 로드: {os.path.basename(srt_path)}")
        srt_entries = parse_srt(srt_path)
    else:
        print("⚠️ 자막(SRT) 파일을 찾을 수 없습니다. 시간 계산이 부정확할 수 있습니다.")

    script_file = os.path.join(ROOT_DIR, "대본.txt")
    if not os.path.exists(script_file): script_file = os.path.join(CORE_DIR, "대본.txt")
    
    if not os.path.exists(script_file):
        print("❌ 대본.txt를 찾을 수 없습니다.")
        return
    
    with open(script_file, "r", encoding="utf-8") as f:
        script_text = f.read()

    # 2. BGM 계획 (플랜 파일 확인)
    plan_path = os.path.join(ROOT_DIR, "bgm_plan.json")
    if not os.path.exists(plan_path): plan_path = os.path.join(CORE_DIR, "bgm_plan.json")
    
    bgm_plan = None
    if os.path.exists(plan_path):
        print(f"📋 BGM 플랜 발견: {os.path.basename(plan_path)}")
        try:
            with open(plan_path, "r", encoding="utf-8") as f:
                bgm_plan = json.load(f)
        except: pass

    # AI 무드 분석 (BGM 플랜이 없을 경우를 대비한 자동 폴백)
    print("🤖 대본 분위기 분석 중...")
    mood, bgm_prompt = analyze_mood(script_text)
    print(f"✨ 분석된 무드: {mood}")
    
    auto_bgm_filename = f"AutoBGM_{mood}"
    auto_bgm_path = os.path.join(BGM_DIR, f"{auto_bgm_filename}.mp3")

    # 3. 효과음(SFX) 및 BGM 생성/확인
    sfx_tags = re.findall(r'\[SFX:([^\]]+)\]', script_text)
    print(f"🔍 발견된 효과음 태그: {len(sfx_tags)}개")
    
    for tag in sfx_tags:
        clean_name = sfx_generator.clean_sfx_name(tag)
        sfx_path = os.path.join(SFX_DIR, f"{clean_name}.mp3")
        if not os.path.exists(sfx_path):
            print(f"🔊 SFX 생성 중: {tag}")
            sfx_generator.generate_local_sfx(tag, clean_name)

    # BGM 작곡 (플랜에 없는 경우나 자동 모드일 때)
    if not bgm_plan and not os.path.exists(auto_bgm_path):
        print(f"🎵 BGM 작곡을 요청합니다 (약 30-60초)...")
        sfx_generator.generate_local_music(bgm_prompt, auto_bgm_filename, duration=30)

    # 4. 믹싱 레이어 구축
    final_audio = AudioSegment.silent(duration=audio_duration_ms)
    
    # BGM 레이어
    if bgm_plan:
        print("🎵 BGM 플랜 기반 레이어 믹스 중...")
        actions = bgm_plan[0].get("actions", [])
        for action in actions:
            bgm_file = action.get("bgm_file")
            bgm_path = os.path.join(BGM_DIR, bgm_file)
            if os.path.exists(bgm_path):
                print(f"   - Overlay: {bgm_file}")
                bgm = AudioSegment.from_mp3(bgm_path) + action.get("volume", -25)
                start_p = time_to_ms(action.get("start_time", "00:00"))
                final_audio = final_audio.overlay(bgm, position=start_p, loop=action.get("loop", True))
    elif os.path.exists(auto_bgm_path):
        print("🎵 자동 AI BGM 레이어 믹스 중...")
        bgm_audio = AudioSegment.from_mp3(auto_bgm_path)
        looped_bgm = (bgm_audio * (int(audio_duration_ms / len(bgm_audio)) + 1))[:audio_duration_ms]
        looped_bgm = looped_bgm.fade_in(3000).fade_out(3000) - 25
        final_audio = final_audio.overlay(looped_bgm)
    
    # SFX 레이어 (SRT 정밀 정렬)
    print("🔊 SFX 레이어 정밀 믹스 중...")
    sfx_count = 0
    # 스크립트를 SRT 순서에 맞춰 조각내어 분석
    if srt_entries:
        # 각 SRT 엔트리 텍스트에서 SFX 태그 찾기
        for entry in srt_entries:
            text = entry['text']
            found_sfx = re.findall(r'\[SFX:([^\]]+)\]', text)
            for sfx_tag in found_sfx:
                clean_name = sfx_generator.clean_sfx_name(sfx_tag)
                sfx_file = os.path.join(SFX_DIR, f"{clean_name}.mp3")
                if os.path.exists(sfx_file):
                    pos_ms = entry['start'] # 자막 시작점에 맞춤
                    sfx_audio = AudioSegment.from_mp3(sfx_file) - 6
                    final_audio = final_audio.overlay(sfx_audio, position=pos_ms)
                    sfx_count += 1
    
    # 태그가 남았거나 SRT에 없는 경우 (백업: 비율 계산)
    if sfx_count == 0:
        for match in re.finditer(r'\[SFX:([^\]]+)\]', script_text):
            tag = match.group(1).strip()
            clean_name = sfx_generator.clean_sfx_name(tag)
            if os.path.exists(os.path.join(SFX_DIR, f"{clean_name}.mp3")):
                ratio = match.start() / len(script_text)
                pos_ms = int(ratio * audio_duration_ms)
                sfx_audio = AudioSegment.from_mp3(os.path.join(SFX_DIR, f"{clean_name}.mp3")) - 8
                final_audio = final_audio.overlay(sfx_audio, position=pos_ms)
                sfx_count += 1

    print(f"✅ {sfx_count}개 효과음 믹스 완료")

    # 목소리 레이어 (상단)
    print("🎙️ 목소리 레이어 결합 중...")
    voice_audio = voice_audio.apply_gain(-0.5)
    final_audio = final_audio.overlay(voice_audio)

    # 5. 마스터링 및 저장
    print("🎚️ 최종 마스터링 진행 중...")
    final_audio = final_audio.normalize(headroom=0.1)
    
    ts = time.strftime("%m%d_%H%M")
    output_name = f"Master_Final_{ts}.mp3"
    output_path = os.path.join(DOWNLOADS_DIR, output_name)
    
    final_audio.export(output_path, format="mp3", bitrate="192k")
    
    print("\n" + "="*50)
    print(f"✨ 모든 오디오 공정 통합 완료! (자막 정밀 정렬 적용)")
    print(f"📍 결과물: {output_path}")
    print("="*50 + "\n")

if __name__ == "__main__":
    run_unified_audio_master()

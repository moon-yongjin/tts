import os
import time
import sys
import re
from pydub import AudioSegment

# [설정]
BASE_PATH = os.path.dirname(os.path.abspath(__file__))
DOWNLOADS_DIR = os.path.join(os.path.expanduser("~"), "Downloads")
LIB_DIR = os.path.join(BASE_PATH, "Library")
BGM_LIB_DIR = os.path.join(LIB_DIR, "bgm")

# FFmpeg 및 PATH 설정 (pydub 필수 설정)
FFMPEG_PATH = r"C:\Users\moori\Downloads\ffmpeg-2026-01-07-git-af6a1dd0b2-essentials_build\ffmpeg-2026-01-07-git-af6a1dd0b2-essentials_build\bin\ffmpeg"
FFPROBE_PATH = r"C:\Users\moori\Downloads\ffmpeg-2026-01-07-git-af6a1dd0b2-essentials_build\ffmpeg-2026-01-07-git-af6a1dd0b2-essentials_build\bin\ffprobe"
FFMPEG_DIR = os.path.dirname(FFMPEG_PATH)

AudioSegment.converter = FFMPEG_PATH
AudioSegment.ffprobe = FFPROBE_PATH
os.environ["PATH"] += os.pathsep + FFMPEG_DIR

# 분위기 키워드 정의
MOOD_KEYWORDS = {
    "Tense": ["검", "혈", "죽음", "습격", "위기", "긴장", "전투", "적", "공격", "혈투", "자객", "살기", "비명"],
    "Sad": ["눈물", "이별", "그리움", "슬픔", "아픔", "고통", "무덤", "통곡", "사라진", "애절", "한숨"],
    "Heroic": ["영웅", "승리", "도약", "희망", "기상", "웅장", "군대", "진격", "광명", "전설", "천하", "패기"],
    "Mystery": ["안개", "비밀", "동굴", "심연", "어둠", "미궁", "기괴", "비급", "은둔", "비기", "환영"],
    "Calm": ["바람", "숲", "평화", "잔잔", "명상", "찻잔", "자연", "산책", "고요", "햇살", "호수", "대화"]
}

def analyze_atmosphere_locally(script_text):
    """제미나이 없이 키워드로 분위기 분석"""
    mood_scores = {mood: 0 for mood in MOOD_KEYWORDS}
    
    # 특수문자 제거 후 분석
    clean_text = re.sub(r'[^\w\s]', '', script_text)
    
    for mood, keywords in MOOD_KEYWORDS.items():
        for kw in keywords:
            count = len(re.findall(re.escape(kw), clean_text))
            mood_scores[mood] += count
    
    # 가장 높은 점수의 분위기 선택
    sorted_moods = sorted(mood_scores.items(), key=lambda x: (x[1], x[0] == "Calm"), reverse=True)
    best_mood = sorted_moods[0][0]
    
    # 모든 점수가 0이면 기본 Calm
    if sum(mood_scores.values()) == 0:
        best_mood = "Calm"
        
    description = {
        "Tense": "긴박하고 어두운 무협 전투 분위기",
        "Sad": "애절하고 슬픈 감성 분위기",
        "Heroic": "웅장하고 희망찬 영웅적 분위기",
        "Mystery": "신비롭고 기괴한 어둠의 분위기",
        "Calm": "잔잔하고 평화로운 일상 분위기"
    }[best_mood]
    
    return {"mood": best_mood, "description": description, "scores": mood_scores}

def run_bgm_composer():
    print("🎙️ [Step 05] AI 배경음 작곡기 (Library-First) 가동...")
    
    if not os.path.exists(BGM_LIB_DIR):
        os.makedirs(BGM_LIB_DIR)

    # 1. 대본 읽기
    script_file = os.path.join(BASE_PATH, "대본.txt")
    if not os.path.exists(script_file):
        print("❌ 대본.txt를 찾을 수 없습니다.")
        return
    with open(script_file, "r", encoding="utf-8") as f:
        script_text = f.read()

    # 2. 로컬 키워드 분석
    print("🤖 키워드 기반 분위기 분석 중...")
    info = analyze_atmosphere_locally(script_text)
    print(f"✨ 분석 결과: {info['mood']} ({info['description']})")
    print(f"📊 감정 점수: {info['scores']}")
    
    # 3. 대상 목소리 파일 찾기
    voice_candidates = sorted([f for f in os.listdir(DOWNLOADS_DIR) if ("FINAL_MERGED" in f or "Full_Merged" in f) and f.endswith(".mp3")], 
                              key=lambda x: os.path.getmtime(os.path.join(DOWNLOADS_DIR, x)), reverse=True)
    if not voice_candidates:
        print("❌ 믹싱할 목소리 합본 파일을 찾을 수 없습니다. (01-1 단계를 먼저 진행해 주세요)")
        return
    
    voice_path = os.path.join(DOWNLOADS_DIR, voice_candidates[0])
    print(f"🎙️ 목소리 파일 로드: {os.path.basename(voice_path)}")
    voice_audio = AudioSegment.from_mp3(voice_path)
    audio_duration_ms = len(voice_audio)

    # 4. BGM 자산 로드
    asset_name = f"{info['mood']}.mp3"
    bgm_asset_path = os.path.join(BGM_LIB_DIR, asset_name)
    
    # 라이브러리에 없으면 안내 후 중단
    if not os.path.exists(bgm_asset_path):
        print(f"\n⚠️ 라이브러리에 '{asset_name}' 파일이 없습니다.")
        print(f"📂 '{BGM_LIB_DIR}' 위치에 {info['mood']} 분위기의 MP3 파일을 'Tense.mp3', 'Calm.mp3' 식으로 넣어주세요.")
        
        # 임시 조치: Downloads에 있는 BGM 자산이 있으면 자동 복사 시도
        found_in_dl = [f for f in os.listdir(DOWNLOADS_DIR) if info['mood'] in f and f.endswith(".mp3")]
        if found_in_dl:
            import shutil
            shutil.copy(os.path.join(DOWNLOADS_DIR, found_in_dl[0]), bgm_asset_path)
            print(f"✅ Downloads 폴더에서 발견한 파일을 라이브러리에 등록했습니다: {asset_name}")
        else:
            return

    bgm_asset = AudioSegment.from_mp3(bgm_asset_path)
    
    # 5. 루핑 및 믹싱
    print("🎚️ 배경음 루핑 및 최종 믹싱 중...")
    looped_bgm = (bgm_asset * (int(audio_duration_ms / len(bgm_asset)) + 1))[:audio_duration_ms]
    looped_bgm = looped_bgm.fade_in(3000).fade_out(3000) - 22 # 배경음은 조금 더 작게 (-22dB)
    
    # 최종 믹싱
    final_mixed = looped_bgm.overlay(voice_audio)
    
    # 6. 저장
    ts = time.strftime("%m%d_%H%M")
    output_name = f"최종_영상용_합본_{ts}.mp3"
    output_path = os.path.join(DOWNLOADS_DIR, output_name)
    
    final_mixed.export(output_path, format="mp3", bitrate="192k")
    print(f"\n✅ 모든 작업 완료!")
    print(f"📂 결과물 위치: {output_path}")

if __name__ == "__main__":
    run_bgm_composer()

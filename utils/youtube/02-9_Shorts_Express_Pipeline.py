import os
import sys
import json
import re
from pathlib import Path

# 모듈 경로 추가 및 임포트
sys.path.append(str(Path(__file__).parent / "lib"))
import video_downloader as vd
import story_analyzer as sa
import smart_diarizer as sd
import shorts_generator as sg

# [설정]
PROJECT_ROOT = Path(__file__).parent.parent.parent
CONFIG_PATH = PROJECT_ROOT / "config.json"
DOWNLOADS_DIR = Path.home() / "Downloads"
EXTRACTED_ASSETS_DIR = DOWNLOADS_DIR / "extracted_assets"
EXTRACTED_ASSETS_DIR.mkdir(parents=True, exist_ok=True)

def load_config():
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

CONFIG = load_config()
GEMINI_KEY = CONFIG.get("Gemini_API_KEY")

def main():
    print("==========================================")
    print("🚀 [V4-Modular] 쇼츠 익스프레스 파이프라인")
    print("==========================================")
    
    inp = ""
    if len(sys.argv) > 1:
        inp = sys.argv[1]
        print(f"📥 명령줄 인자 감지됨: {inp}")
    else:
        inp = input("🔗 유튜브 URL 또는 로컬 MP4 파일 경로를 입력하세요: ").strip()
    
    if not inp: return

    is_local = os.path.exists(inp) and inp.lower().endswith(".mp4")
    
    if is_local:
        full_video_path = Path(inp)
        title = full_video_path.stem
        ts_desc = [] # 로컬 파일은 목차 정보가 기본적으로 없음
        print(f"📁 로컬 파일 감지됨: {full_video_path.name}")
    else:
        url = inp
        # 1. 메타데이터 및 다운로드
        title, ts_desc = vd.get_video_metadata(url)
        if not title: return
        
        safe_title = re.sub(r'[^\w\s-]', '', title).strip().replace(' ', '_')
        full_video_path = DOWNLOADS_DIR / f"{safe_title}_full.mp4"
        
        if not vd.download_video(url, full_video_path):
            return

    safe_title = re.sub(r'[^\w\s-]', '', title).strip().replace(' ', '_')

    # 2. 사연 목록 분석
    print("📄 사연 목록 분석 중...")
    if not ts_desc:
        visual_ts = sa.get_timestamps_from_visual(full_video_path)
        # 지능형 목차 정제
        ts_desc = sa.refine_timestamps_with_gemini(GEMINI_KEY, "", visual_ts)
    
    print("\n📍 발견된 사연 목록:")
    for i, (ts, t) in enumerate(ts_desc, 1):
        print(f"   {i}) {ts} - {t}")
    
    try:
        choice = int(input("\n👉 작업할 사연 번호를 선택하세요: ")) - 1
    except ValueError:
        return
        
    selected_ts = ts_desc[choice]
    start_ts = selected_ts[0]
    end_ts = ts_desc[choice+1][0] if choice+1 < len(ts_desc) else None
    
    # 사연별 임시 컷팅
    story_dir = EXTRACTED_ASSETS_DIR / f"{safe_title}_Story_{choice+1}"
    story_dir.mkdir(parents=True, exist_ok=True)
    story_video = story_dir / "story_origin.mp4"
    
    import subprocess
    cmd = ["ffmpeg", "-y", "-ss", start_ts]
    if end_ts: cmd += ["-to", end_ts]
    cmd += ["-i", str(full_video_path), "-c", "copy", str(story_video)]
    vd.run_command(cmd, "사연 클립 추출")

    # 3. 화자 분리 (Diarization)
    audio_path = story_video.with_suffix(".wav")
    vd.run_command(["ffmpeg", "-y", "-i", str(story_video), "-vn", "-acodec", "pcm_s16le", "-ar", "16000", str(audio_path)], "오디오 추출")
    
    segments = sd.transcribe_with_whisper(audio_path)
    diarized_segments = sd.diarize_with_gemini(GEMINI_KEY, segments)
    
    # --- [수동 제어 Phase] ---
    transcript_file = story_dir / "Editable_Transcript.txt"
    with open(transcript_file, "w", encoding="utf-8") as f:
        for s in diarized_segments:
            f.write(f"[{s.get('start', 0):.1f}s] {s.get('speaker', '?')}: {s.get('text', '')}\n")
            
    print("\n" + "📝" * 20)
    print(f"📍 대본 추출 완료: {transcript_file.name}")
    print("👉 위 파일을 열어서 '필요 없는 문장'을 지우고 저장해 주세요.")
    print("👉 하찮은 부분을 다 지운 후 터미널에서 '엔터'를 누르면 합성을 시작합니다.")
    print("📝" * 20)
    
    os.system(f"open '{transcript_file}'")
    input("\n✅ 편집을 완료했으면 [엔터]를 누르세요...")
    
    # 수정된 대본 읽기
    edited_segments = []
    if transcript_file.exists():
        with open(transcript_file, "r", encoding="utf-8") as f:
            edited_lines = f.readlines()
            
        for line in edited_lines:
            match = re.search(r"\[(\d+\.?\d*)s\]", line)
            if match:
                start_val = float(match.group(1))
                # 원본 세그먼트에서 매칭되는 것 찾기
                for s in diarized_segments:
                    if abs(s.get('start', 0) - start_val) < 0.1:
                        edited_segments.append(s)
                        break
    
    # 4. 최종 쇼츠 생성 (수동 모드 또는 자동 모드)
    if edited_segments:
        print("💡 수동 편집된 대본을 기반으로 합성을 시작합니다...")
        script_p, audio_p = sg.generate_shorts_from_manual_segments(edited_segments, story_video, story_dir)
    else:
        print("⚠️ 편집된 내용이 없어 기존 자동 모드로 진행합니다.")
        script_p, audio_p = sg.generate_golden_shorts(GEMINI_KEY, diarized_segments, story_video, story_dir)
    
    if script_p:
        print("\n" + "✨" * 20)
        print("✅ 쇼츠 원클릭 준비 완료!")
        print(f"📄 대본: {script_p.name}")
        print(f"🎙️ 음성: {audio_p.name}")
        print(f"📂 폴더: {story_dir}")
        print("✨" * 20)
        os.system(f"open {story_dir}")

if __name__ == "__main__":
    main()

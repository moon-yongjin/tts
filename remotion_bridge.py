import os
import shutil
import json
import re
from pathlib import Path

# [설정] 경로
PROJECT_ROOT = Path("/Users/a12/projects/tts")
DOWNLOADS = Path.home() / "Downloads"
REMOTION_PUBLIC = PROJECT_ROOT / "remotion-hello-world/public"
REMOTION_IMAGES = REMOTION_PUBLIC / "images"
TARGET_SCRIPT = PROJECT_ROOT / "대본.txt"

def get_latest_file(pattern):
    files = list(DOWNLOADS.glob(pattern))
    if not files:
        return None
    return max(files, key=os.path.getmtime)

def run_bridge():
    print("====================================================")
    print("🚀 리모션 애셋 브릿지 (Remotion Asset Bridge)")
    print("====================================================")

    # 1. 최신 오디오 및 자막 찾기
    latest_wav = get_latest_file("DualSpeaker_*.wav")
    latest_srt = get_latest_file("DualSpeaker_*.srt")

    if not latest_wav or not latest_srt:
        print("⚠️ 최신 DualSpeaker 파일을 찾을 수 없습니다. (동기화 건너뜀)")
    else:
        print(f"🎵 최신 음성: {latest_wav.name}")
        shutil.copy(latest_wav, REMOTION_PUBLIC / "latest_drama.wav")
        shutil.copy(latest_srt, REMOTION_PUBLIC / "latest_drama.srt")
        print("✅ 오디오 및 자막 동기화 완료 (latest_drama.wav/srt)")

    # 2. 이미지 동기화
    src_images_dir = DOWNLOADS / "Script_Scenes_Dynamic"
    if src_images_dir.exists():
        # 이미지 폴더 정리
        if REMOTION_IMAGES.exists():
            shutil.rmtree(REMOTION_IMAGES)
        REMOTION_IMAGES.mkdir(parents=True)

        found_images = sorted([f.name for f in src_images_dir.glob("*.png")])
        for img in found_images:
            shutil.copy(src_images_dir / img, REMOTION_IMAGES / img)
        
        print(f"📸 이미지 {found_images.__len__()}장 동기화 완료")
    else:
        print("⚠️ 이미지 소스 폴더를 찾을 수 없습니다: Downloads/Script_Scenes_Dynamic")
        found_images = []

    # 3. 메타데이터 업데이트 (제목 및 스타일 보존)
    metadata_path = REMOTION_PUBLIC / "metadata.json"
    metadata = {}
    if metadata_path.exists():
        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)

    # 기존 제목이 있고 유효하다면 유지
    current_title = metadata.get("title", "")
    new_title = "배은망덕한 자식들의 몰락" # 기본값
    if TARGET_SCRIPT.exists():
        with open(TARGET_SCRIPT, "r", encoding="utf-8") as f:
            lines = [l.strip() for l in f.readlines() if l.strip()]
            if lines:
                new_title = lines[0]

    # 제목 업데이트 조건: 제목이 없거나, 기본값이거나, 방금 생성된 '천구백...' 인 경우만 업데이트
    if not current_title or current_title in ["배은망덕한 자식들의 몰락", "", "천구백칠십팔년 팔월 강릉 청자다방"]:
        metadata["title"] = new_title
        print(f"📄 제목 업데이트: {new_title}")
    else:
        print(f"📄 기존 제목 유지: {current_title}")

    metadata["audio_file"] = "latest_drama.wav"
    
    # 이미지는 새로 들어온 게 있을 때만 업데이트
    if found_images:
        metadata["images"] = found_images
    elif not metadata.get("images"):
        metadata["images"] = []

    # 스타일 블록이 없으면 기본값 생성
    if "style" not in metadata:
        metadata["style"] = {
            "title": {
                "topPart": {"fontSize": "48px", "color": "black", "backgroundColor": "white"},
                "bottomPart": {"fontSize": "110px", "color": "#FF00FF"}
            },
            "subtitle": {"fontSize": "46px", "color": "white", "bottom": 350}
        }

    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    print(f"📄 메타데이터 업데이트 완료 (최종 제목: {metadata['title']})")
    print("====================================================")
    print("✨ 모든 작업이 완료되었습니다! 리모션 스튜디오를 확인하세요.")

if __name__ == "__main__":
    run_bridge()

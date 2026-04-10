import sys
import json
from pathlib import Path

# 모듈 경로 추가
sys.path.append("/Users/a12/projects/tts/utils/youtube/lib")
import auto_remix_engine as are

# 설정 로드
with open("/Users/a12/projects/tts/config.json", "r") as f:
    config = json.load(f)
GEMINI_KEY = config.get("Gemini_API_KEY")

# 데이터 경로
diarized_json = Path("/Users/a12/Downloads/extracted_assets/test_story_04/04_Diarized_Result_Pre_Shorts.json")
video_source = Path("/Users/a12/Downloads/100분_눈물_콧물_주의_슬픈_사연_모음_책임감이라는_단어가_주는_마음의_무게에서_벗어나_나를_먼저_돌아보기_김창옥쇼2_clips/04_치매_시어머니를_모시며_앞집_아저씨처럼_느껴지는_남편.mp4")
output_dir = Path("/Users/a12/Downloads/extracted_assets/test_story_04_v5_auto")

# 자동화 리믹스 실행
print("🚀 V5 자동 편집 엔진 기동 중...")
result = are.run_auto_remix(GEMINI_KEY, diarized_json, video_source, output_dir)

if result:
    wav, txt = result
    print(f"\n✨ 자동 리믹스 완료!")
    print(f"🎙️ 오디오: {wav}")
    print(f"📄 대본: {txt}")
else:
    print("\n❌ 리믹스 생성 실패")

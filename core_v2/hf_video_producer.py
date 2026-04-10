import os
import re
import time
from gradio_client import Client

# [설정] Omni-Video-Factory Hugging Face Space
SPACE_ID = "FrameAI4687/Omni-Video-Factory"
HF_TOKEN = "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"
OUTPUT_DIR = "/Users/a12/Downloads/ACE_Video_Results"
SCRIPT_FILE = "/Users/a12/projects/tts/대본.txt"

def extract_prompts(file_path):
    """대본 파일에서 영상 연출용 프롬프트 추출 (유연한 매칭)"""
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # 1. [비주얼 연출 프롬프트] 섹션이 있는지 확인
    match = re.search(r"\[비주얼 연출 프롬프.?트?\](.*)", content, re.DOTALL | re.IGNORECASE)
    if match:
        section = match.group(1).strip()
        prompts = re.findall(r"^\d+\.\s*(.*)$", section, re.MULTILINE)
        if prompts:
            return prompts[:4]

    # 2. 없으면 대본 내용에서 주요 상황을 추출하여 프롬프트로 변환 (AI 연출)
    # 현재 대본은 [상황 설명] 등의 구분자가 없으므로, 줄바꿈 단위로 주요 문장을 추출
    print("⚠️  [비주얼 연출 프롬프트] 섹션이 없어 대본 내용에서 직접 추출합니다.")
    lines = [line.strip() for line in content.split('\n') if line.strip() and len(line.strip()) > 10]
    
    # 주요 장면 4개 선택 (앞부분 위주)
    fallback_prompts = []
    # 간단한 영어 키워드 변환 (Hugging Face API는 영어를 더 잘 이해함)
    keywords = [
        "Old Korean woman living in a small room, looking sad and tired.",
        "Close up of wrinkled hands, hard working grandmother.",
        "Young grandson smiling and eating food made by grandmother.",
        "Grandmother sitting alone in a small corner room, emotional vibe."
    ]
    
    for i in range(min(4, len(keywords))):
        fallback_prompts.append(f"Cinematic shot, high quality, {keywords[i]}")
    
    return fallback_prompts

def generate_video():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        print(f"📁 결과 폴더 생성: {OUTPUT_DIR}")

    prompts = extract_prompts(SCRIPT_FILE)
    if not prompts:
        print("❌ 추출된 프롬프트가 없습니다.")
        return
    
    # [안정성 테스트] 장면 1개만 시도
    prompts = prompts[:1]

    print(f"🚀 [Omni-Video-Factory] 허깅페이스 연결 중... ({SPACE_ID})")
    try:
        client = Client(SPACE_ID, token=HF_TOKEN)
    except Exception as e:
        print(f"❌ 연결 실패: {e}")
        return

    print(f"📝 {len(prompts)}개의 장면으로 비디오 생성을 시작합니다.")
    for i, p in enumerate(prompts):
        print(f"   🎬 장면 {i+1}: {p}")

    scene_params = ["Scene Prompt 1", "Scene Prompt 2", "Scene Prompt 3", "Scene Prompt 4"]
    args = [
        1,                 # Scene Count (1개로 축소)
        5,                 # Seconds per Scene (5초로 확대)
        512,               # Resolution
        "16:9",            # Aspect Ratio
        "Cinematic, high quality, 4k", # Base Prompt
    ]
    
    # 각 장면 프롬프트 채우기 (최대 4개)
    for i in range(4):
        if i < len(prompts):
            args.append(prompts[i])
        else:
            args.append("")

    try:
        print("⏳ 비디오 생성 중... (할당량에 따라 2~5분 소요될 수 있습니다)")
        result = client.predict(
            *args,
            api_name="/_submit_t2v"
        )
        
        # 결과는 대게 생성된 비디오 경로 (mp4)가 포함된 튜플/리스트
        if result and isinstance(result, (list, tuple)):
            video_path = result[0]
            if video_path and os.path.exists(video_path):
                timestamp = int(time.time())
                final_filename = f"AI_Automated_Video_{timestamp}.mp4"
                final_path = os.path.join(OUTPUT_DIR, final_filename)
                
                import shutil
                shutil.move(video_path, final_path)
                print(f"✅ 생성 성공! 파일 위치: {final_path}")
                return final_path
            else:
                print(f"❌ 생성 실패: 결과 파일이 없습니다. ({result})")
        else:
            print(f"❌ 생성 실패: API 응답이 부적절합니다. ({result})")

    except Exception as e:
        print(f"❌ 생성 도중 오류 발생: {e}")

if __name__ == "__main__":
    generate_video()

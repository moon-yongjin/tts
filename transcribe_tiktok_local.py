import os
import glob
from google import genai
from google.oauth2 import service_account
from google.genai import types

# --- [설정] ---
TIKTOK_DIR = os.path.expanduser("~/Downloads/tiktok_downloads_korea1233211")
OUTPUT_FILE = os.path.expanduser("~/Downloads/틱톡_대본모음_korea1233211.txt")
CREDENTIALS_PATH = "/Users/a12/projects/tts/core_v2/service_account.json"

# --- [Gemini 클라이언트 설정] ---
try:
    credentials = service_account.Credentials.from_service_account_file(
        CREDENTIALS_PATH,
        scopes=['https://www.googleapis.com/auth/cloud-platform']
    )
    client = genai.Client(
        vertexai=True, 
        project="ttss-483505", 
        location="us-central1", 
        credentials=credentials
    )
    print("✅ Gemini 클라이언트 초기화 성공")
except Exception as e:
    print(f"❌ Gemini Error: {e}")
    exit()

def transcribe_video_with_gemini(file_path):
    print(f"  진행 중: Gemini로 영상 분석 중... ({os.path.basename(file_path)})")
    try:
        # 1. 파일 읽기
        with open(file_path, "rb") as f:
            file_bytes = f.read()

        # 2. 프롬프트 생성
        prompt = """
        이 영상은 한국어 틱톡 영상입니다. 
        영상에 나오는 모든 대사를 그대로 받아적어 대본(Transcript)을 만들어주세요. 
        대사 외에 다른 부가 설명이나 인사말 등은 제외하고 **오직 들리는 한국어 대사만** 공백으로 이어붙여서 쭉 적어주세요.
        """
        
        # 3. Gemini 호출 (MP4 지원)
        response = client.models.generate_content(
            model="publishers/google/models/gemini-2.0-flash-001",
            contents=[prompt, types.Part.from_bytes(data=file_bytes, mime_type="video/mp4")]
        )
        return response.text.strip()
    except Exception as e:
        print(f"  ❌ Gemini 변환 실패: {e}")
        return f"[Gemini 변환 실패]"

def main():
    print("--- 틱톡 로컬 파일 대본 추출 시작 ---")
    video_files = sorted(glob.glob(os.path.join(TIKTOK_DIR, "*.mp4")))
    
    # 이미 처리된 파일 목록 불러오기
    processed_files = []
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
            processed_files = re.findall(r'\[\d+\] ([\w\.-]+)', content)
    
    # 새로운 파일만 필터링
    new_video_files = [f for f in video_files if os.path.basename(f) not in processed_files]
    
    print(f"전체 {len(video_files)}개 중 {len(new_video_files)}개의 새로운 영상을 처리합니다.")
    
    if not new_video_files:
        print("새롭게 처리할 영상이 없습니다.")
        return

    # 'a' 모드로 열어서 기존 파일에 추가
    with open(OUTPUT_FILE, 'a', encoding='utf-8') as f:
        start_idx = len(processed_files) + 1
        for i, video_path in enumerate(new_video_files):
            filename = os.path.basename(video_path)
            print(f"\n({i+1}/{len(new_video_files)}) 처리 중...: {filename}")
            
            transcript = transcribe_video_with_gemini(video_path)
            print(f"  ✅ 대본 추출 완료 (길이: {len(transcript)}자)")
            
            f.write(f"[{start_idx + i}] {filename}\n")
            f.write(f"대본: {transcript}\n")
            f.write("-" * 50 + "\n\n")
            
    print(f"\n🎉 모든 처리가 완료되었습니다! 결과 저장: {OUTPUT_FILE}")

if __name__ == "__main__":
    import re
    main()

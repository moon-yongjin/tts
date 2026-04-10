import os
import time
from gradio_client import Client

SPACE_ID = "FrameAI4687/Omni-Video-Factory"
HF_TOKEN = "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"
OUTPUT_DIR = "/Users/a12/Downloads/ACE_Video_Results"

# 허깅페이스 오라 가이드 프롬프트 4개 (텍스트 기반 다이렉트 생성)
prompts = [
    "Extreme microscopic macro close-up of a mosquito's head and proboscis hovering. Cinematic side lighting, dark atmosphere, ultra-detailed 4k.",
    "Microscopic cellular-level cross-section view of a mosquito proboscis piercing into transparent human skin layers searching for a vessel.",
    "Inside a transparent biological tube, crimson red blood cells (erythrocytes) rushing through like a high-speed conveyor belt fluid stream.",
    "Extreme macro close-up of a mosquito's abdomen expanding and translucent skin glowing bright red with glowing blood volume inside."
]

def generate_video():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        print(f"📁 결과 폴더 생성: {OUTPUT_DIR}")

    print(f"🚀 [Hugging Expert] Connecting to {SPACE_ID} for T2V generation...")
    try:
        client = Client(SPACE_ID, token=HF_TOKEN)
    except Exception as e:
        print(f"❌ 연결 실패: {e}")
        return

    # API Endpoint 파라미터 구성
    # predict(scene_count, seconds_per_scene, resolution, aspect_ratio, base_prompt, s1, s2, s3, s4)
    args = [
        "4",               # Scene Count (str Literal)
        "5",               # Seconds per Scene (str Literal)
        "512",              # Resolution (str Literal)
        "9:16",            # Aspect Ratio (TikTok 포맷)
        "Photorealistic cinematic microbiology, high quality, 4k", # Base Prompt
        prompts[0],
        prompts[1],
        prompts[2],
        prompts[3]
    ]

    try:
        print("⏳ [Hugging Expert] 4개 장면 비디오 생성 요청 중... (할당량 비례 3~5분 소요)")
        # _submit_t2v API 호출
        result = client.predict(
            *args,
            api_name="/_submit_t2v"
        )
        
        print(f"\n📜 --- API Response ---")
        print(result)
        print("-----------------------\n")

        # 결과 파싱 (Gradio는 주로 튜플이며 첫번째가 비디오 경로일 수 있음)
        if result and isinstance(result, (list, tuple)):
            # 결과 구조 분석: (status_text, video_dict_or_path, ...)
            # endpoint 리턴형: (generation_status, generated_video, value_71, ...)
            # generated_video 는 dict 형태인듯 : dict(video: filepath, subtitles: filepath)
            
            video_info = result[1] # 2번째 인자
            video_path = None
            if isinstance(video_info, dict) and "video" in video_info:
                 video_path = video_info["video"]
            elif isinstance(video_info, str):
                 video_path = video_info # 가끔 다이렉트 경로일 때도 있음

            if video_path and os.path.exists(video_path):
                timestamp = int(time.time())
                final_path = os.path.join(OUTPUT_DIR, f"Hugging_Mosquito_Short_{timestamp}.mp4")
                
                import shutil
                shutil.move(video_path, final_path)
                print(f"✅ 생성 성공! 파일 저장됨: {final_path}")
                return
            else:
                 print(f"⚠️ 비디오 경로를 추출할 수 없지만 실행은 완료됨. 결과 타입: {type(video_info)}")

    except Exception as e:
        print(f"❌ 대기열 구동 실패: {e}")

if __name__ == "__main__":
    generate_video()

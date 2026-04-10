import os
import shutil
import time
from gradio_client import Client, handle_file

# [설정] 사용자 지정 Wan 2.2 First-Last Frame Space
SPACE_ID = "cakegreen/Wan-2-2-first-last-frame"
# 사용자 PRO 토큰
HF_TOKEN = "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"
OUTPUT_DIR = "/Users/a12/Downloads/Toffee_Wan22_Cakegreen"

# 이미지 경로 (최근 사용한 주모 이미지 01 -> 02)
START_IMG = "/Users/a12/Downloads/Script_Scenes_Dynamic/Jumo_Idol_Joseon_01.png"
END_IMG = "/Users/a12/Downloads/Script_Scenes_Dynamic/Jumo_Idol_Joseon_02.png"

def generate_wan22_sample():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        print(f"📁 결과 폴더 생성됨: {OUTPUT_DIR}")
    
    print(f"🚀 [Wan 2.2] {SPACE_ID} 연결 중...")
    try:
        client = Client(SPACE_ID, token=HF_TOKEN)
    except Exception as e:
        print(f"❌ 연결 실패: {e}")
        return
    
    # [핵심] 3초 설정 및 일관성 위주 프롬프트
    prompt = "A high-quality cinematic video where the woman subtly blinks and shifts her weight. No new objects, maintain perfect consistency with the images."
    
    print(f"🎬 Wan 2.2 비디오 생성 시작 (5초)...")
    try:
        # API: predict(start_image_pil, end_image_pil, prompt, negative_prompt, duration_seconds, steps, ..., api_name="/generate_video")
        result = client.predict(
            start_image_pil=handle_file(START_IMG),
            end_image_pil=handle_file(END_IMG),
            prompt=prompt,
            negative_prompt="low quality, distorted, static, text, watermark, changing background, morphing artifacts",
            duration_seconds=5.0, # 사용자 요청: 5초
            steps=8,
            guidance_scale=1.0,
            guidance_scale_2=1.0,
            seed=42,
            randomize_seed=True,
            api_name="/generate_video"
        )
        
        # 결과 구조: (generated_video, seed)
        video_temp_path, seed = result
            
        timestamp = int(time.time())
        final_filename = f"Wan22_Cakegreen_Sample_{int(seed)}.mp4"
        final_path = os.path.join(OUTPUT_DIR, final_filename)
        
        shutil.move(video_temp_path, final_path)
        print(f"✅ 생성 성공! 파일 위치: {final_path}")
        return final_path
        
    except Exception as e:
        print(f"❌ 생성 도중 오류 발생: {e}")
        return None

if __name__ == "__main__":
    generate_wan22_sample()

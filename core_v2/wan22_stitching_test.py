import os
import shutil
import time
from gradio_client import Client, handle_file

# [설정] Wan 2.2 First-Last Frame (더 안정적인 모델)
SPACE_ID = "multimodalart/wan-2-2-first-last-frame"
HF_TOKEN = "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"
OUTPUT_DIR = "/Users/a12/Downloads/Toffee_Wan22_Test"

# 테스트용 이미지 (구도가 가장 일관된 것을 선택)
START_IMG = "/Users/a12/Downloads/Script_Scenes_Dynamic/Jumo_Idol_Joseon_04.png"
END_IMG = "/Users/a12/Downloads/Script_Scenes_Dynamic/Jumo_Idol_Joseon_05.png"

def generate_wan22_stitch():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    
    print(f"🚀 [Wan 2.2] 더 안정적인 모델로 재시도 중... ({SPACE_ID})")
    try:
        client = Client(SPACE_ID, token=HF_TOKEN)
    except Exception as e:
        print(f"❌ 연결 실패: {e}")
        return
    
    # [핵심] 헛소리 방지용 극사실적 프롬프트
    # 배경이나 새로운 사물을 설명하지 않고, 인물의 '미세한 움직임'만 지시
    prompt = "A high-quality cinematic video where the woman subtly blinks and shifts her weight. No new objects, maintain perfect consistency with the images."
    
    print(f"🎬 Wan 2.2 비디오 생성 시작...")
    try:
        # Wan 2.2 API 구조에 맞춘 호출 (보통 LTX보다 파라미터가 단순함)
        result = client.predict(
            image=handle_file(START_IMG),
            last_image=handle_file(END_IMG),
            prompt=prompt,
            negative_prompt="low quality, distorted, static, text, watermark, changing background, morphing artifacts",
            api_name="/predict"
        )
        
        # 결과물 처리
        video_temp_path = result
        timestamp = int(time.time())
        final_filename = f"Wan22_Jumo_Test_{timestamp}.mp4"
        final_path = os.path.join(OUTPUT_DIR, final_filename)
        
        shutil.move(video_temp_path, final_path)
        print(f"✅ 생성 성공! 파일 위치: {final_path}")
        return final_path
        
    except Exception as e:
        print(f"❌ 생성 도중 오류 발생: {e}")
        return None

if __name__ == "__main__":
    generate_wan22_stitch()

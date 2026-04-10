import os
import shutil
import time
from gradio_client import Client, handle_file

# [설정] Wan 2.2 First-Last Frame
SPACE_ID = "multimodalart/wan-2-2-first-last-frame"
# hf_token은 환경변수로 처리하거나, 필요 없다면 제외
HF_TOKEN = "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"
OUTPUT_DIR = "/Users/a12/Downloads/Toffee_Wan22_Production"

def generate_wan22_interpolation(start_img, end_img, index):
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    
    print(f"🚀 [Wan 2.2] 장면 {index} 생성 시도 중 ({os.path.basename(start_img)} -> {os.path.basename(end_img)})")
    try:
        # 최신 gradio_client는 token을 매개변수로 받지 않는 경우가 있으므로 환경변수로 설정
        os.environ["HF_TOKEN"] = HF_TOKEN
        client = Client(SPACE_ID)
    except Exception as e:
        print(f"❌ 연결 실패: {e}")
        return None
    
    prompt = "A high-quality cinematic video with natural movement. Maintain perfect consistency between the two images. Beautiful traditional Joseon style."
    
    try:
        # 이 스페이스의 API 구조를 확인해야 하지만, 일단 기본 predict 사용
        result = client.predict(
            image=handle_file(start_img),
            last_image=handle_file(end_img),
            prompt=prompt,
            negative_prompt="low quality, distorted, static, text, watermark, changing background, morphing artifacts",
            api_name="/predict"
        )
        
        video_temp_path = result
        final_filename = f"Wan22_Stitch_{index}_{int(time.time())}.mp4"
        final_path = os.path.join(OUTPUT_DIR, final_filename)
        
        shutil.move(video_temp_path, final_path)
        print(f"✅ 생성 성공: {final_path}")
        return final_path
        
    except Exception as e:
        print(f"❌ 생성 도중 오류 발생: {e}")
        # API 구조가 다를 수 있으므로 에러 메시지 상세 출력
        return None

if __name__ == "__main__":
    img1 = "/Users/a12/Downloads/1.png"
    img2 = "/Users/a12/Downloads/2.png"
    img3 = "/Users/a12/Downloads/3.png"
    
    # 1 -> 2 생성
    generate_wan22_interpolation(img1, img2, 1)
    # 2 -> 3 생성
    generate_wan22_interpolation(img2, img3, 2)

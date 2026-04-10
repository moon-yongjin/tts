import os
import shutil
import time
from gradio_client import Client, handle_file

# [설정] Wan 2.1 FLF2V (First-Last Frame to Video) Hugging Face Space
SPACE_ID = "vaibhavpandeyvpz/Wan2.1-FLF2V"
# 사용자 PRO 토큰
HF_TOKEN = "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"
OUTPUT_DIR = "/Users/a12/Downloads/Toffee_Wan21_Sample"

# 테스트용 이미지 (구도가 가장 일관된 것을 선택)
START_IMG = "/Users/a12/Downloads/Script_Scenes_Dynamic/Jumo_Idol_Joseon_01.png"
END_IMG = "/Users/a12/Downloads/Script_Scenes_Dynamic/Jumo_Idol_Joseon_02.png"

def generate_wan21_stitch():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        print(f"📁 결과 폴더 생성됨: {OUTPUT_DIR}")
    
    print(f"🚀 [Wan 2.1] 허깅페이스 스페이스 연결 중... ({SPACE_ID})")
    try:
        client = Client(SPACE_ID, token=HF_TOKEN)
    except Exception as e:
        print(f"❌ 연결 실패: {e}")
        return
    
    # [핵심] 일관성 유지를 위한 최소한의 프롬프트
    prompt = "A high-quality cinematic video, the woman subtly moves her head and blinks naturally, maintain consistency with the provided images, 8k resolution."
    
    print(f"🎬 Wan 2.1 비디오 생성(보간) 시작...")
    print(f"   - 시작 이미지: {os.path.basename(START_IMG)}")
    print(f"   - 끝 이미지: {os.path.basename(END_IMG)}")
    
    try:
        # API 검사 결과에 따른 파라미터 구성 (보통 입력을 순서대로 넣음)
        # predict(first_frame, prompt, last_frame, shift, n_frames, api_name="/predict")
        # 실제 API 구조는 스페이스마다 다를 수 있으므로 /predict 또는 명시적 이름을 사용
        result = client.predict(
            first_frame=handle_file(START_IMG),
            prompt=prompt,
            last_frame=handle_file(END_IMG),
            shift=3.0,
            n_frames=81, # 약 3-4초 분량 (24fps 기준)
            api_name="/predict"
        )
        
        # 결과물 처리 (video_path)
        video_temp_path = result
        timestamp = int(time.time())
        final_filename = f"Wan21_Jumo_Stitch_{timestamp}.mp4"
        final_path = os.path.join(OUTPUT_DIR, final_filename)
        
        shutil.move(video_temp_path, final_path)
        print(f"✅ 생성 성공! 파일 위치: {final_path}")
        return final_path
        
    except Exception as e:
        print(f"❌ 생성 도중 오류 발생: {e}")
        return None

if __name__ == "__main__":
    generate_wan21_stitch()

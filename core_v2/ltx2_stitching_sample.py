import os
import shutil
import time
from gradio_client import Client, handle_file

# [설정] LTX-2 First-Last Frame Hugging Face Space 정보
SPACE_ID = "linoyts/ltx-2-first-last-frame"
# 사용자 PRO 토큰 (기존 파일에서 확인됨)
HF_TOKEN = "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"
OUTPUT_DIR = "/Users/a12/Downloads/Toffee_LTX2_Sample"

# 테스트용 이미지 경로 (다운로드 폴더의 주모 사진 사용)
START_IMG = "/Users/a12/Downloads/Script_Scenes_Dynamic/Jumo_Idol_Joseon_02.png"
END_IMG = "/Users/a12/Downloads/Script_Scenes_Dynamic/Jumo_Idol_Joseon_03.png"

def generate_ltx2_stitch():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        print(f"📁 결과 폴더 생성됨: {OUTPUT_DIR}")
    
    print(f"🚀 [LTX-2] 허깅페이스 스페이스 연결 중... ({SPACE_ID})")
    try:
        client = Client(SPACE_ID, token=HF_TOKEN)
    except Exception as e:
        print(f"❌ 연결 실패: {e}")
        return
    
    # 두 번째 장면의 움직임을 위한 프롬프트 수정
    prompt = "The woman in Hanbok is smiling broadly while slightly tilting her head, natural lighting, high quality, cinematic."
    
    print(f"🎬 LTX-2 비디오 생성 시작 (두 번째 구간: 02 ➡️ 03)...")
    print(f"   - 시작 이미지: {os.path.basename(START_IMG)}")
    print(f"   - 끝 이미지: {os.path.basename(END_IMG)}")
    
    try:
        # API 검사 결과에 따른 파라미터 구성
        # predict(start_frame, prompt, end_frame_upload, end_frame_generated, strength_start, strength_end, duration, enhance_prompt, negative_prompt, seed, randomize_seed, num_inference_steps, cfg_guidance_scale, height, width, api_name="/generate_video")
        result = client.predict(
            start_frame=handle_file(START_IMG),
            prompt=prompt,
            end_frame_upload=handle_file(END_IMG),
            end_frame_generated=None,
            strength_start=1.0,
            strength_end=0.9,
            duration=5.0,
            enhance_prompt=True,
            negative_prompt="shaky, glitchy, low quality, worst quality, deformed, distorted, disfigured, motion smear, motion artifacts, fused fingers, bad anatomy, weird hand, ugly, transition, static",
            seed=42,
            randomize_seed=True,
            num_inference_steps=20,
            cfg_guidance_scale=3.0,
            height=512,
            width=768,
            api_name="/generate_video"
        )
        
        # 결과 구조: (generated_video, final_prompt_used, seed)
        video_temp_path, final_prompt, seed = result
            
        timestamp = int(time.time())
        final_filename = f"LTX2_Jumo_Stitch_{int(seed)}.mp4"
        final_path = os.path.join(OUTPUT_DIR, final_filename)
        
        shutil.move(video_temp_path, final_path)
        print(f"✅ 생성 성공! 파일 위치: {final_path}")
        print(f"📝 사용된 최종 프롬프트: {final_prompt}")
        return final_path
        
    except Exception as e:
        print(f"❌ 생성 도중 오류 발생: {e}")
        return None

if __name__ == "__main__":
    generate_ltx2_stitch()

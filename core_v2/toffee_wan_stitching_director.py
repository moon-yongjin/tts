import os
import time
import json
import shutil
from pathlib import Path
from gradio_client import Client, handle_file

# [설정] Wan 2.1 Hugging Face Space 정보
# r3gm/wan2-2-fp8da-aoti-preview: 보간(Interpolation) 기능이 있는 테스트용 스페이스
SPACE_ID = "r3gm/wan2-2-fp8da-aoti-preview"
OUTPUT_DIR = Path.home() / "Downloads" / "Toffee_Wan_Stitching"

def generate_interpolation_segment(start_img, end_img, prompt, index):
    """
    두 이미지 사이를 Wan 2.1로 이어붙여(보간) 영상을 생성합니다.
    """
    print(f"🎬 [Wan Stitching] 장면 {index+1} 생성 중: {os.path.basename(start_img)} ➡️ {os.path.basename(end_img)}")
    
    try:
        client = Client(SPACE_ID)
        
        # Wan 2.1 보간 API 호출
        # predict(input_image, last_image, prompt, steps, negative_prompt, duration_seconds, ...)
        result = client.predict(
            input_image=handle_file(str(start_img)),
            last_image=handle_file(str(end_img)),
            prompt=prompt,
            steps=6,
            negative_prompt="low quality, distorted, static, text, watermark",
            duration_seconds=3.5,
            guidance_scale=1,
            guidance_scale_2=1,
            seed=-1, # 랜덤 시드
            randomize_seed=True,
            quality=6,
            scheduler="UniPCMultistep",
            flow_shift=3.0,
            frame_multiplier=16,
            video_component=True,
            api_name="/generate_video"
        )
        
        # 결과물: (video_info, temp_download_path, seed)
        _, temp_path, seed = result
        
        filename = f"stitch_{index+1:03d}_{int(seed)}.mp4"
        final_path = OUTPUT_DIR / filename
        
        shutil.move(temp_path, final_path)
        print(f"✅ 장면 {index+1} 완료: {filename}")
        return str(final_path)

    except Exception as e:
        print(f"❌ 장면 {index+1} 생성 실패: {e}")
        return None

def run_multi_stitching(image_folder, global_prompt):
    """
    폴더 내의 이미지들을 순서대로 가져와서 사이사이를 영상으로 이어붙입니다.
    """
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    
    # 이미지 정렬해서 가져오기
    images = sorted([os.path.join(image_folder, f) for f in os.listdir(image_folder) if f.endswith(".png")])
    
    if len(images) < 2:
        print("❌ 이어붙이기를 하려면 최소 2장 이상의 이미지가 필요합니다.")
        return

    print(f"🚀 [Toffee Wan Director] 총 {len(images)-1}개의 연결 구간(Stitching) 생성을 시작합니다.")
    start_time = time.time()
    
    generated_clips = []
    
    # 이미지 쌍(Pair)으로 반복문 실행 (1-2, 2-3, 3-4...)
    for i in range(len(images) - 1):
        clip_path = generate_interpolation_segment(images[i], images[i+1], global_prompt, i)
        if clip_path:
            generated_clips.append(clip_path)
        
        # API 부하 조절을 위한 짧은 대기
        time.sleep(1)

    elapsed = time.time() - start_time
    print(f"\n✨ 전체 작업 완료! 생성된 클립: {len(generated_clips)}개")
    print(f"⏱️ 총 소요 시간: {elapsed/60:.1f}분")
    print(f"📂 저장 위치: {OUTPUT_DIR}")
    
    # 나중에 하나로 합치기 편하도록 리스트 파일 생성
    list_path = OUTPUT_DIR / "concat_list.txt"
    with open(list_path, "w", encoding="utf-8") as f:
        for clip in generated_clips:
            f.write(f"file '{os.path.abspath(clip)}'\n")
    print(f"📜 병합용 리스트 생성됨: {list_path}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--folder", type=str, required=True, help="이미지가 들어있는 폴더 경로")
    parser.add_argument("--prompt", type=str, default="Natural cinematic transition, smooth movement, high quality.", help="영상 생성 프롬프트")
    args = parser.parse_args()

    run_multi_stitching(args.folder, args.prompt)

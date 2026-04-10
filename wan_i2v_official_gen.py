import os
import time
from gradio_client import Client, handle_file

# Configuration
SPACE_ID = "Wan-AI/Wan2.1"
OUTPUT_DIR = "Wan_I2V_Outputs"
IMAGE_PATH = "/Users/a12/Downloads/Angry_Villain_Vertical.png"

def generate_wan_i2v():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        print(f"📁 Created output directory: {OUTPUT_DIR}")

    print(f"🚀 Connecting to Official Wan 2.1 Space: {SPACE_ID} with PRO Token...")
    try:
        # User's PRO token for priority access
        client = Client(SPACE_ID, token="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")
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return

    # Prompt with Korean instruction as requested
    prompt = "The arrogant CEO is shouting and venting his anger. 입을 크게 벌리고 말하는 모습, 생생한 표정 변화, cinematic lighting, ultra high quality."
    
    print(f"🎬 Starting I2V generation (Single Image Mode)...")
    print(f"🖼️ Source: {os.path.basename(IMAGE_PATH)}")

    try:
        # Start async generation
        # predict(prompt, image, watermark_wan, seed, api_name="/i2v_generation_async")
        print("📨 Submitting task to queue...")
        resp = client.predict(
            prompt=prompt,
            image=handle_file(IMAGE_PATH),
            watermark_wan=False,
            seed=-1,
            api_name="/i2v_generation_async"
        )
        print(f"📡 Task submitted! Estimated wait: {resp[1]}s")

        # Polling for status
        print("⏳ Polling for results...")
        max_attempts = 100
        for i in range(max_attempts):
            # predict(api_name="/status_refresh") -> (generated_video_dict, cost, wait, progress)
            status = client.predict(api_name="/status_refresh")
            video_info = status[0]
            progress = status[3]
            
            if video_info and 'video' in video_info:
                video_url = video_info['video']
                timestamp = int(time.time())
                final_filename = f"wan_i2v_single_{timestamp}.mp4"
                final_path = os.path.join(OUTPUT_DIR, final_filename)
                
                import shutil
                shutil.move(video_url, final_path)
                shutil.copy(final_path, os.path.join("/Users/a12/Downloads", final_filename))
                
                print(f"✅ Success! Video saved to: {final_path}")
                print(f"📍 Also copied to Downloads as: {final_filename}")
                return final_path
            
            print(f"🔄 Progress: {progress}% (Attempt {i+1}/{max_attempts})")
            time.sleep(5) # Wait between polls
            
        print("❌ Timeout reached without video completion.")

    except Exception as e:
        print(f"❌ Generation failed: {e}")
        return None

if __name__ == "__main__":
    generate_wan_i2v()

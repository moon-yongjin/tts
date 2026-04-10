import os
from gradio_client import Client, handle_file

# Configuration
SPACE_ID = "r3gm/wan2-2-fp8da-aoti-preview"
OUTPUT_DIR = "Wan_Interpolation_Outputs"
# HF_TOKEN = "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" # Using available token from previous script if needed, but space might be public

# Paths
start_image = "/Users/a12/Downloads/Angry_Villain_Vertical.png"
end_image = "/Users/a12/Downloads/Villain_Shocked_Last_Image.png"

def generate_wan_video():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        print(f"📁 Created output directory: {OUTPUT_DIR}")

    print(f"🚀 Connecting to Wan 2.1 Space: {SPACE_ID}...")
    try:
        client = Client(SPACE_ID)
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return

    # User requested: "입모양은 혹시 모르니 한글로 적어봐"
    # We'll combine English and Korean for the best result
    prompt = "The villain's expression changes dramatically from arrogant anger to pure shock and disbelief. 입을 크게 벌리고 말하는 모습, 표정이 실시간으로 변하는 고화질 영상, cinematic lighting, high quality."
    
    print(f"🎬 Generating interpolation video (Wan 2.1)...")
    print(f"⬅️ Start: {os.path.basename(start_image)}")
    print(f"➡️ End: {os.path.basename(end_image)}")

    try:
        # predict(input_image, last_image, prompt, steps, negative_prompt, duration_seconds, ...)
        result = client.predict(
            input_image=handle_file(start_image),
            last_image=handle_file(end_image),
            prompt=prompt,
            steps=6,
            negative_prompt="low quality, distorted, static, text, watermark",
            duration_seconds=3.5,
            guidance_scale=1,
            guidance_scale_2=1,
            seed=42,
            randomize_seed=True,
            quality=6,
            scheduler="UniPCMultistep",
            flow_shift=3.0,
            frame_multiplier=16,
            video_component=True,
            api_name="/generate_video"
        )
        
        # Result structure: (generated_video_dict, download_video_path, seed)
        video_info, download_path, seed = result
        
        final_filename = f"wan_interpolation_{int(seed)}.mp4"
        final_path = os.path.join(OUTPUT_DIR, final_filename)
        
        import shutil
        shutil.move(download_path, final_path)
        
        # Also copy to Downloads for easy access
        shutil.copy(final_path, os.path.join("/Users/a12/Downloads", final_filename))
        
        print(f"✅ Success! Wan interpolation video saved to: {final_path}")
        print(f"📍 Also copied to Downloads for you.")
        return final_path

    except Exception as e:
        print(f"❌ Generation failed: {e}")
        return None

if __name__ == "__main__":
    generate_wan_video()

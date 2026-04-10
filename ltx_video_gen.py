import os
import sys
import argparse
from gradio_client import Client

# Configuration
HF_TOKEN = "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"
SPACE_ID = "Lightricks/ltx-video-distilled"
OUTPUT_DIR = "LTX_Outputs"

def generate_video(prompt, negative_prompt=None, duration=2, width=704, height=512, seed=-1):
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        print(f"📁 Created output directory: {OUTPUT_DIR}")

    print(f"🚀 Connecting to Hugging Face Space: {SPACE_ID}...")
    try:
        client = Client(SPACE_ID, token=HF_TOKEN)
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return None

    if negative_prompt is None:
        negative_prompt = "worst quality, inconsistent motion, blurry, jittery, distorted"

    is_random_seed = True if seed == -1 else False
    target_seed = 42 if seed == -1 else seed

    print(f"🎬 Generating video for prompt: '{prompt}'")
    print(f"⚙️ Settings: {width}x{height}, Duration: {duration}s, Seed: {'Random' if is_random_seed else target_seed}")

    try:
        # Based on API inspection:
        # predict(prompt, negative_prompt, input_image_filepath, input_video_filepath, height_ui, width_ui, mode, duration_ui, ui_frames_to_use, seed_ui, randomize_seed, ui_guidance_scale, improve_texture_flag, api_name="/text_to_video")
        result = client.predict(
            prompt,               # prompt
            negative_prompt,      # negative_prompt
            None,                 # input_image_filepath (Textbox)
            None,                 # input_video_filepath (Textbox)
            height,               # height_ui
            width,                # width_ui
            "text-to-video",      # mode
            duration,             # duration_ui
            9,                    # ui_frames_to_use (default for distilled)
            target_seed,          # seed_ui
            is_random_seed,       # randomize_seed
            1.0,                  # ui_guidance_scale
            True,                 # improve_texture_flag
            api_name="/text_to_video"
        )
        
        # result is (generated_video_dict, seed)
        video_data, final_seed = result
        video_path = video_data['video']
        
        # Move to output directory
        filename = f"ltx_{final_seed}.mp4"
        final_path = os.path.join(OUTPUT_DIR, filename)
        
        import shutil
        shutil.move(video_path, final_path)
        
        print(f"✅ Success! Video saved to: {final_path}")
        return final_path

    except Exception as e:
        print(f"❌ Generation failed: {e}")
        return None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="LTX-Video HF API Generator")
    parser.add_argument("prompt", type=str, help="Text prompt for video generation")
    parser.add_argument("--duration", type=float, default=2.0, help="Duration in seconds")
    parser.add_argument("--width", type=int, default=704)
    parser.add_argument("--height", type=int, default=512)
    parser.add_argument("--seed", type=int, default=-1)

    args = parser.parse_args()
    generate_video(args.prompt, duration=args.duration, width=args.width, height=args.height, seed=args.seed)

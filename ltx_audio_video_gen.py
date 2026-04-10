import os
import sys
import argparse
from gradio_client import Client, handle_file

# Configuration
HF_TOKEN = "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"
SPACE_ID = "multimodalart/ltx2-audio-to-video"
OUTPUT_DIR = "LTX_Audio_Outputs"

def generate_audio_video(image_path, audio_path, prompt=None, negative_prompt=None, duration=None, seed=-1):
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        print(f"📁 Created output directory: {OUTPUT_DIR}")

    if not os.path.exists(image_path):
        print(f"❌ Image not found: {image_path}")
        return None
    if not os.path.exists(audio_path):
        print(f"❌ Audio not found: {audio_path}")
        return None

    print(f"🚀 Connecting to Hugging Face Space: {SPACE_ID}...")
    try:
        client = Client(SPACE_ID, token=HF_TOKEN)
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return None

    # Get audio duration if not provided
    if duration is None:
        try:
            duration_resp = client.predict(handle_file(audio_path), api_name="/get_audio_duration")
            if isinstance(duration_resp, dict) and 'value' in duration_resp:
                duration = float(duration_resp['value'])
            else:
                duration = float(duration_resp)
            # Clamp duration to API limits (1.0 - 12.0)
            duration = max(1.0, min(12.0, duration))
            print(f"⏱️ Audio duration detected and parsed: {duration}s")
        except Exception as e:
            print(f"⚠️ Could not detect duration accurately, defaulting to 4.0s. Error: {e}")
            duration = 4.0
    else:
        print(f"⏱️ Using manual duration: {duration}s")

    if prompt is None or prompt.strip() == "":
        # Even more minimal prompt to prevent the model from 'hallucinating' a new person
        prompt = "lips moving in sync with audio, consistent face, talking head"
    
    if negative_prompt is None or negative_prompt.strip() == "":
        negative_prompt = "low quality, worst quality, deformed, distorted, changing person, different face"

    print(f"🎬 Generating lip-synced video...")
    print(f"🖼️ Image: {os.path.basename(image_path)}")
    print(f"🎵 Audio: {os.path.basename(audio_path)}")

    try:
        # predict(image_path, audio_path, prompt, negative_prompt, video_duration, seed, api_name="/generate")
        result = client.predict(
            handle_file(image_path), # image_path
            handle_file(audio_path), # audio_path
            prompt,                  # prompt
            negative_prompt,         # negative_prompt
            duration,                # video_duration
            seed,                    # seed
            api_name="/generate"
        )
        
        # result is (video_filepath, used_seed)
        generated_video_path, used_seed = result
        
        # Move to output directory
        filename = f"ltx_audio_{int(used_seed)}.mp4"
        final_path = os.path.join(OUTPUT_DIR, filename)
        
        import shutil
        shutil.move(generated_video_path, final_path)
        
        print(f"✅ Success! Audio-synced video saved to: {final_path}")
        return final_path

    except Exception as e:
        print(f"❌ Generation failed: {e}")
        return None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="LTX2 Audio-to-Video API Generator")
    parser.add_argument("--image", type=str, required=True, help="Path to input image")
    parser.add_argument("--audio", type=str, required=True, help="Path to input audio")
    parser.add_argument("--prompt", type=str, help="Optional text prompt")
    parser.add_argument("--duration", type=float, help="Manual duration in seconds")
    parser.add_argument("--seed", type=int, default=-1, help="Random seed")

    args = parser.parse_args()
    generate_audio_video(args.image, args.audio, prompt=args.prompt, duration=args.duration, seed=args.seed)

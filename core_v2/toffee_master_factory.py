import os
import sys
import json
import time
import datetime
import subprocess
from pathlib import Path

# Paths
ENGINE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJ_ROOT = os.path.dirname(ENGINE_DIR)
DOWNLOADS_DIR = os.path.join(os.path.expanduser("~"), "Downloads")

def run_command(command):
    print(f"🏃 Running: {' '.join(command)}")
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ Error: {result.stderr}")
        return False
    print(result.stdout)
    return True

def start_toffee_workflow(script_path):
    print(f"🎬 [Toffee Master Factory] Starting Silent Shorts Workflow")
    timestamp = datetime.datetime.now().strftime("%m%d_%H%M")
    base_name = Path(script_path).stem
    
    # 1. Image Generation (Visual Director)
    # Output to a unique folder in Downloads
    image_out_dir = os.path.join(DOWNLOADS_DIR, f"toffee_{base_name}_{timestamp}")
    os.makedirs(image_out_dir, exist_ok=True)
    
    # Run toffee_visual_director
    visual_cmd = [
        sys.executable, 
        os.path.join(ENGINE_DIR, "toffee_visual_director.py"),
        "--script", script_path,
        "--output", image_out_dir
    ]
    
    if not run_command(visual_cmd):
        print("❌ Visual generation failed.")
        return

    # 2. Skip TTS (Silence is the goal)
    print("🔇 [Step 2] Skipping TTS (ToffeeTime Style - Silent)")

    # 3. Create dummy sequence metadata for video director
    # Most video directors in this codebase expect a JSON with scenes and image paths
    # We should generate a basic sequence.json that core components can use
    sequence_path = os.path.join(image_out_dir, "sequence.json")
    scenes = []
    image_files = sorted([f for f in os.listdir(image_out_dir) if f.endswith(".png")])
    
    for img in image_files:
        scenes.append({
            "image_path": os.path.join(image_out_dir, img),
            "duration": 4.0, # Default 4s per scene for slow cinematic feel
            "caption": "" # No captions for now, or could parse from script
        })
    
    with open(sequence_path, "w", encoding="utf-8") as f:
        json.dump({"scenes": scenes}, f, indent=4)

    # 4. Background Music (BGM)
    # We can use the existing bgm_master or a similar logic
    # For now, we'll notify that we are ready for the next step or try to call bgm_master
    print(f"🎵 [Step 4] Images generated at: {image_out_dir}")
    print(f"📜 [Step 4] Sequence metadata: {sequence_path}")

    # 5. Final Assembly (Motion & Rendering)
    # This usually involves video_director + master_render
    # Since visual direction is done, we could potentially call the video director here
    video_dir_cmd = [
        sys.executable,
        os.path.join(ENGINE_DIR, "03_video_director_v2.py"),
        "--sequence", sequence_path,
        "--output_dir", image_out_dir
    ]
    # Note: Whether to auto-run this depends on if 03_video_director_v2.py supports these flags
    # Many scripts here use hardcoded inputs, so we might need to customize a bit more later.
    
    print(f"✨ Toffee workflow preparation complete.")
    print(f"👉 Generated images are in: {image_out_dir}")
    print(f"👉 To finalize motion, run: python core_v2/03_video_director_v2.py --sequence {sequence_path}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python toffee_master_factory.py <script_text_or_json>")
        sys.exit(1)
    
    script = sys.argv[1]
    start_toffee_workflow(script)

#!/bin/bash
cd "$(dirname "$0")"
source $(conda info --base)/etc/profile.d/conda.sh
conda activate comfy_local

echo "🎵 LTX2 Audio-to-Video (Lip-Sync)"
echo "Available internal files (samples):"
ls reference.png current_narration.mp3 2>/dev/null

read -p "Enter Image path (default reference.png): " IMAGE
IMAGE=${IMAGE:-reference.png}

read -p "Enter Audio path (default current_narration.mp3): " AUDIO
AUDIO=${AUDIO:-current_narration.mp3}

read -p "Enter Prompt (Leave EMPTY for Identity Preservation): " PROMPT

python ltx_audio_video_gen.py --image "$IMAGE" --audio "$AUDIO" --prompt "$PROMPT"

echo "✅ Generation attempt finished. Press any key to close."
read -n 1

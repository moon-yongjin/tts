#!/bin/bash
cd "$(dirname "$0")"
source $(conda info --base)/etc/profile.d/conda.sh
conda activate comfy_local

echo "🎥 LTX-Video Text-to-Video Generation"
read -p "Enter your prompt: " PROMPT
read -p "Duration (default 2s): " DURATION
DURATION=${DURATION:-2}

python ltx_video_gen.py "$PROMPT" --duration $DURATION

echo "✅ Generation attempt finished. Press any key to close."
read -n 1

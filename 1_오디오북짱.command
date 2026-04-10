#!/bin/bash
# Move to the project directory
cd "/Users/a12/projects/tts"

# Execute using the dedicated MLX virtual environment
"/Users/a12/projects/tts/qwen3-tts-apple-silicon/.venv/bin/python3" "/Users/a12/projects/tts/1-3-100_AutoRun_NewShot.py"

# Keep the terminal open to see results
echo ""
echo "Press any key to close this window..."
read -n 1 -s

#!/bin/bash
# comfy_entrypoint.sh - Original Launch Script
echo "===================================================="
echo "   🚀 Starting RunPod Custom ComfyUI Environment"
echo "===================================================="

# Launch ComfyUI directly from the pre-configured workspace
cd /workspace/ComfyUI || exit 1
echo "🌟 Launching ComfyUI on port 8188..."
python3 main.py --listen 0.0.0.0

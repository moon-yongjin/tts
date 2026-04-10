#!/bin/bash
# comfy_entrypoint_v3.2.sh - Optimized Launch Script
echo "===================================================="
echo "   🚀 Starting RunPod Custom ComfyUI (V3.2 Optimized)"
echo "   🔥 Models & Nodes are pre-installed for instant boot."
echo "===================================================="

# Navigate to workspace
cd /workspace/ComfyUI || exit 1

# Check for updates (Optional, but keeping for flexibility)
# git pull

echo "🌟 Launching ComfyUI on port 8188..."
# Added --highvram for 4090/5090 performance
python3 main.py --listen 0.0.0.0 --port 8188 --highvram

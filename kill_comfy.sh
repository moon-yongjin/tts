#!/bin/bash
ssh -o StrictHostKeyChecking=no -i ~/.ssh/id_ed25519_runpod -p 19090 root@213.173.109.153 "kill -9 \$(lsof -t -i:8188) 2>/dev/null; pkill -9 -f python; sleep 2; cd /workspace/ComfyUI; nohup python main.py --listen 127.0.0.1 > comfy_internal.log 2>&1 &"
echo "✅ 런팟 서버 강제 재시작 명령어 전송 완료!"

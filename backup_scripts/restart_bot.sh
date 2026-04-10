#!/bin/bash
PROJECT_DIR="/Users/a12/projects/tts"
BOT_SCRIPT="$PROJECT_DIR/ai_factory_bot.py"
PYTHON="/Users/a12/miniforge3/bin/python"

echo "Stopping any existing bot instances..."
pkill -9 -f ai_factory_bot.py
sleep 2

echo "Creating bridge directory..."
mkdir -p "$PROJECT_DIR/bridge"
rm -f "$PROJECT_DIR/bridge/request.json"

echo "Starting the bot..."
nohup $PYTHON "$BOT_SCRIPT" > "$PROJECT_DIR/bot.log" 2>&1 &

sleep 2
if pgrep -f ai_factory_bot.py > /dev/null; then
    echo "✅ Bot started successfully!"
    tail -n 5 "$PROJECT_DIR/bot.log"
else
    echo "❌ Bot failed to start. Check bot.log"
    cat "$PROJECT_DIR/bot.log"
fi

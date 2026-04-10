#!/bin/zsh

# ----------------------------------------------------------------
# 나노바나나 이미지 순서 정렬 자동화 커맨드
# ----------------------------------------------------------------

PROMPT_FILE="/Users/a12/projects/tts/final_story_prompts.txt"
INPUT_DIR="/Users/a12/Downloads/NB2_output"
OUTPUT_DIR="/Users/a12/Downloads/NB2_Ordered"
SCRIPT_PATH="/Users/a12/projects/tts/reorder_tool/reorder_images_by_prompt.py"

echo "🚀 이미지 정렬 작업을 시작합니다..."
echo "📂 원본 폴더: $INPUT_DIR"
echo "📂 결과 폴더: $OUTPUT_DIR"

# 기존 결과 폴더 초기화 (선택 사항)
# rm -rf "$OUTPUT_DIR" && mkdir -p "$OUTPUT_DIR"

python3 "$SCRIPT_PATH" "$PROMPT_FILE" "$INPUT_DIR" "$OUTPUT_DIR"

echo "✅ 정렬이 완료되었습니다. $OUTPUT_DIR 폴더를 확인하세요!"

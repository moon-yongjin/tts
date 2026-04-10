import json
from pathlib import Path

json_path = Path("/Users/a12/Downloads/extracted_assets/test_story_04/04_Diarized_Result_Pre_Shorts.json")
with open(json_path, "r", encoding="utf-8") as f:
    segments = json.load(f)

# 유저가 남겨둔 타임스탬프들
target_starts = [249.82, 258.86, 263.94, 267.34, 271.04, 277.54, 289.02, 292.58, 300.00, 307.70, 314.38, 319.22, 321.58, 324.72, 548.36, 556.58, 563.46, 566.26]

print("🔍 분석 중인 세그먼트 상세:")
for ts in target_starts:
    for s in segments:
        if abs(s["start"] - ts) < 0.1:
            dur = s["end"] - s["start"]
            print(f"[{s['start']:.2f}s - {s['end']:.2f}s (길이: {dur:.2f}s)] {s.get('speaker', '?')}: {s['text']}")

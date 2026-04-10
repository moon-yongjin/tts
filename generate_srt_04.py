import json
import re
from pathlib import Path

def format_srt_time(seconds):
    ms = int((seconds - int(seconds)) * 1000)
    s = int(seconds)
    m = s // 60
    h = m // 60
    return f"{h:02d}:{m%60:02d}:{s%60:02d},{ms:03d}"

def generate_srt():
    trans_path = Path("/Users/a12/Downloads/extracted_assets/test_story_04_pinpoint/04_Pinpoint_Visual_Hardship_Transcript.txt")
    json_path = Path("/Users/a12/Downloads/extracted_assets/test_story_04/04_Diarized_Result_Pre_Shorts.json")
    out_srt = Path("/Users/a12/Downloads/extracted_assets/test_story_04_pinpoint/04_Pinpoint_Visual_Hardship_Remix.srt")
    
    segments = []
    if json_path.exists():
        with open(json_path, "r", encoding="utf-8") as f:
            segments = json.load(f)
    else:
        print("⚠️ JSON 파일을 찾을 수 없어 기본 길이(3.5초)를 사용합니다.")
    
    with open(trans_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    current_time = 0.0
    srt_output = []
    counter = 1
    
    for line in lines:
        match = re.search(r"\[(\d+\.?\d*)s\]", line)
        if match:
            start_orig = float(match.group(1))
            text = re.sub(r"\[\d+\.?\d*s\]", "", line).strip()
            
            # Find matching segment in JSON to get duration
            duration = 3.5 # Fallback (평균적인 문장 길이)
            for s in segments:
                if abs(s.get("start", 0) - start_orig) < 0.1:
                    duration = s.get("end", 0) - s.get("start", 0)
                    break
            
            end_time = current_time + duration
            
            srt_output.append(f"{counter}")
            srt_output.append(f"{format_srt_time(current_time)} --> {format_srt_time(end_time)}")
            srt_output.append(text)
            srt_output.append("")
            
            # Update current_time for next subtitle (including 200ms silence gap)
            current_time = end_time + 0.2
            counter += 1
            
    with open(out_srt, "w", encoding="utf-8") as f:
        f.write("\n".join(srt_output))
    
    print(f"✅ SRT 생성 완료: {out_srt}")

if __name__ == "__main__":
    generate_srt()

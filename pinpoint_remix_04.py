import os
import json
import subprocess
from pathlib import Path
from pydub import AudioSegment

def pinpoint_manual_remix(diarized_json, video_source, output_dir):
    with open(diarized_json, "r", encoding="utf-8") as f:
        segments = json.load(f)

    # 유저가 명시적으로 준 고난/희생 중심의 타임라인
    # [249s - 327s] 학교 진학 상담, 서면 보호자 역할, 엄마 보호
    # [548s - 663s] 환경적 요인으로 인한 결혼 포기 및 변화
    # [735s - 742s] 언니를 향한 동생의 간절한 소망 (그늘이 없어졌으면)
    
    target_ranges = [
        (249.42, 277.54),
        (289.02, 307.70),
        (307.70, 327.22),
        (548.36, 620.56),
        (624.04, 663.76),
        (735.56, 742.24)
    ]

    selected_segments = []
    for start, end in target_ranges:
        for s in segments:
            # 타임스탬프가 겹치는 사연자(주인공)의 목소리만 수집
            if s["start"] >= start - 1.0 and s["end"] <= end + 1.0 and s.get("speaker") == "사연자":
                # 중복 방지
                if not any(item["id"] == s["id"] for item in selected_segments):
                    selected_segments.append(s)

    if not selected_segments:
        print("❌ 매칭되는 세그먼트를 찾지 못했습니다.")
        return
    
    output_dir.mkdir(parents=True, exist_ok=True)
    out_wav = output_dir / "04_Pinpoint_Visual_Hardship_Remix.wav"
    out_txt = output_dir / "04_Pinpoint_Visual_Hardship_Transcript.txt"

    print(f"🎬 유저 편집 내용 반영 중...")
    
    temp_wav = output_dir / "temp_pinpoint.wav"
    subprocess.run([
        "ffmpeg", "-y", "-i", str(video_source),
        "-vn", "-acodec", "pcm_s16le", "-ar", "44100", "-ac", "2",
        str(temp_wav)
    ], capture_output=True)
    
    full_audio = AudioSegment.from_wav(str(temp_wav))
    combined = AudioSegment.empty()
    
    # 텍스트 파일 읽기 (유저가 수정한 상태)
    txt_path = Path("/Users/a12/Downloads/extracted_assets/test_story_04_pinpoint/04_Pinpoint_Visual_Hardship_Transcript.txt")
    with open(txt_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    with open(out_txt, "w", encoding="utf-8") as f:
        f.write("=== [유저 최종 편집] 시각적 고난 중심 정밀 리믹스 ===\n\n")
        for line in lines:
            import re
            match = re.search(r"\[(\d+\.?\d*)s\]", line)
            if match:
                start_sec = float(match.group(1))
                
                # 내용이 없는 경우 스킵
                content = re.sub(r"\[\d+\.?\d*s\]", "", line).strip()
                if not re.search(r"[가-힣a-zA-Z0-9]", content):
                    print(f"⏩ 스킵: {line.strip()}")
                    continue

                # JSON에서 정확한 end 시간 매칭
                end_sec = None
                for s in segments:
                    if abs(s["start"] - start_sec) < 0.1:
                        end_sec = s["end"]
                        break
                
                if end_sec:
                    start_ms = int(start_sec * 1000)
                    end_ms = int(end_sec * 1000)
                    chunk = full_audio[start_ms:end_ms]
                    
                    if len(combined) > 0:
                        combined = combined.append(chunk, crossfade=100)
                    else:
                        combined = chunk
                    
                    combined += AudioSegment.silent(duration=200)
                    f.write(line)

    combined.export(str(out_wav), format="wav")
    if temp_wav.exists(): os.remove(temp_wav)
    
    print(f"✅ 리믹스 오디오: {out_wav.name}")
    print(f"✅ 리믹스 대본: {out_txt.name}")

if __name__ == "__main__":
    diarized_json = Path("/Users/a12/Downloads/extracted_assets/test_story_04/04_Diarized_Result_Pre_Shorts.json")
    video_source = Path("/Users/a12/Downloads/100분_눈물_콧물_주의_슬픈_사연_모음_책임감이라는_단어가_주는_마음의_무게에서_벗어나_나를_먼저_돌아보기_김창옥쇼2_clips/04_치매_시어머니를_모시며_앞집_아저씨처럼_느껴지는_남편.mp4")
    output_dir = Path("/Users/a12/Downloads/extracted_assets/test_story_04_pinpoint")
    
    pinpoint_manual_remix(diarized_json, video_source, output_dir)

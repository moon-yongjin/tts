import os
import subprocess
import re
from pathlib import Path

# [설정] 정확히 확인된 경로 사용
FULL_VIDEO = Path("/Users/a12/Downloads/100분_눈물_콧물_주의_슬픈_사연_모음_책임감이라는_단어가_주는_마음의_무게에서_벗어나_나를_먼저_돌아보기_김창옥쇼2_clips/05_8년_만에_찾아온_이별_위기_80세에_후회할까_두려운_.mp4")
OUTPUT_DIR = Path("/Users/a12/Downloads/extracted_assets/curated_story_v12")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

CURATED_TEXT = """
[509.8s] 사연자:  아니고 이제 그냥
[511.8s] 사연자:  사실혼 관계처럼 지내고 있었는데
[514.8s] 사연자:  이제 임신 기간 때까지는 괜찮았는데
[516.8s] 사연자:  이제 아기를 낳고
[518.8s] 사연자:  얼마 안 돼서 제가 헤어짐을 통보를 받은 거예요
[525.8s] 사연자:  이제 자기가 부담이 된다고
[537.8s] 사연자:  아이를 낳고
[545.8s] 사연자:  근데
[546.8s] 사연자:  그때 남편이
[547.8s] 사연자:  아기를 입양 보내라고
[549.8s] 사연자:  입양 보내라고
[550.8s] 사연자:  해서
[555.8s] 사연자:  아기랑 이미
[556.8s] 사연자:  정이 붙어버리는 상황이었거든요
[557.8s] 사연자:  제가 이제
[558.8s] 사연자:  열 달 동안
[560.8s] 사연자:  키우고 있었기도 했고
[561.8s] 사연자:  이제
[562.8s] 사연자:  낳고 나서
[563.8s] 사연자:  이제 아기를 보는데
[565.8s] 사연자:  아기
[567.8s] 사연자:  애기
[664.8s] 사연자:  그래서 바로 이 친구네 집을 갔는데
[667.8s] 사연자:  그때 이 이야기를 처음 들었어요
[670.8s] 사연자:  애기를 혼자 키우게 됐다고
[672.8s] 사연자:  저희 또래에 맞는 이야기가 있잖아요
[676.8s] 사연자:  저는 놀러 다니는데
[678.8s] 사연자:  이 친구는 아무렇지 않게
[679.8s] 사연자:  애기 봐야 한다고 하고
[681.8s] 사연자:  그럴 때 약간
[682.8s] 사연자:  애가 행복했으면 좋겠다
[684.8s] 사연자:  어떤 방식으로든
[686.8s] 사연자:  그런 생각이 좀 많이 들어요
[691.8s] 김창옥:  혹시 아이가 아픈 데가 좀 있다고 하던데
[695.8s] 사연자:  태어났을 때부터
[697.8s] 사연자:  이제 태어났을 때부터
[698.8s] 사연자:  이제 뱃속에 있었을 때부터
[699.8s] 사연자:  선천적으로 신장이 하나예요
[701.8s] 사연자:  단일신장이어서
[703.8s] 사연자:  괜히 약간 제 책임인 것 같아서
[707.8s] 사연자:  제가 볼 잘못 먹어서 그런 건지
[709.8s] 사연자:  볼 잘못 발라서 그런 건지
[711.8s] 사연자:  볼 잘못 발라서 그런 건지
[713.8s] 사연자:  약간 제 탓을 좀 많이 했어요
[715.8s] 사연자:  제 탓도 하고
[717.8s] 사연자:  일단
[719.8s] 사연자:  아픈의 상처가 아이에게 되물림이 될까 봐
[1102.8s] 사연자:  사랑하는 우리 아들 한우리
[1105.8s] 사연자:  엄마가 엄마 아빠가 내게
[1107.8s] 사연자:  엄마 아빠가 내게
[1109.8s] 사연자:  엄마 아빠가 내게
[1111.8s] 사연자:  너에게 많은 상처를
[1198.4s] 사연자:  직장은 안 다니고 있고 아기만 보고 있어요
[1201.6s] 사연자:  아직 어린이집을 안 가서
"""

def format_srt_time(seconds):
    ms = int((seconds - int(seconds)) * 1000)
    s = int(seconds)
    m = s // 60
    h = m // 60
    return f"{h:02d}:{m%60:02d}:{s%60:02d},{ms:03d}"

def run():
    if not FULL_VIDEO.exists():
        print(f"❌ 원본 파일을 찾을 수 없습니다: {FULL_VIDEO}")
        return

    lines = [l.strip() for l in CURATED_TEXT.strip().split("\n") if l.strip()]
    
    tmp_dir = OUTPUT_DIR / "tmp_v12"
    if tmp_dir.exists():
        import shutil
        shutil.rmtree(tmp_dir)
    tmp_dir.mkdir(parents=True)
    
    segment_files = []
    srt_output = []
    current_remix_time = 0.0
    
    print(f"🎬 총 {len(lines)}개 세그먼트 추출 시작...")
    
    for i, line in enumerate(lines):
        match = re.search(r"\[(\d+\.?\d*)s\]", line)
        if not match: continue
        
        start_abs = float(match.group(1))
        # 기본 길이 2.0s로 설정 (대본 구조상 촘촘함)
        duration = 2.0
        if i + 1 < len(lines):
            next_match = re.search(r"\[(\d+\.?\d*)s\]", lines[i+1])
            if next_match:
                diff = float(next_match.group(1)) - start_abs
                if 0 < diff < 5.0:
                    duration = diff
        
        text = re.sub(r"\[\d+\.?\d*s\]", "", line).strip()
        
        # 1. 오디오 세그먼트 추출
        seg_file = tmp_dir / f"seg_{i:03d}.wav"
        cmd = [
            "ffmpeg", "-y", "-ss", str(start_abs), "-t", str(duration),
            "-i", str(FULL_VIDEO), "-vn", "-acodec", "pcm_s16le", "-ar", "44100", "-ac", "2",
            str(seg_file)
        ]
        result = subprocess.run(cmd, capture_output=True)
        if result.returncode == 0:
            segment_files.append(seg_file)
        else:
            print(f"⚠️ 세그먼트 {i} 추출 실패: {result.stderr.decode()}")
            continue
        
        # 2. SRT 구성
        end_remix_time = current_remix_time + duration
        srt_output.append(f"{i+1}")
        srt_output.append(f"{format_srt_time(current_remix_time)} --> {format_srt_time(end_remix_time)}")
        srt_output.append(text)
        srt_output.append("")
        
        current_remix_time = end_remix_time + 0.1 # 문장 사이 아주 살짝 간격
        
    # 3. 전체 세그먼트 합치기
    if not segment_files:
        print("❌ 추출된 세그먼트가 없습니다.")
        return

    list_path = tmp_dir / "list.txt"
    with open(list_path, "w", encoding="utf-8") as f:
        for sf in segment_files:
            f.write(f"file '{sf.name}'\n")
            
    final_audio = OUTPUT_DIR / "Curated_Shorts_Remix.wav"
    concat_cmd = [
        "ffmpeg", "-y", "-f", "concat", "-i", str(list_path),
        "-c:a", "pcm_s16le", str(final_audio)
    ]
    result = subprocess.run(concat_cmd, cwd=str(tmp_dir), capture_output=True)
    
    if result.returncode == 0:
        # 4. SRT 저장
        final_srt = OUTPUT_DIR / "Curated_Shorts_Remix.srt"
        with open(final_srt, "w", encoding="utf-8") as f:
            f.write("\n".join(srt_output))
            
        print(f"✅ 작업 완료!")
        print(f"🎙️ 오디오: {final_audio}")
        print(f"📝 자막: {final_srt}")
        print(f"📊 오디오 크기: {os.path.getsize(final_audio) // 1024} KB")
    else:
        print(f"❌ 최종 합치기 실패: {result.stderr.decode()}")

if __name__ == "__main__":
    run()

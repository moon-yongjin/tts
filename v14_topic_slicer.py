import os
import sys
import json
import re
import subprocess
from pathlib import Path

# 모듈 경로 추가 및 임포트
sys.path.append(str(Path(__file__).parent / "utils" / "youtube" / "lib"))
import video_downloader as vd
import story_analyzer as sa

def get_video_duration(video_path):
    cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(video_path)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    try:
        return float(result.stdout.strip())
    except:
        return 0.0

def hms_to_seconds(t_str):
    parts = list(map(float, t_str.split(':')))
    if len(parts) == 3:
        return parts[0] * 3600 + parts[1] * 60 + parts[2]
    elif len(parts) == 2:
        return parts[0] * 60 + parts[1]
    return 0.0

def slice_by_topic(video_path, ts_desc, output_dir):
    total_dur = get_video_duration(video_path)
    if not ts_desc:
        print("❌ 추출된 목차 타임스탬프가 없습니다. 자막 기반 추출을 시도해야 합니다.")
        return

    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"\n🎬 총 {len(ts_desc)}개의 사연(주제) 단위로 큼직하게 컷팅을 시작합니다...")

    for i in range(len(ts_desc)):
        start_str = ts_desc[i][0]
        st = hms_to_seconds(start_str)
        
        # 마지막 항목이면 끝까지, 아니면 다음 항목 시작 전까지
        if i + 1 < len(ts_desc):
            ed = hms_to_seconds(ts_desc[i+1][0])
        else:
            ed = total_dur
            
        # 제목에서 파일명으로 쓸 수 없는 문자 제거
        clean_title = re.sub(r'[^\w\s-가-힣]', '', ts_desc[i][1]).strip().replace(' ', '_')
        out_file = output_dir / f"Story_{i+1:02d}_{clean_title}.mp4"
        
        print(f"✂️ 자르는 중: [{i+1:02d}] {start_str} ~ ({st}s ~ {ed}s)")
        # -c copy 를 사용하여 인코딩 없이 순식간에 자름. (사연 단위 컷팅이라 1~2초 오차는 문제없음)
        cmd = [
            "ffmpeg", "-y", "-i", str(video_path),
            "-ss", str(st), "-to", str(ed),
            "-c", "copy", str(out_file)
        ]
        subprocess.run(cmd, capture_output=True)

    print(f"\n✅ {len(ts_desc)}개의 사연 덩어리 분할 완료!")
    print(f"📂 결과물 폴더: {output_dir}")
    os.system(f"open '{output_dir}'")

def main():
    print("==========================================")
    print("🚀 [V14] Topic-Based Slicer (사연별 큼직한 분할기)")
    print("==========================================")
    
    inp = ""
    if len(sys.argv) > 1:
        inp = sys.argv[1]
    else:
        inp = input("🔗 유튜브 URL(모음집)을 입력하세요: ").strip()
        
    if not inp: return
    
    downloads_dir = Path.home() / "Downloads"
    
    p_inp = Path(inp)
    is_local = p_inp.exists() and p_inp.suffix.lower() == ".mp4"
    
    ts_desc = []
    
    if is_local:
        full_video_path = p_inp
        title = full_video_path.stem
        safe_title = re.sub(r'[^\w\s-]', '', title).strip().replace(' ', '_')
        print(f"🎬 로컬 파일이 감지되었습니다: {full_video_path.name}")
        
        # 1. 같은 이름의 .txt 파일이 있는지 먼저 확인
        txt_path = full_video_path.with_suffix(".txt")
        if not txt_path.exists():
            print(f"⚠️ 타임스탬프 파일({txt_path.name})이 없습니다.")
            txt_inp = input("🔗 타임스탬프가 적힌 텍스트 파일 경로를 직접 입력하세요: ").strip()
            if txt_inp:
                txt_path = Path(txt_inp)
            else:
                print("❌ 타임스탬프 정보가 없으면 영상을 나눌 수 없습니다.")
                return
        
        if txt_path.exists():
            print(f"🔍 {txt_path.name} 파일에서 타임스탬프를 추출합니다...")
            with open(txt_path, "r", encoding="utf-8") as f:
                content = f.read()
                # 다양한 형식 지원 ([00:00], 00:00 등)
                matches = re.findall(r'(\d{1,2}:\d{2}(?::\d{2})?)[\s\]\)-]+(.*)', content)
                for m_ts, m_desc in matches:
                    ts_desc.append((m_ts, m_desc.strip()))
                    
        if not ts_desc:
            print("⚠️ 텍스트 파일에서 타임스탬프를 찾지 못했습니다. (형식: 00:00 제목)")
            return

    else:
        url = inp
        print("🔍 유튜브 설명란에서 타임스탬프(목차)를 추출합니다...")
        title, ts_desc = vd.get_video_metadata(url)
        if not title: return
        safe_title = re.sub(r'[^\w\s-]', '', title).strip().replace(' ', '_')
        full_video_path = downloads_dir / f"{safe_title}_topic_source.mp4"
        
        if not ts_desc:
            print("⚠️ 설명란에 타임스탬프가 없습니다. 수동 분할이 필요합니다.")
            return
            
        print("\n📥 영상 다운로드 중...")
        if not vd.download_video(url, full_video_path): return
        
    print("\n📍 추출된 타임스탬프:")
    for t, desc in ts_desc:
        print(f"   [{t}] {desc}")
        
    output_dir = downloads_dir / f"Topics_{safe_title}"
    slice_by_topic(full_video_path, ts_desc, output_dir)

if __name__ == "__main__":
    main()

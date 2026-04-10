import os
import sys
import re
import datetime
from pathlib import Path

# --- [유틸리티] ---
def parse_srt_time(time_str):
    """ SRT 타임코드를 초(seconds)로 변환 """
    h, m, s_ms = time_str.split(':')
    s, ms = s_ms.split(',')
    return datetime.timedelta(hours=int(h), minutes=int(m), seconds=int(s), milliseconds=int(ms)).total_seconds()

def format_srt_time(seconds):
    """ 초(seconds)를 SRT 타임코드 문자열로 변환 """
    if seconds < 0: seconds = 0
    td = datetime.timedelta(seconds=seconds)
    total_seconds = int(td.total_seconds())
    return f"{total_seconds//3600:02d}:{(total_seconds%3600)//60:02d}:{total_seconds%60:02d},{int(td.microseconds / 1000):03d}"

def split_text_by_length(text, min_len=8, max_len=12):
    """
    텍스트를 단어(어절) 단위로 쪼갠 후, 
    한 청크가 8~12자 부근이 되도록 병합하여 분할합니다.
    단, 쉼표(,)나 마침표(.) 감지 시 더 짧아도 즉시 분할합니다.
    """
    # 불필요한 연속 공백 제거
    text = re.sub(r'\s+', ' ', text).strip()
    words = text.split(' ')
    chunks = []
    current_chunk = ""

    for word in words:
        if not current_chunk:
            current_chunk = word
        elif len(current_chunk + " " + word) <= max_len:
             current_chunk += " " + word
        else:
            chunks.append(current_chunk)
            current_chunk = word
            
        # 💡 사용자 추가 요청: 쉼표(,)나 마침표(.)로 끝나는 단어라면 즉각 강제 분할
        if word.endswith(',') or word.endswith('.'):
            if current_chunk:
                chunks.append(current_chunk)
                current_chunk = ""
            
    if current_chunk:
        chunks.append(current_chunk)
        
    return [c.strip() for c in chunks if c.strip()]


def process_srt(srt_content, target_len=10):
    """
    SRT 콘텐츠 전체를 파싱하고 문장들을 비례 배분하여 쪼갭니다.
    """
    # SRT 항목 분할 (빈 라인 기준)
    blocks = re.split(r'\n\s*\n', srt_content.strip())
    new_blocks = []
    new_index = 1

    for block in blocks:
        lines = block.strip().splitlines()
        if len(lines) < 3: continue  # 인덱스, 시간, 대사 구조가 아니면 스킵

        index = lines[0]
        timecode = lines[1]
        text_lines = " ".join(lines[2:]) # 3라인 이상일 수 있으므로 통합
        
        # 타임코드 파싱
        match = re.search(r'(\d{2}:\d{2}:\d{2},\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2},\d{3})', timecode)
        if not match: continue

        start_time = parse_srt_time(match.group(1))
        end_time = parse_srt_time(match.group(2))
        duration = end_time - start_time
        
        # 텍스트 청분할 (8~14 캐릭터 유도)
        text_sub_chunks = split_text_by_length(text_lines, min_len=8, max_len=12)
        
        if len(text_sub_chunks) <= 1:
            # 쪼갤 필요가 없는 짧은 대사
            new_blocks.append(f"{new_index}\n{timecode}\n{text_lines}")
            new_index += 1
            continue

        # ⭐️ 타임코드 비례배분 연산
        # 공백 제외 문자수로 비중 계산
        cleaned_text = text_lines.replace(" ", "")
        total_chars = len(cleaned_text) if cleaned_text else 1
        
        current_start = start_time
        
        for i, chunk in enumerate(text_sub_chunks):
            chunk_len = len(chunk.replace(" ", ""))
            # 비례 비율 배분 (최소 0.1초 보장)
            weight = chunk_len / total_chars 
            chunk_duration = max(0.2, duration * weight)
            
            # 마지막 청크는 딱 맞아떨어지게 보정
            if i == len(text_sub_chunks) - 1:
                current_end = end_time
            else:
                current_end = current_start + chunk_duration
                if current_end > end_time: current_end = end_time # 초과 방지
                
            # 💡 사용자 요청: 대본 출력 시 특수문자 전면 제거
            clean_chunk = re.sub(r'[^가-힣a-zA-Z0-9\s]', '', chunk).strip()
            new_blocks.append(
                f"{new_index}\n"
                f"{format_srt_time(current_start)} --> {format_srt_time(current_end)}\n"
                f"{clean_chunk}"
            )
            new_index += 1
            current_start = current_end # 다음 차례 준비

    return "\n\n".join(new_blocks)

def run_main():
    if len(sys.argv) > 1:
        target_srt = Path(sys.argv[1])
        if not target_srt.exists():
            print(f"❌ 파일을 찾을 수 없습니다: {target_srt}")
            return
        base_dir = target_srt.parent
    else:
        base_dir = Path.home() / "Downloads"
        # 가장 최신 SRT 파일 찾기
        srt_files = sorted(list(base_dir.glob("*.srt")), key=os.path.getmtime, reverse=True)
        
        if not srt_files:
            print("❌ Downloads 폴더 내에 처리할 .srt 파일이 없습니다.")
            return
        target_srt = srt_files[0]

    print("\n" + "="*50)
    print(f"🎬 [SRT 자막 분배기] 가동 중")
    print(f"📂 대상 파일: {target_srt.name}")
    print("="*50)

    try:
        # utf-8-sig로 읽기 (BOM 처리)
        with open(target_srt, "r", encoding="utf-8-sig") as f:
            content = f.read()
        
        updated_content = process_srt(content)
        
        output_name = target_srt.stem + "_Split.srt"
        output_path = base_dir / output_name
        
        with open(output_path, "w", encoding="utf-8-sig") as f:
            f.write(updated_content)
            
        print(f"✅ 프리미엄 분배 완료: {output_name}")
        print(f"💡 결과 파일 위치: {output_path}")
        print(f"💡 자막이 약 8-12자 단위로 쪼개져 렌더링을 돕습니다.")
        print("="*50)
    except Exception as e:
        print(f"❌ 에러 발생: {e}")

if __name__ == "__main__":
    run_main()

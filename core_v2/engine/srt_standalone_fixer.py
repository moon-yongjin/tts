import re
import os
import sys

def clean_script_canonical(text):
    """대본에서 SFX 태그 등을 제거하고 실제 발화되어야 할 단어들만 추출"""
    # SFX 및 각종 메타 태그 제거
    text = re.sub(r'\[SFX:.*?\]', ' ', text)
    text = re.sub(r'\[(대사|묘사|지문|설명|SFX|챕터|CHAPTER).*?\]', ' ', text, flags=re.IGNORECASE)
    text = re.sub(r'\(.*?\)', ' ', text)
    # 단어 리스트 반환
    return text.split()

def parse_srt_structure(srt_path):
    """SRT 파일의 시간 구조만 추출 (텍스트는 버림)"""
    if not os.path.exists(srt_path): return []
    with open(srt_path, "r", encoding="utf-8-sig") as f:
        content = f.read().strip()
    
    blocks = re.split(r'\n\s*\n', content)
    structure = []
    for block in blocks:
        lines = block.splitlines()
        if len(lines) >= 2:
            num = lines[0]
            time_range = lines[1]
            # 원본 단어 개수 파악 (비율 배분용)
            original_text = " ".join(lines[2:])
            word_count = len(original_text.split())
            if word_count == 0: word_count = 1 # 최소 1단어 공간 확보
            structure.append({'num': num, 'time': time_range, 'count': word_count})
    return structure

def run_standalone_fix(srt_path, script_path):
    print(f"🛠️  자막 강제 보정 중...")
    print(f"📁 대상 자막: {os.path.basename(srt_path)}")
    print(f"📄 기준 대본: {os.path.basename(script_path)}")

    # 1. 대본 로드 및 단어화
    with open(script_path, "r", encoding="utf-8") as f:
        script_raw = f.read()
    script_words = clean_script_canonical(script_raw)
    
    # 2. SRT 구조 로드
    srt_structure = parse_srt_structure(srt_path)
    if not srt_structure:
        print("❌ 자막 구조를 읽을 수 없습니다.")
        return

    # 3. 텍스트 재배치 (Redistribution)
    # 전체 대본 단어 수와 SRT 블록들의 총 가중치를 계산하여 배분
    total_original_words = sum(s['count'] for s in srt_structure)
    total_script_words = len(script_words)
    
    corrected_srt = []
    current_word_ptr = 0
    
    for i, block in enumerate(srt_structure):
        # 이 블록이 차지하던 비중에 맞춰 대본 단어 수를 할당
        # 마지막 블록은 남은 단어 전부 몰아넣기
        if i == len(srt_structure) - 1:
            assigned_count = total_script_words - current_word_ptr
        else:
            ratio = block['count'] / total_original_words
            assigned_count = round(total_script_words * ratio)
            # 최소 1단어는 할당 (단어가 남아있다면)
            if assigned_count == 0 and current_word_ptr < total_script_words:
                assigned_count = 1
        
        assigned_words = script_words[current_word_ptr : current_word_ptr + assigned_count]
        current_word_ptr += assigned_count
        
        text = " ".join(assigned_words)
        corrected_srt.append(f"{block['num']}\n{block['time']}\n{text}\n\n")

    # 4. 저장
    output_path = srt_path.replace(".srt", "_fixed.srt")
    with open(output_path, "w", encoding="utf-8-sig") as f:
        f.writelines(corrected_srt)
    
    print(f"✨ 보정 완료! 보정된 파일: {os.path.basename(output_path)}")
    print(f"💡 팁: 캡컷에서 {os.path.basename(output_path)} 파일을 불러오세요.")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        # 인자가 없을 경우 Downloads 폴더에서 자동 탐색
        downloads = os.path.join(os.environ['USERPROFILE'], 'Downloads')
        srts = [os.path.join(downloads, f) for f in os.listdir(downloads) if f.endswith(".srt") and "_fixed" not in f]
        if not srts:
            print("❌ 다운로드 폴더에서 자막 파일을 찾을 수 없습니다.")
            sys.exit(1)
        latest_srt = max(srts, key=os.path.getmtime)
        
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        target_script = os.path.join(base_dir, "대본.txt")
        
        run_standalone_fix(latest_srt, target_script)
    else:
        run_standalone_fix(sys.argv[1], sys.argv[2])

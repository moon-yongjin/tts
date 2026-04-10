import re
import os
import sys
import difflib

def normalize(text):
    return re.sub(r'[^a-zA-Z가-힣0-9]', '', str(text)).lower()

def get_clean_script_words(script_path):
    with open(script_path, "r", encoding="utf-8") as f:
        text = f.read()
    
    # [클린 작업] SFX 관련 태그 및 뒤따르는 설명 문구 제거
    # [SFX]: 문구... 형태를 처리하되, 뒤따르는 대사(명숙은, 며느리가 등)를 침범하지 않도록 조절
    text = re.sub(r'\[SFX\]\s*:[^.\[\n]*\.?', ' ', text, flags=re.IGNORECASE)
    text = re.sub(r'\[SFX:.*?\]', ' ', text, flags=re.IGNORECASE)
    
    # [클린 작업] 기타 메타 태그 제거 ([대사], [지문] 등)
    text = re.sub(r'\[(대사|묘사|지문|설명|배경|음악|챕터|CHAPTER).*?\]', ' ', text, flags=re.IGNORECASE)
    text = re.sub(r'\(.*?\)', ' ', text)
    
    # [클린 작업] 말끝 줄임표 및 반복되는 점들 제거
    text = text.replace('...', ' ').replace('..', ' ')
    
    # 단어 리스트 반환 (공백 제거)
    return [w.strip('.,') for w in text.split() if w.strip()]

def parse_srt(srt_path):
    with open(srt_path, "r", encoding="utf-8-sig") as f:
        content = f.read().strip()
    blocks = re.split(r'\n\s*\n', content)
    entries = []
    for block in blocks:
        lines = block.splitlines()
        if len(lines) >= 3:
            entries.append({
                'num': lines[0],
                'time': lines[1],
                'text': " ".join(lines[2:]),
                'words': " ".join(lines[2:]).split()
            })
    return entries

def fix_srt(srt_path, script_path):
    print(f"🎬 자막 누락 보정 작업을 시작합니다...")
    
    script_words = get_clean_script_words(script_path)
    srt_entries = parse_srt(srt_path)
    
    if not script_words or not srt_entries:
        print("❌ 데이터를 읽을 수 없습니다.")
        return

    # 모든 SRT 단어 나열
    srt_all_words = []
    for e in srt_entries:
        srt_all_words.extend(e['words'])
    
    # 정규화 매칭
    script_norm = [normalize(w) for w in script_words]
    srt_norm = [normalize(w) for w in srt_all_words]
    
    sm = difflib.SequenceMatcher(None, script_norm, srt_norm)
    srt_to_script = {}
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag in ('equal', 'replace'):
            for offset in range(min(i2-i1, j2-j1)):
                srt_to_script[j1 + offset] = i1 + offset

    # 보정 및 가시화
    corrected_srt = []
    word_ptr = 0
    last_script_idx = -1
    
    for entry in srt_entries:
        # 이 블록에 매칭된 대본 인덱스들
        indices = [srt_to_script.get(word_ptr + k) for k in range(len(entry['words'])) if (word_ptr + k) in srt_to_script]
        word_ptr += len(entry['words'])
        
        if indices:
            start = min(indices)
            end = max(indices)
            
            # 이전 블록 이후부터 현재 블록 끝까지의 모든 단어를 다 끌어옴 (누락 방지 핵심)
            actual_start = last_script_idx + 1
            actual_end = end
            
            if actual_start <= actual_end:
                final_text = " ".join(script_words[actual_start : actual_end + 1])
                # 특수기호(따옴표, 슬래시 등) 최종 정제
                final_text = re.sub(r'["\'/\\^]', '', final_text)
                last_script_idx = actual_end
            else:
                final_text = entry['text']
        else:
            final_text = entry['text']
            
        corrected_srt.append(f"{entry['num']}\n{entry['time']}\n{final_text}\n\n")
    
    # 마지막 남은 자투리 대본이 있다면 마지막 블록에 추가
    if last_script_idx < len(script_words) - 1:
        extra_text = " ".join(script_words[last_script_idx + 1:])
        corrected_srt[-1] = corrected_srt[-1].strip() + " " + extra_text + "\n\n"

    # 새 파일로 저장
    output_path = srt_path.replace(".srt", "_보정완료.srt")
    with open(output_path, "w", encoding="utf-8-sig") as f:
        f.writelines(corrected_srt)
    
    print(f"✅ 보정 완료!")
    print(f"📄 원본: {os.path.basename(srt_path)}")
    print(f"✨ 결과: {os.path.basename(output_path)}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("사용법: py srt_final_fixer.py <srt파일경로> <대본파일경로>")
    else:
        fix_srt(sys.argv[1], sys.argv[2])

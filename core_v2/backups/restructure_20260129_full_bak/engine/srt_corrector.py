import re
import os
import sys
import difflib

def normalize(text):
    """비교를 위해 특수문자 제거 및 소문자화"""
    if not text: return ""
    return re.sub(r'[^a-zA-Z가-힣0-9]', '', str(text)).lower()

def clean_script_words(text):
    """대본에서 발화되지 않는 태그들을 제거하고 단어와 원본 텍스트 리스트 반환"""
    # SFX 및 각종 태그 제거 (정규식은 muhyup_factory와 동일하게 유지)
    text = re.sub(r'\[SFX:.*?\]', ' ', text)
    text = re.sub(r'\[(대사|묘사|지문|설명|SFX|챕터|CHAPTER).*?\]', ' ', text, flags=re.IGNORECASE)
    text = re.sub(r'\(.*?\)', ' ', text)
    
    # 단어별로 쪼개되, 빈 칸은 무시
    raw_words = text.split()
    return raw_words

def parse_srt(srt_content):
    """SRT 내용을 객체 리스트로 변환"""
    blocks = re.split(r'\n\s*\n', srt_content.strip())
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

def correct_srt_content(srt_content, script_text):
    # 1. 준비
    script_words = clean_script_words(script_text)
    srt_entries = parse_srt(srt_content)
    
    if not script_words or not srt_entries:
        return srt_content

    # 2. 정규화된 리스트 생성 (매칭용)
    script_norm = [normalize(w) for w in script_words]
    srt_all_words = []
    for entry in srt_entries:
        srt_all_words.extend(entry['words'])
    srt_norm = [normalize(w) for w in srt_all_words]

    # 3. Fuzzy Matching (SequenceMatcher)
    matcher = difflib.SequenceMatcher(None, script_norm, srt_norm)
    
    # SRT 단어 인덱스 -> 대본 단어 인덱스 맵 생성
    srt_to_script_map = {}
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == 'equal':
            for offset in range(i2 - i1):
                srt_to_script_map[j1 + offset] = i1 + offset
        elif tag == 'replace':
            # 발음 교정 등으로 인해 변형된 경우 (안방 -> 안빵 등)
            # 글자 수가 비슷하면 매칭 시도
            if (i2 - i1) == (j2 - j1):
                for offset in range(i2 - i1):
                    srt_to_script_map[j1 + offset] = i1 + offset

    # 4. 결과 재구성
    corrected_srt = []
    word_ptr = 0
    last_script_idx = -1

    for entry in srt_entries:
        entry_word_indices = range(word_ptr, word_ptr + len(entry['words']))
        word_ptr += len(entry['words'])
        
        # 이 항목에 해당하는 대본 단어 찾기
        matched_script_indices = []
        for idx in entry_word_indices:
            script_idx = srt_to_script_map.get(idx)
            if script_idx is not None:
                matched_script_indices.append(script_idx)
        
        if matched_script_indices:
            # 연속된 범위로 보정 (중간에 빠진 단어 포함)
            start_idx = min(matched_script_indices)
            end_idx = max(matched_script_indices)
            
            # 이전 항목과 겹치지 않게 조절
            if start_idx <= last_script_idx:
                start_idx = last_script_idx + 1
            
            if start_idx <= end_idx:
                corrected_text = " ".join(script_words[start_idx : end_idx + 1])
                last_script_idx = end_idx
            else:
                corrected_text = entry['text']
        else:
            # 매칭 실패 시 원본 유지
            corrected_text = entry['text']
            
        corrected_srt.append(f"{entry['num']}\n{entry['time']}\n{corrected_text}\n\n")

    return "".join(corrected_srt)

def main(srt_path, script_path):
    if not os.path.exists(srt_path) or not os.path.exists(script_path):
        print("❌ 파일을 찾을 수 없습니다.")
        return

    with open(srt_path, "r", encoding="utf-8-sig") as f:
        srt_content = f.read()
    with open(script_path, "r", encoding="utf-8") as f:
        script_text = f.read()

    corrected = correct_srt_content(srt_content, script_text)
    
    with open(srt_path, "w", encoding="utf-8-sig") as f:
        f.write(corrected)
    print(f"✅ 보정 완료: {srt_path}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: py srt_corrector.py <srt_path> <script_path>")
    else:
        main(sys.argv[1], sys.argv[2])

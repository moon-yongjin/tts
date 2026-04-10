import re
from pathlib import Path

def split_chunks(text, max_chars=120):
    lines = text.splitlines()
    final_chunks = []
    for line in lines:
        line = line.strip()
        if not line: continue
        # 정규식으로 문장 단위 분리
        sentences = re.findall(r'[^.!?,\s][^.!?,\n]*[.!?,\n]*', line)
        current_chunk = ""
        for s in sentences:
            s = s.strip()
            if not s: continue
            if len(current_chunk) + len(s) + 1 <= max_chars:
                if current_chunk: current_chunk += " " + s
                else: current_chunk = s
            else:
                if current_chunk: final_chunks.append(current_chunk)
                current_chunk = s
        if current_chunk: final_chunks.append(current_chunk)
    return [c.strip() for c in final_chunks if c.strip()]

def main():
    script_path = Path("/Users/a12/projects/tts/대본.txt")
    if not script_path.exists():
         print("❌ 파일 없음")
         return
         
    with open(script_path, "r", encoding="utf-8") as f:
         text = f.read().strip()
         
    chunks = split_chunks(text)
    print(f"📊 총 청크(문장) 수: {len(chunks)}개\n")
    
    for i, c in enumerate(chunks):
         print(f"[{i+1}] {c}")

if __name__ == "__main__":
    main()

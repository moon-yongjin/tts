import os
import sys
import re
from pathlib import Path

# Add project root to path for imports
PROJ_ROOT = Path("/Users/a12/projects/tts")
sys.path.append(str(PROJ_ROOT))

try:
    from Ollama_Studio.llm_router import ask_huggingface
except ImportError:
    print("❌ llm_router import failed.")
    sys.exit(1)

def split_chunks(text, max_chars=120):
    lines = text.splitlines()
    final_chunks = []
    for line in lines:
        line = line.strip()
        if not line: continue
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
         print("❌ 대본 파일이 없습니다.")
         return
         
    with open(script_path, "r", encoding="utf-8") as f:
         text = f.read().strip()
         
    chunks = split_chunks(text)
    print(f"📊 총 분리된 청크 수: {len(chunks)}개")
    
    if len(chunks) == 0:
         print("⚠️ 처리할 청크가 없습니다.")
         return

    full_answer = ""
    batch_size = 10
    total_batches = (len(chunks) + batch_size - 1) // batch_size

    print(f"\n🧠 Consulting 'Hugging Model' in {total_batches} batches...")

    for b in range(total_batches):
        start_idx = b * batch_size
        end_idx = min((b + 1) * batch_size, len(chunks))
        batch_chunks = chunks[start_idx:end_idx]
        
        chunk_list_text = ""
        for i, c in enumerate(batch_chunks):
            chunk_list_text += f"{start_idx + i + 1}. {c}\n"

        # print(f"\n💡 Batch {b+1}/{total_batches} 전송 중... ({start_idx+1}~{end_idx})")
        
        question = f"""
!!! 중요 !!! [필수 조건] !!! 중요 !!!
당신은 한국어 숏폼 연출 대본 및 디자인 전문 작가입니다.
아래에 제공되는 텍스트는 숏폼 영상 제작을 위해 분리된 **문장 청크(Sentence Chunks)**입니다.

**미션: 각 번호(청크)에 1:1 매칭되는 이미지 생성 프롬프트를 작성해 주세요.**

[작성 포맷]
번호 [화면 연출]: (이 장면에 어울리는 극적인 비주얼 설명, 한글)
Prompt: (Flux/Midjourney용 물리적 설명 영문 프롬프트)

[문장 청크 리스트]
{chunk_list_text}

모든 답변 형식은 위의 [작성 포맷]을 엄격히 준수해야 하며, 영어 프롬프트 줄을 제외한 연출 지시문은 **한국어**로만 출력해 주세요.
번호는 제공된 순서대로({start_idx+1}부터 {end_idx}까지) 이어져야 합니다.
"""

        try:
            answer = ask_huggingface(question)
            full_answer += answer + "\n\n"
            print(f"✅ Batch {b+1}/{total_batches} 완료")
        except Exception as e:
            print(f"❌ Batch {b+1} 에서 실패: {e}")
            full_answer += f"\n[Batch {b+1} 에러 발생]\n"

    print("\n📜 --- Hugging Model's 31 Image Prompts ---")
    print(full_answer)
    print("------------------------------------------\n")
    
    output_path = "/Users/a12/Downloads/31_이미지_프롬프트_허깅.txt"
    with open(output_path, "w", encoding="utf-8") as f:
         f.write(full_answer)
    print(f"✅ 이미지 프롬프트 저장 완료: {output_path}")


if __name__ == "__main__":
    main()

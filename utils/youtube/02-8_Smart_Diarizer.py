import os
import sys
import json
import re
from pathlib import Path
from google import genai
from google.genai import types

# [설정]
PROJECT_ROOT = Path(__file__).parent.parent.parent
CONFIG_PATH = PROJECT_ROOT / "config.json"

def load_gemini_key():
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            config = json.load(f)
            return config.get("Gemini_API_KEY")
    except:
        return None

def parse_srt(srt_path):
    """SRT 파일을 파싱하여 (index, timestamp, text) 리스트 반환"""
    with open(srt_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # SRT 패턴: index \n time \n text \n\n
    blocks = re.split(r'\n\n+', content.strip())
    segments = []
    for block in blocks:
        lines = block.split('\n')
        if len(lines) >= 3:
            index = lines[0]
            timestamp = lines[1]
            text = " ".join(lines[2:])
            segments.append({"index": index, "time": timestamp, "text": text})
    return segments

def diarize_segments(segments):
    api_key = load_gemini_key()
    if not api_key:
        print("❌ Gemini API Key를 찾을 수 없습니다.")
        return None
    
    client = genai.Client(api_key=api_key)
    
    # 세그먼트를 50개씩 묶어서 처리 (컨텍스트 유지를 위해)
    chunk_size = 50
    diarized_results = []
    
    print(f"🧠 총 {len(segments)}개의 문장을 분석 중입니다...")
    
    for i in range(0, len(segments), chunk_size):
        chunk = segments[i:i + chunk_size]
        chunk_text = "\n".join([f"{s['index']}|{s['time']}|{s['text']}" for s in chunk])
        
        prompt = f"""
다음은 유튜브 토크쇼(김창옥쇼)의 자막 데이터입니다. 
각 문장의 앞뒤 문맥을 파악하여 누가 말했는지 화자(김창옥, 사연자, 관객 등)를 분류해 주세요.

**분류 규칙:**
1. 문맥상 질문을 하거나 강연을 이끄는 사람은 '김창옥'입니다.
2. 자기 고민을 털어놓거나 대답을 하는 주인공은 '사연자'입니다.
3. 중간에 크게 웃거나 소리를 지르는 등 다수는 '관객'입니다.
4. 화자를 알 수 없는 경우 '기타'로 표시하세요.

**입력 형식:** 번호|시간|내용
{chunk_text}

---
**출력 형식 (JSON 배열만 출력):**
[
  {{"index": "1", "speaker": "김창옥", "text": "안녕하세요"}},
  ...
]
"""
        try:
            print(f"   [{i//chunk_size + 1}/{(len(segments)-1)//chunk_size + 1}] 분석 중...")
            response = client.models.generate_content(
                model='gemini-2.0-flash',
                contents=prompt,
                config=types.GenerateContentConfig(response_mime_type="application/json")
            )
            raw_data = json.loads(response.text.strip())
            
            # 원본 세그먼트와 매칭하여 시간 정보 복구
            for j, item in enumerate(raw_data):
                full_item = chunk[j].copy()
                full_item["speaker"] = item.get("speaker", "알수없음")
                diarized_results.append(full_item)
                
        except Exception as e:
            print(f"❌ Gemini 분석 중 오류: {e}")
            # 오류 시 이름 없이 원본이라도 넣음
            for s in chunk:
                s["speaker"] = "Error"
                diarized_results.append(s)

    return diarized_results

def main():
    print("==========================================")
    print("🧠 지능형 화자 분리 대본 생성기 (Gemini)")
    print("==========================================")
    
    if len(sys.argv) < 2:
        input_path = input("📄 분석할 SRT 파일 혹은 폴더 경로를 입력하세요: ").strip()
    else:
        input_path = sys.argv[1]

    path = Path(input_path).resolve()
    
    if path.is_dir():
        files = list(path.glob("*.srt"))
        if not files:
            print("❌ 폴더 내에 SRT 파일이 없습니다.")
            return
        target_file = files[0]
    else:
        target_file = path

    if target_file.suffix != ".srt":
        print("❌ SRT 파일이 아닙니다.")
        return

    # 1. SRT 파싱
    segments = parse_srt(target_file)
    if not segments:
        print("❌ 파싱할 자막 내용이 없습니다.")
        return

    # 2. 화자 분석
    diarized_data = diarize_segments(segments)
    
    if diarized_data:
        # 3. 결과 저장 (전체 버전)
        output_path = target_file.parent / f"{target_file.stem}_화자분리.txt"
        with open(output_path, "w", encoding="utf-8") as f:
            for item in diarized_data:
                f.write(f"[{item['time']}] {item['speaker']}: {item['text']}\n")
        
        # 4. 사연자 버전 추출
        story_clean_path = target_file.parent / f"{target_file.stem}_사연자_목소리만.txt"
        with open(story_clean_path, "w", encoding="utf-8") as f:
            f.write("=== 사연자(주인공) 발언 구간 모음 ===\n\n")
            for item in diarized_data:
                if item['speaker'] == "사연자":
                    f.write(f"[{item['time']}] {item['text']}\n")

        print("\n" + "="*40)
        print("✨ 화자 분리 완료!")
        print(f"📝 전체 대본: {output_path.name}")
        print(f"🎙️ 사연자만: {story_clean_path.name}")
        print("="*40)
        
        os.system(f"open {output_path.parent}")
    else:
        print("❌ 화자 분리에 실패했습니다.")

if __name__ == "__main__":
    main()

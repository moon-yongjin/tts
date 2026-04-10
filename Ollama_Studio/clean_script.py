import re
import sys
import os

def clean_yadam_script(file_path):
    if not os.path.exists(file_path):
        print(f"❌ 파일을 찾을 수 없습니다: {file_path}")
        return

    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read()

    # 1. DeepSeek/Gemini 생각 태그 제거
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL).strip()
    
    # 2. 배우 이름 태그 제거 (이름: "대사" -> "대사")
    lines = text.splitlines()
    cleaned_lines = []
    tag_pattern = re.compile(r'^[^"]+?[:：]\s*')
    
    for line in lines:
        stripped_line = line.strip()
        if '"' in stripped_line:
            new_line = tag_pattern.sub('', stripped_line)
            cleaned_lines.append(new_line)
        else:
            cleaned_lines.append(stripped_line)
            
    text = "\n".join(cleaned_lines)
    
    # 3. 스테이지 디렉션(괄호 내용) 제거
    text = re.sub(r'\(.*?\)', '', text)
    text = re.sub(r'\[.*?\]', '', text)
    
    # 4. Qwen TTS 초강력 음향 정제 (쉼표 기반 호흡 최적화)
    # 허용 문자: 한글, 영문, 숫자, 공백, 쌍따옴표("), 쉼표(,)
    # 마침표(.)는 쉼표(,)로 교체하여 자연스러운 호흡 유도
    
    text = text.replace('.', ',')
    
    final_chars = []
    for char in text:
        if char == '"' or char == ',' or char.isspace() or re.match(r'[가-힣a-zA-Z0-9]', char):
            final_chars.append(char)
        else:
            final_chars.append(" ")
            
    result = "".join(final_chars)
    
    # 5. 중복 쉼표 및 공백 정제
    result = re.sub(r',+', ',', result) # 중복 쉼표 제거
    result = re.sub(r' +', ' ', result)
    result = result.strip()
    
    # 결과 저장
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(result)
    
    print(f"✅ Qwen TTS 최적화 정제 완료: {file_path}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        clean_yadam_script(sys.argv[1])
    else:
        print("사용법: python clean_script.py [file_path]")

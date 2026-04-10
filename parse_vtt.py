import sys
import re

# VTT 파일 경로 
filename = "이혼하자마자 내 친구와 결혼한 남편, 그 둘이 웃으며 하는 말이 충격입니다 [ 오디오드라마 가족사연 감동사연 시니어드라마 이혼사연 오디오북 반전사연 복수극 ] [qr9hVKW4I7Q].ko.vtt"

try:
    with open(filename, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    clean_lines = []
    for line in lines:
        line = line.strip()
        # 시간 타임스탬프, WEBVTT 헤더, 빈 줄 무시
        if "-->" in line or line.startswith("WEBVTT") or line.startswith("Kind:") or line.startswith("Language:") or not line:
            continue
        # HTML 태그 (<c> 등) 삭제
        line = re.sub(r'<[^>]+>', '', line)
        
        # 중복 라인 반복 방지 (자막 재생성 시 동일 대사가 중복으로 찍히는 문제 극복)
        if not clean_lines or clean_lines[-1] != line:
            clean_lines.append(line)

    # 대본 파일로 저장
    with open("/Users/a12/projects/tts/대본.txt", 'w', encoding='utf-8') as f:
        f.write("\n".join(clean_lines))

    print("✅ 대본 파싱 완료! -> /Users/a12/projects/tts/대본.txt")

except Exception as e:
    print(f"❌ 대본 변환 중 오류 발생: {e}")

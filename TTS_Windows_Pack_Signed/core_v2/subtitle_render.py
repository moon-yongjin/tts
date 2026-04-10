# 1. 필요한 라이브러리 불러오기
import os
import subprocess

# [설정] 워크스페이스 내로 복사된 FFmpeg 경로
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FFMPEG_PATH = os.path.join(BASE_DIR, r"ffmpeg\ffmpeg-2026-01-07-git-af6a1dd0b2-essentials_build\bin\ffmpeg")

# 2. ASS 자막 내용 정의 (테스트용)
ass_content = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,60,&H00FFFFFF,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,3,2,2,10,10,100,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,0:00:00.00,0:00:03.00,Default,,0,0,0,,작동 확인용 테스트 자막입니다.
Dialogue: 0,0:00:03.00,0:00:06.00,Default,,0,0,0,,FFmpeg 자막 합치기 성공!
"""

# 3. 자막 파일(test.ass) 생성
with open('test.ass', 'w', encoding='utf-8') as f:
    f.write(ass_content)
print("✅ 자막 파일(test.ass)이 생성되었습니다.")

# 4. 입력 영상 확인 및 FFmpeg 실행
input_video = 'input.mp4'
output_video = 'output_test.mp4'

if os.path.exists(input_video):
    print(f"🚀 렌더링을 시작합니다... (FFmpeg: {FFMPEG_PATH})")
    
    # 윈도우 경로 특수 처리: subtitles 필터는 콜론(:)과 백슬래시(\)에 민감함
    # 1. 절대 경로를 가져옴
    abs_ass_path = os.path.abspath('test.ass')
    # 2. 백슬래시를 슬래시로 변경
    ass_path = abs_ass_path.replace('\\', '/')
    # 3. 드라이브 문자 뒤의 콜론(:) 이스케이프 (C:/ -> C\\:/)
    ass_path = ass_path.replace(':', '\\:')
    
    # FFmpeg 명령어 구성
    args = [
        FFMPEG_PATH,
        "-i", input_video,
        "-vf", f"subtitles='{ass_path}'",
        "-y", output_video
    ]
    
    try:
        # 실행
        print(f"명령어 실행 중...")
        result = subprocess.run(args, capture_output=True, text=True, check=True)
        print(f"✨ 렌더링 완료! 결과물: {output_video}")
    except subprocess.CalledProcessError as e:
        print("❌ 렌더링에 실패했습니다.")
        print(f"에러 메시지:\n{e.stderr}")
    except Exception as e:
        print(f"❌ 예기치 않은 오류가 발생했습니다: {e}")
else:
    print(f"⚠️ {input_video} 파일이 없습니다. (현재 경로: {os.getcwd()})")

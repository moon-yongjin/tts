# 1. 필요한 라이브러리 불러오기
import os

# Google Colab 전용 라이브러리는 로컬 환경에서는 필요 없으므로 예외 처리합니다.
try:
    from google.colab import files
except ImportError:
    files = None

# 2. ASS 자막 내용 정의 (코드로 자막 스타일과 내용을 제어)
# Tip: 여기서 내용을 수정하면 영상에 반영됩니다.
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
Dialogue: 0,0:00:00.00,0:00:05.00,Default,,0,0,0,,부자가 못 되는 건\\N지능의 문제다.
Dialogue: 0,0:00:05.00,0:00:10.00,Default,,0,0,0,,감성 비용을 제거해라.\\N가성비 최악의 지출이다.
"""

# FFmpeg 경로를 찾는 함수
def get_ffmpeg_path():
    """시스템 PATH 또는 알려진 설치 경로(Vrew, CapCut 등)에서 FFmpeg를 찾습니다."""
    # 1. 시스템 PATH 확인
    import shutil
    ffmpeg_system = shutil.which("ffmpeg")
    if ffmpeg_system:
        return ffmpeg_system

    # 2. 알려진 로컬 설치 경로 확인
    appdata = os.environ.get('APPDATA')
    localappdata = os.environ.get('LOCALAPPDATA')
    
    known_paths = [
        # Vrew 설치 경로
        os.path.join(appdata, r"vrew\ffmpeg_lgpl_v19\ffmpeg"),
        # CapCut 설치 경로
        os.path.join(localappdata, r"CapCut\Apps\7.9.0.3294\ffmpeg"),
        os.path.join(localappdata, r"CapCut\Apps\2025713212110502_Packet\6.5.0.2562\ffmpeg"),
        # 기타 사용자 다운로드 폴더 등 (필요시 추가)
    ]

    for path in known_paths:
        if os.path.exists(path):
            return f'"{path}"' # 경로에 공백이 있을 수 있으므로 따옴표 처리
            
    return "ffmpeg" # 못 찾으면 일단 기본 명령어로 반환

# 3. 자막 파일(test.ass) 생성
with open('test.ass', 'w', encoding='utf-8') as f:
    f.write(ass_content)
print("✅ 자막 파일(test.ass)이 성공적으로 생성되었습니다.")

# 4. 입력 영상 확인 및 FFmpeg 실행
# 주의: 스크립트 실행 경로에 'input.mp4'라는 이름의 영상이 있어야 합니다.
input_video = 'input.mp4'
output_video = 'output_final.mp4'
ffmpeg_cmd = get_ffmpeg_path()

if os.path.exists(input_video):
    print(f"🚀 {input_video}를 사용하여 렌더링을 시작합니다... (FFmpeg: {ffmpeg_cmd})")
    
    # FFmpeg 명령어 실행 (subprocess.run 사용 권장)
    import subprocess
    
    # ffmpeg_cmd가 따옴표로 감싸져 있을 수 있으므로 스트립트 처리
    cmd_path = ffmpeg_cmd.strip('"')
    
    args = [
        cmd_path,
        "-i", input_video,
        "-vf", "subtitles=test.ass",
        "-y", output_video
    ]
    
    try:
        result = subprocess.run(args, capture_output=True, text=True, check=True)
        print(f"✨ 렌더링 완료! 결과물: {output_video}")
    except subprocess.CalledProcessError as e:
        print("❌ 렌더링에 실패했습니다.")
        print(f"에러 메시지: {e.stderr}")
    except Exception as e:
        print(f"❌ 예기치 않은 오류가 발생했습니다: {e}")
else:
    print(f"⚠️ {input_video} 파일이 없습니다. 영상을 {os.getcwd()} 경로에 넣어주시고 파일명을 {input_video}로 변경해주세요.")

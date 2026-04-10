import os
import subprocess
import time
import re
import sys

# [설정] 
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if os.path.basename(SCRIPT_DIR) == "core_v2":
    ROOT_DIR = os.path.dirname(SCRIPT_DIR)
    CORE_DIR = SCRIPT_DIR
else:
    ROOT_DIR = SCRIPT_DIR
    CORE_DIR = os.path.join(ROOT_DIR, "core_v2")

FFMPEG_EXE = "/Users/a12/miniforge3/envs/qwen-tts/bin/ffmpeg"
if not os.path.exists(FFMPEG_EXE):
    FFMPEG_EXE = "ffmpeg"

DOWNLOADS_DIR = os.path.join(os.path.expanduser("~"), "Downloads")

def get_latest_folder():
    folders = [os.path.join(DOWNLOADS_DIR, d) for d in os.listdir(DOWNLOADS_DIR) 
               if os.path.isdir(os.path.join(DOWNLOADS_DIR, d)) and (d.startswith("무협_생성_") or d.startswith("무협_로컬생성_"))]
    if not folders: return None
    return max(folders, key=os.path.getmtime)

def create_thumbnail_ass(ass_path, text, font_size=250):
    """섬네일용 대형 자막 스타일 ASS 생성"""
    # 텍스트 줄바꿈 처리 (\N)
    text = text.replace("\n", "\\N")
    
    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1280
PlayResY: 720
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Title,Cafe24 Ohsquare,{font_size},&H0000FFFF,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,15,10,5,10,10,10,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,0:00:00.00,0:00:10.00,Title,,0,0,0,,{text}
"""
    with open(ass_path, "w", encoding="utf-8") as f:
        f.write(header)

def make_thumbnail():
    print("\n" + "="*50)
    print("🎨 [STEP 08] ASS 기반 시네마틱 섬네일 생성")
    print("="*50)
    
    target_dir = get_latest_folder()
    if not target_dir:
        print("❌ 작업 폴더를 찾을 수 없습니다."); return

    # 1. 소스 이미지 찾기 (첫 번째 스케치 이미지 등)
    images = sorted([f for f in os.listdir(target_dir) if f.endswith(".png")])
    if not images:
        print(f"⚠️ {target_dir} 폴더에 PNG 이미지가 없습니다. 다른 폴더를 검색합니다.")
        # 다른 무협 폴더도 확인
        all_dirs = sorted([d for d in os.listdir(DOWNLOADS_DIR) if d.startswith("무협_")], reverse=True)
        img_path = None
        for d in all_dirs:
            d_path = os.path.join(DOWNLOADS_DIR, d)
            imgs = sorted([f for f in os.listdir(d_path) if f.endswith(".png")])
            if imgs:
                img_path = os.path.join(d_path, imgs[0])
                break
        if not img_path:
            print("❌ 원본 이미지를 찾을 수 없습니다."); return
    else:
        # 가장 임팩트 있는 장면(중간쯤) 선택
        idx = len(images) // 4
        img_path = os.path.join(target_dir, images[idx])

    print(f"📸 소스 이미지: {os.path.basename(img_path)}")
    
    # 2. 텍스트 입력 받기
    title = input("📝 섬네일 제목을 입력하세요 (엔터 시 기본값): ").strip()
    if not title:
        title = "운명의 열쇠\n복수의 시작" # 기본 예시

    # 3. ASS 생성
    ass_path = os.path.join(target_dir, "thumbnail.ass")
    create_thumbnail_ass(ass_path, title)
    
    # 4. FFmpeg 렌더링
    output_path = os.path.join(target_dir, "thumbnail_final.jpg")
    ass_path_fixed = os.path.abspath(ass_path).replace('\\', '/').replace(':', '\\:')
    fonts_dir = CORE_DIR.replace('\\', '/').replace(':', '\\:')
    
    cmd = [
        FFMPEG_EXE, "-y",
        "-i", img_path,
        "-vf", f"subtitles=filename='{ass_path_fixed}':fontsdir='{fonts_dir}'",
        "-q:v", "2",
        output_path
    ]
    
    print("🎬 섬네일 렌더링 중...")
    try:
        subprocess.run(cmd, check=True, capture_output=True)
        print(f"✅ 완성: {output_path}")
        # 프리뷰를 위해 복사
        shutil_dest = os.path.join(DOWNLOADS_DIR, "latest_thumbnail.jpg")
        import shutil
        shutil.copy2(output_path, shutil_dest)
    except subprocess.CalledProcessError as e:
        print(f"❌ 렌더링 실패: {e.stderr.decode()}")

if __name__ == "__main__":
    make_thumbnail()

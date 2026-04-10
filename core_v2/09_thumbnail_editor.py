import streamlit as st
import os
import re
import random
import subprocess
import time
from PIL import Image

# [설정]
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if os.path.basename(SCRIPT_DIR) == "core_v2":
    ROOT_DIR = os.path.dirname(SCRIPT_DIR)
    CORE_DIR = SCRIPT_DIR
else:
    ROOT_DIR = SCRIPT_DIR
    CORE_DIR = os.path.join(ROOT_DIR, "core_v2")

# 시스템 FFmpeg 사용
FFMPEG_EXE = "ffmpeg"
if not os.path.exists(FFMPEG_EXE):
    FFMPEG_EXE = "ffmpeg"

DOWNLOADS_DIR = os.path.join(os.path.expanduser("~"), "Downloads")

st.set_page_config(layout="wide", page_title="🎬 무협 섬네일 에디터")

def get_latest_folder():
    folders = [os.path.join(DOWNLOADS_DIR, d) for d in os.listdir(DOWNLOADS_DIR) 
               if os.path.isdir(os.path.join(DOWNLOADS_DIR, d)) and (d.startswith("무협_생성_") or d.startswith("무협_로컬생성_"))]
    if not folders: return None
    return max(folders, key=os.path.getmtime)

def hex_to_ass(hex_color):
    """#RRGGBB -> &H00BBGGRR format (ASS uses BGR)"""
    hex_color = hex_color.lstrip('#')
    r, g, b = hex_color[0:2], hex_color[2:4], hex_color[4:6]
    return f"{b}{g}{r}" # BGR 순서

def create_ass(ass_path, title_data, border_color_ass):
    """ASS 생성 엔진"""
    # 색상 변환
    c_main = hex_to_ass(title_data['c_main'])
    c_hl1 = hex_to_ass(title_data['c_hl1'])
    c_hl2 = hex_to_ass(title_data['c_hl2'])
    
    # 텍스트 치환
    def apply_hl(text):
        if not text: return ""
        # 키워드 하이라이팅
        if title_data['kw1']:
            pat = re.compile(re.escape(title_data['kw1']), re.IGNORECASE)
            text = pat.sub(f"{{\\\\c&H{c_hl1}&}}{title_data['kw1']}{{\\\\c&H{c_main}&}}", text)
        if title_data['kw2']:
            pat = re.compile(re.escape(title_data['kw2']), re.IGNORECASE)
            text = pat.sub(f"{{\\\\c&H{c_hl2}&}}{title_data['kw2']}{{\\\\c&H{c_main}&}}", text)
        return text

    l1 = apply_hl(title_data['line1'])
    l2 = apply_hl(title_data['line2'])

    ass_content = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1280
PlayResY: 720
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Main,Cafe24 Ohsquare,{title_data['fs_main']},&H00{c_main}&,&H00000000,&H00000000,-1,0,0,0,100,100,-6,0,1,1.5,4,2,10,10,10,1
Style: Side,Cafe24 Ohsquare,{title_data['fs_side']},&H00{c_hl1}&,&H00000000,&H00000000,-1,0,0,0,100,100,0,12,1,1,2,6,30,30,350,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 1,0:00:00.00,0:00:10.00,Main,,0,0,0,,{{\\pos({title_data['x_pos']},{title_data['y_pos']-title_data['gap']})}}{l1}
Dialogue: 1,0:00:00.00,0:00:10.00,Main,,0,0,0,,{{\\pos({title_data['x_pos']},{title_data['y_pos']})}}{l2}
Dialogue: 2,0:00:00.00,0:00:10.00,Side,,0,0,0,,{{\\pos({title_data['side_x']},{title_data['side_y']})}}{title_data['side']}
"""
    with open(ass_path, "w", encoding="utf-8") as f:
        f.write(ass_content)

# --- UI ---
st.title("🎬 시네마틱 섬네일 에디터 (Web Pro)")

target_dir = st.session_state.get('target_dir', get_latest_folder())
if not target_dir:
    st.error("작업 폴더를 찾을 수 없습니다.")
    st.stop()

# 이미지 로드
col1, col2 = st.columns([1, 1])

with col1:
    images = sorted([f for f in os.listdir(target_dir) if f.lower().endswith(('.png', '.jpg'))])
    img_idx = st.slider("📸 이미지 선택", 0, len(images)-1, len(images)-1)
    selected_img = images[img_idx]
    img_path = os.path.join(target_dir, selected_img)
    st.image(img_path, caption=selected_img, use_container_width=True)

with col2:
    st.subheader("🛠️ 텍스트 & 스타일 조정")
    
    with st.expander("📝 텍스트 입력", expanded=True):
        line1 = st.text_input("메인 줄 1", "300억 가로챈 남편의")
        line2 = st.text_input("메인 줄 2", "추악하고 소름돋는 정체")
        
        c1, c2 = st.columns(2)
        kw1 = c1.text_input("강조 단어 1 (Keyword)", "정체")
        kw2 = c2.text_input("강조 단어 2 (Amount)", "300억")
        
        side_text = st.text_input("사이드 문구", "[소름 주의]")

    with st.expander("🎨 색상 팔레트", expanded=True):
        cp1, cp2, cp3 = st.columns(3)
        c_main = cp1.color_picker("메인 텍스트", "#FFFFFF")
        c_hl1 = cp2.color_picker("강조색 1 (Keyword)", "#00FFFF")
        c_hl2 = cp3.color_picker("강조색 2 (Amount)", "#FFFF00")
        
        border_color = st.color_picker("프레임 테두리 색상", "#0000FF") # 기본 레드

    with st.expander("📏 위치 & 크기 (초정밀 커서)", expanded=True):
        st.caption("메인 텍스트 좌표")
        x_pos = st.number_input("X 좌표 (중앙 640)", value=640, step=10)
        y_pos = st.number_input("Y 좌표 (바닥 705)", value=705, step=5)
        gap = st.number_input("줄간격 (Gap)", value=100, step=5)
        fs_main = st.number_input("글자 크기", value=130, step=5)
        
        st.divider()
        st.caption("사이드 문구 좌표")
        side_x = st.number_input("Side X", value=1100, step=10)
        side_y = st.number_input("Side Y", value=300, step=10)
        fs_side = st.number_input("Side 크기", value=55, step=5)

# 렌더링 버튼
if st.button("✨ 섬네일 미리보기 & 생성", type="primary"):
    data = {
        "line1": line1, "line2": line2,
        "kw1": kw1, "kw2": kw2,
        "side": side_text,
        "c_main": c_main, "c_hl1": c_hl1, "c_hl2": c_hl2,
        "x_pos": x_pos, "y_pos": y_pos, "gap": gap,
        "fs_main": fs_main, "side_x": side_x, "side_y": side_y, "fs_side": fs_side
    }
    
    ass_path = os.path.join(target_dir, "web_temp.ass")
    # ASS 프레임 색은 BGR 헥스값 필요 (Drawbox필터는 0xRRGGBB)
    create_ass(ass_path, data, border_color)
    
    # 테두리 색상 처리 (RGB -> 0xRRGGBB)
    bd_hex = border_color.lstrip('#')
    
    output_temp = os.path.join(target_dir, "preview.jpg")
    ass_fix = os.path.abspath(ass_path).replace('\\', '/').replace(':', '\\:')
    font_fix = CORE_DIR.replace('\\', '/').replace(':', '\\:')
    
    cmd = [
        FFMPEG_EXE, "-y", "-i", img_path,
        "-vf", f"drawbox=t=30:c=0x{bd_hex},subtitles=filename='{ass_fix}':fontsdir='{font_fix}'",
        "-vframes", "1", output_temp
    ]
    
    with st.spinner("렌더링 중..."):
        subprocess.run(cmd)
        st.success("완료!")
        st.image(output_temp, caption="최종 결과물", use_container_width=True)
        
        # 저장용 복사
        ts = int(time.time())
        final_path = os.path.join(DOWNLOADS_DIR, f"web_thumb_{ts}.jpg")
        import shutil
        shutil.copy2(output_temp, final_path)
        st.caption(f"저장 위치: {final_path}")

import streamlit as st
import os
import json
import subprocess
import sys
import time
import re
from datetime import datetime

# [Paths]
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR) if os.path.basename(BASE_DIR) == "WebUI" else BASE_DIR
CONFIG_PATH = os.path.join(PROJECT_ROOT, "config.json")
DEFAULT_SCRIPT_PATH = os.path.join(PROJECT_ROOT, "대본.txt")
DOWNLOADS_DIR = os.path.join(os.path.expanduser("~"), "Downloads")

# [Page Setup]
st.set_page_config(
    page_title="Muhyup Visual Studio Pro",
    page_icon="🎨",
    layout="wide",
)

# [Custom CSS for Premium Look]
st.markdown("""
<style>
    .main {
        background-color: #0e1117;
    }
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        height: 3em;
        font-weight: bold;
        background-color: #238636;
        color: white;
    }
    .stCodeBlock {
        border-radius: 10px;
    }
    h1, h2, h3 {
        color: #e6edf3;
    }
    .stTextArea textarea {
        background-color: #0d1117;
        color: #c9d1d9;
        font-family: 'Inter', sans-serif;
    }
    .status-card {
        padding: 20px;
        border-radius: 10px;
        background-color: #161b22;
        border: 1px solid #30363d;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

# [Helper: Load/Save Config]
def load_config():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except: return {}
    return {}

def save_config(data):
    current = load_config()
    current.update(data)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(current, f, indent=2, ensure_ascii=False)

# [Helper: Get Latest Folder]
def get_latest_generation_folder():
    try:
        subdirs = [os.path.join(DOWNLOADS_DIR, d) for d in os.listdir(DOWNLOADS_DIR) 
                   if os.path.isdir(os.path.join(DOWNLOADS_DIR, d)) and d.startswith("무협_생성_")]
        if subdirs:
            return sorted(subdirs)[-1]
    except: pass
    return None

# [Sidebar: Settings]
st.sidebar.title("🎨 Visual Settings")
config = load_config()

with st.sidebar.expander("🔑 API Configuration", expanded=False):
    g_key = st.text_input("Gemini API Key", value=config.get("Gemini_API_KEY", ""), type="password")
    if st.button("Save API Key"):
        save_config({"Gemini_API_KEY": g_key})
        st.success("Config updated!")

st.sidebar.markdown("---")
selected_style = st.sidebar.selectbox("🎨 화풍 스타일 선택", ["스케치", "수묵화", "애니메이션", "고전민화", "김성모", "컬러스케치"])
image_count = st.sidebar.number_input("🖼️ 생성할 이미지 수량 (0=자동)", min_value=0, value=10)
use_korean_context = st.sidebar.toggle("🇰🇷 한국인 설정 강제 (추천)", value=True)

st.sidebar.markdown("---")
st.sidebar.info("💡 **팁**: 한국인 기와 얼굴을 강조하려면 '한국인 설정'을 켜두세요.")

# [Main UI]
st.title("🎨 이미지 스튜디오 프로")
st.caption("고품질 무협 이미지 생성 및 비주얼 디렉팅 시스템")

col_left, col_right = st.columns([1.5, 1])

with col_left:
    st.subheader("📝 대본 편집기")
    
    script_content = ""
    if os.path.exists(DEFAULT_SCRIPT_PATH):
        try:
            with open(DEFAULT_SCRIPT_PATH, "r", encoding="utf-8") as f:
                script_content = f.read()
        except: pass

    script_editor = st.text_area("내용 수정", value=script_content, height=450, placeholder="여기에 대본 내용을 입력하세요...")
    
    if st.button("💾 대본 저장 및 적용"):
        try:
            with open(DEFAULT_SCRIPT_PATH, "w", encoding="utf-8") as f:
                f.write(script_editor)
            st.success("대본이 저장되었습니다.")
        except Exception as e:
            st.error(f"저장 실패: {e}")

with col_right:
    st.subheader("🚀 이미지 생성 실행")
    
    if "is_running" not in st.session_state:
        st.session_state.is_running = False
    
    run_btn = st.button("🚀 생성 시작", type="primary", disabled=st.session_state.is_running)
    
    log_container = st.empty()
    progress_bar = st.progress(0)
    
    if run_btn:
        st.session_state.is_running = True
        logs = []
        log_container.code("초기화 중...", language="bash")
        
        # [NEW] 02_visual_director_96.py 실행
        python_exe = "/Users/a12/miniforge3/envs/qwen-tts/bin/python" # 기존 스크립트 기반 경로
        if not os.path.exists(python_exe):
            python_exe = sys.executable
            
        cmd = [python_exe, os.path.join(PROJECT_ROOT, "core_v2/02_visual_director_96.py"), selected_style, "--count", str(int(image_count))]
        
        try:
            process = subprocess.Popen(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.STDOUT, 
                text=True, 
                cwd=PROJECT_ROOT,
                encoding='utf-8',
                errors='replace'
            )
            
            for line in process.stdout:
                logs.append(line)
                # 로그가 너무 길어지면 UI가 느려지므로 마지막 20줄만 유지
                display_logs = "".join(logs[-30:])
                log_container.code(display_logs, language="bash")
                
                # 진행률 추정 (로그 메시지 기반 간단 트릭)
                if "파트" in line and "/" in line:
                    try:
                        match = re.search(r'(\d+)/(\d+)', line)
                        if match:
                            curr, total = map(int, match.groups())
                            progress_bar.progress(curr / total)
                    except: pass
            
            process.wait()
            
            if process.returncode == 0:
                st.success("✨ 이미지 생성이 완료되었습니다!")
                st.balloons()
            else:
                st.error(f"❌ 생성 중 오류 발생 (코드: {process.returncode})")
        
        except Exception as e:
            st.error(f"🔥 치명적 오류: {str(e)}")
        
        st.session_state.is_running = False
        st.rerun()

    st.markdown("---")
    st.subheader("📂 최신 생성 결과물")
    latest_folder = get_latest_generation_folder()
    
    if latest_folder:
        st.info(f"📍 폴더: {os.path.basename(latest_folder)}")
        images = [f for f in os.listdir(latest_folder) if f.endswith(".png")]
        if images:
            images.sort()
            # 갤러리 형태로 마지막 4장만 미리보기
            cols = st.columns(2)
            for i, img_name in enumerate(images[-4:]):
                with cols[i % 2]:
                    st.image(os.path.join(latest_folder, img_name), caption=img_name, use_container_width=True)
            
            if st.button("📂 폴더 열기 (다운로드)"):
                subprocess.run(["open", latest_folder])
        else:
            st.warning("폴더 안에 이미지가 아직 없습니다.")
    else:
        st.write("생성된 폴더가 없습니다.")

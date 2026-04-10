import streamlit as st
import os
import json
import subprocess
import sys
import re
import time
from datetime import datetime

# [Paths]
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR) if os.path.basename(BASE_DIR) == "WebUI" else BASE_DIR
CONFIG_PATH = os.path.join(PROJECT_ROOT, "config.json")
DEFAULT_SCRIPT_PATH = os.path.join(PROJECT_ROOT, "대본.txt")
DOWNLOADS_DIR = os.path.join(os.path.expanduser("~"), "Downloads")

# [Page Setup]
st.set_page_config(
    page_title="Muhyup Audio Studio Pro",
    page_icon="🎙️",
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
    }
    .stCodeBlock {
        border-radius: 10px;
    }
    .css-1offfwp {
        background-color: #161b22 !important;
    }
    .sidebar .sidebar-content {
        background-color: #161b22;
    }
    h1, h2, h3 {
        color: #e6edf3;
    }
    .stTextArea textarea {
        background-color: #0d1117;
        color: #c9d1d9;
        font-family: 'Courier New', Courier, monospace;
    }
</style>
""", unsafe_allow_html=True)

# [Helper: Find Assets]
def get_latest_audio_assets():
    """Find the latest Full_Merged mp3 and srt in Downloads"""
    try:
        mp3_files = [f for f in os.listdir(DOWNLOADS_DIR) if f.endswith(".mp3") and "_Full_Merged" in f]
        if not mp3_files: return None, None
        
        latest_mp3 = max([os.path.join(DOWNLOADS_DIR, f) for f in mp3_files], key=os.path.getmtime)
        latest_srt = latest_mp3.replace(".mp3", ".srt")
        
        if not os.path.exists(latest_srt): latest_srt = None
        return latest_mp3, latest_srt
    except:
        return None, None

def get_latest_master_mp4():
    """Find the latest Final Master MP4"""
    try:
        folders = [os.path.join(DOWNLOADS_DIR, d) for d in os.listdir(DOWNLOADS_DIR) 
                   if os.path.isdir(os.path.join(DOWNLOADS_DIR, d)) and "무협_생성_" in d]
        
        if not folders: return None
        
        latest_folder = max(folders, key=os.path.getmtime)
        mp4_files = [f for f in os.listdir(latest_folder) if f.endswith(".mp4") and "마스터" in f]
        
        if not mp4_files: return None
        
        latest_mp4 = max([os.path.join(latest_folder, f) for f in mp4_files], key=os.path.getmtime)
        return latest_mp4
    except:
        return None

# [Config Logic]
def load_config():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except: return {}
    return {}

def save_config(data):
    # Keep existing formatting by reading first if possible
    current = load_config()
    current.update(data)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(current, f, indent=2, ensure_ascii=False)

# [Sidebar: Settings]
st.sidebar.title("💎 Studio Settings")
config = load_config()

with st.sidebar.expander("🔑 API Configuration", expanded=False):
    g_key = st.text_input("Gemini API Key", value=config.get("Gemini_API_KEY", ""), type="password")
    
    if st.button("Save Configuration"):
        save_config({
            "Gemini_API_KEY": g_key
        })
        st.success("Config updated!")

st.sidebar.markdown("---")
st.sidebar.info("💡 **Tip**: 4번 공정 전 대본을 한 번 더 확인하세요.")

# [Main UI]
st.title("🎙️ 오디오 스튜디오 프로")
st.caption("고품질 배경음 및 효과음 레이어링 시스템 (프리미엄 에디션)")

# [Debugging Connectivity]
if st.sidebar.checkbox("접속 정보 보기"):
    import socket
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    st.sidebar.write(f"🏠 로컬 IP: {local_ip}")
    st.sidebar.write(f"🌐 접속 주소: http://{local_ip}:8501")

# [Asset Management Section]
st.subheader("📂 파일 선택")
col_assets_1, col_assets_2 = st.columns(2)

# 1. Script Selection (Uploader)
with col_assets_1:
    uploaded_script = st.file_uploader("대본 파일 선택 (.txt)", type=["txt"])
    if uploaded_script:
        # Save to DEFAULT_SCRIPT_PATH to be used by original scripts
        with open(DEFAULT_SCRIPT_PATH, "wb") as f:
            f.write(uploaded_script.getbuffer())
        script_path_input = DEFAULT_SCRIPT_PATH
        st.success(f"✅ '{uploaded_script.name}' 로드됨")
    else:
        script_path_input = DEFAULT_SCRIPT_PATH

# 2. Narration Selection (Uploader)
with col_assets_2:
    uploaded_audio = st.file_uploader("음성 파일 선택 (.mp3)", type=["mp3"])
    if uploaded_audio:
        # Create a temp narration file in Project Root for the scripts to find
        temp_audio_path = os.path.join(PROJECT_ROOT, "current_narration.mp3")
        with open(temp_audio_path, "wb") as f:
            f.write(uploaded_audio.getbuffer())
        narration_path_input = temp_audio_path
        st.success(f"✅ '{uploaded_audio.name}' 로드됨")
    else:
        # Fallback to latest in Downloads
        latest_audio_path, _ = get_latest_audio_assets()
        narration_path_input = latest_audio_path

st.markdown("---")

# [Layout]
col_left, col_right = st.columns([1.5, 1])

with col_left:
    st.subheader("📝 대본 편집기")
    
    script_content = ""
    if script_path_input and os.path.exists(script_path_input):
        try:
            with open(script_path_input, "r", encoding="utf-8") as f:
                script_content = f.read()
        except: pass

    script_editor = st.text_area("내용 수정", value=script_content, height=450)
    
    if st.button("💾 대본 변경사항 저장"):
        try:
            with open(script_path_input, "w", encoding="utf-8") as f:
                f.write(script_editor)
            st.success("대본이 성공적으로 저장되었습니다.")
        except Exception as e:
            st.error(f"저장 실패: {e}")

with col_right:
    st.subheader("🎵 오디오 미리보기")
    if narration_path_input and os.path.exists(narration_path_input):
        st.audio(narration_path_input)
    else:
        st.warning("선택된 음성 파일이 없습니다.")

    st.markdown("---")
    st.subheader("⚙️ 작업 스튜디오")
    
    # [NEW] Log Viewer Expander
    with st.expander("📄 상세 진행 로그 확인 (오류 발생 시 확인용)", expanded=False):
        log_box = st.empty()

    # Initialize session state for process tracking
    if "process_complete" not in st.session_state:
        st.session_state.process_complete = False
    if "final_file_path" not in st.session_state:
        st.session_state.final_file_path = None

    def get_explicit_targets(directory, base_name):
        """Finds the specific BGM mixed file and SFX layer file for merging."""
        bgm_mix = os.path.join(directory, f"{base_name}_Full_Merged-reverted.mp3")
        sfx_layer = os.path.join(directory, f"002_{base_name}_Full_Merged_배경_효과음_레이어.mp3")
        
        # Fallback: find by suffix if exact name fails
        if not os.path.exists(bgm_mix):
            candidates = [f for f in os.listdir(directory) if f.endswith("-reverted.mp3")]
            if candidates:
                bgm_mix = os.path.join(directory, max(candidates, key=lambda x: os.path.getmtime(os.path.join(directory, x))))
        
        if not os.path.exists(sfx_layer):
            candidates = [f for f in os.listdir(directory) if "_배경_효과음_레이어.mp3" in f]
            if candidates:
                sfx_layer = os.path.join(directory, max(candidates, key=lambda x: os.path.getmtime(os.path.join(directory, x))))
                
        return bgm_mix, sfx_layer

    def run_process_99():
        status_box = st.empty()
        timer_box = st.empty()
        st.session_state.process_complete = False
        
        start_time = time.time()
        
        # [CRITICAL] Fixed Base Name
        sync_base = "Studio_Project" 
        sync_mp3 = os.path.join(DOWNLOADS_DIR, f"{sync_base}_Full_Merged.mp3")
        sync_srt = os.path.join(DOWNLOADS_DIR, f"{sync_base}_Full_Merged.srt")
        
        try:
            from pydub import AudioSegment
            import shutil
            
            # 1. Sync & Detect MP3 Duration
            duration_ms = 0
            if narration_path_input and os.path.exists(narration_path_input):
                shutil.copy2(narration_path_input, sync_mp3)
                audio = AudioSegment.from_mp3(sync_mp3)
                duration_ms = len(audio)
                st.info(f"📁 음성 소스 준비 완료 ({duration_ms/1000:.1f}초)")
            
            # 2. Create Accurate Segmented SRT (Fixes SFX duration mismatch)
            with open(sync_srt, "w", encoding="utf-8") as f:
                if script_editor.strip().startswith("1") and "-->" in script_editor:
                    f.write(script_editor)
                else:
                    # Simple SRT (Single block)
                    def ms_to_srt_time(ms):
                        h, m, s, milli = int(ms / 3600000), int((ms % 3600000) / 60000), int((ms % 60000) / 1000), int(ms % 1000)
                        return f"{h:02d}:{m:02d}:{s:02d},{milli:03d}"
                    start_t = "00:00:00,000"
                    end_t = ms_to_srt_time(duration_ms)
                    f.write(f"1\n{start_t} --> {end_t}\n{script_editor[:1000]}\n\n")
            st.info(f"📁 자막(SRT) 데이터 동기화 완료")
        except Exception as e:
            st.error(f"⚠️ 초기화 중 오류: {e}")
            return

        python_exe = sys.executable
        
        # Original simple 99 flow
        steps = [
            ("1단계: 배경음(BGM) 엔진", "core_v2/04_bgm_master.py"),
            ("2단계: AI 효과음 레이어", "core_v2/05_audio_layer_factory.py"),
            ("3단계: 최종 통합 (영상)", "core_v2/07_master_integration.py")
        ]
        
        for name, script_file in steps:
            status_box.info(f"▶️ {name} 진행 중...")
            cmd = [python_exe, os.path.join(PROJECT_ROOT, script_file)]
            subprocess.run(cmd, cwd=PROJECT_ROOT)
        
        # Final result check
        latest_mp4 = get_latest_master_mp4()
        if latest_mp4:
            st.session_state.final_file_path = latest_mp4
            status_box.success("✅ 마스터 영상 생성이 완료되었습니다!")
        else:
            # Simple fallback: find latest mp3 containing "합본"
            candidates = [f for f in os.listdir(DOWNLOADS_DIR) if ".mp3" in f and ("합본" in f or "Merged" in f)]
            if candidates:
                latest_audio = os.path.join(DOWNLOADS_DIR, max(candidates, key=lambda x: os.path.getmtime(os.path.join(DOWNLOADS_DIR, x))))
                st.session_state.final_file_path = latest_audio
                status_box.success(f"✅ 오디오 합본 감지: {os.path.basename(latest_audio)}")
            else:
                status_box.error("❌ 생성된 결과물을 찾을 수 없습니다.")

        st.balloons()
        st.session_state.process_complete = True
        st.rerun()

    if st.button("🚀 오디오 통합 생성 시작", type="primary", use_container_width=True):
        if not narration_path_input or not os.path.exists(narration_path_input):
            st.error("먼저 음성 파일을 선택해 주세요.")
        else:
            run_process_99()
            
    # [FIX] Download Section (Always rendered after completion)
    if st.session_state.process_complete and st.session_state.final_file_path:
        st.markdown("---")
        st.header("📥 생성 완료! 파일을 다운로드하세요")
        col_dl_1, col_dl_2 = st.columns([2, 1])
        
        with col_dl_1:
            display_name = os.path.basename(st.session_state.final_file_path)
            is_mp4 = display_name.endswith(".mp4")
            st.success(f"생성된 파일: {display_name}")
            with open(st.session_state.final_file_path, "rb") as f:
                st.download_button(
                    label="💾 지금 바탕화면(다운로드)에 저장하기",
                    data=f.read(),
                    file_name=display_name,
                    mime="video/mp4" if is_mp4 else "audio/mpeg",
                    type="primary",
                    use_container_width=True,
                    key="final_download_btn"
                )
            
            st.components.v1.html("""
                <script>
                    setTimeout(function() {
                        const buttons = window.parent.document.querySelectorAll('button');
                        for (const button of buttons) {
                            if (button.innerText.includes('바탕화면에 저장')) {
                                button.click();
                                break;
                            }
                        }
                    }, 500);
                </script>
            """, height=0)
        
        with col_dl_2:
            if st.button("🔄 새로 작업하기"):
                st.session_state.process_complete = False
                st.session_state.final_file_path = None
                st.rerun()
            
    # [HISTORY] Latest generation check
    st.markdown("---")
    final_output = get_latest_master_mp4()
    if not final_output:
        # Try finding latest mixed MP3 if no MP4 exists
        mp3_folders = [os.path.join(DOWNLOADS_DIR, f) for f in os.listdir(DOWNLOADS_DIR) if "합본" in f]
        if mp3_folders:
            final_output = max(mp3_folders, key=os.path.getmtime)

    if final_output and not st.session_state.process_complete:
        st.subheader("📥 최근 작업물 (기존 파일 가져오기)")
        f_display = os.path.basename(final_output)
        with open(final_output, "rb") as f:
             st.download_button(
                label=f"📥 {f_display} 다운로드",
                data=f.read(),
                file_name=f_display,
                mime="video/mp4" if f_display.endswith(".mp4") else "audio/mpeg",
                use_container_width=True
            )

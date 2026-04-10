import streamlit as st
import os
import json
import subprocess
import sys
import time

# [Paths]
# [Paths]
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# If app.py is in a subfolder (e.g. WebUI), we assume the project root is one level up
PROJECT_ROOT = os.path.dirname(BASE_DIR) if os.path.basename(BASE_DIR) == "WebUI" else BASE_DIR

CONFIG_PATH = os.path.join(PROJECT_ROOT, "config.json")
SCRIPT_PATH = os.path.join(BASE_DIR, "SCRIPT_INPUT.txt")

# [Page Config]
st.set_page_config(
    page_title="무협 비디오 생성기",
    page_icon="🐉",
    layout="wide"
)

# [Helper: Find Latest Video]
def get_latest_video():
    # 1. Desktop Check (Priority)
    desktop_dir = os.path.join(os.path.expanduser("~"), "Desktop")
    # Search recursively for "무협_최종_합본_마스터" in subfolders of Desktop
    latest_video = None
    latest_time = 0

    # Search in Desktop/무협_생성_* folders
    for root, dirs, files in os.walk(desktop_dir):
        if "무협_생성_" in root:
            for file in files:
                if "무협_최종_합본_마스터" in file and file.endswith(".mp4"):
                    full_path = os.path.join(root, file)
                    mtime = os.path.getmtime(full_path)
                    if mtime > latest_time:
                        latest_time = mtime
                        latest_video = full_path

    # 2. Downloads Check (Fallback)
    if not latest_video:
        downloads_dir = os.path.join(os.path.expanduser("~"), "Downloads")
        for root, dirs, files in os.walk(downloads_dir):
             if "무협_생성_" in root:
                 for file in files:
                    if "무협_최종_합본_마스터" in file and file.endswith(".mp4"):
                        full_path = os.path.join(root, file)
                        mtime = os.path.getmtime(full_path)
                        if mtime > latest_time:
                            latest_time = mtime
                            latest_video = full_path
    
    return latest_video

# [Helper: Load/Save Config]
def load_config():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except: return {}
    return {}

def save_config(eleven, gemini, azure_key, azure_region):
    data = {
        "ElevenLabs_API_KEY": eleven,
        "Gemini_API_KEY": gemini,
        "Azure_Speech_Key": azure_key,
        "Azure_Region": azure_region
    }
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

# [UI Header]
st.title("🐉 무협 비디오 자동 생성기")
st.markdown("---")

# [Tabs]
tab1, tab2 = st.tabs(["🎬 비디오 생성", "⚙️ 설정 (API Key)"])

# --- TAB 1: GENERATOR ---
with tab1:
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("1. 대본 입력")
        
        # Load default script
        default_script = ""
        if os.path.exists(SCRIPT_PATH):
            try:
                with open(SCRIPT_PATH, "r", encoding="utf-8") as f:
                    default_script = f.read()
            except: pass

        script_text = st.text_area(
            "대본을 여기에 붙여넣으세요:", 
            value=default_script, 
            height=300,
            placeholder="최강호 사장. 그는 민수 씨가..."
        )
        
        image_count = st.number_input("생성할 이미지 수량 (0=자동)", min_value=0, value=10, step=1)
        
        # [NEW] Skip TTS Option
        skip_tts = st.checkbox("음성/자막 생성 건너뛰기 (이미지/영상만 생성)", value=False)
        
        generate_btn = st.button("🚀 영상 생성 시작", type="primary", use_container_width=True)

    with col2:
        st.subheader("2. 작업 로그")
        log_container = st.empty()
        
        if generate_btn:
            # Save Script
            try:
                with open(SCRIPT_PATH, "w", encoding="utf-8") as f:
                    f.write(script_text)
            except Exception as e:
                st.error(f"대본 저장 실패: {e}")
                st.stop()

            # Run Process
            logs = []
            log_container.code("작업을 시작합니다...", language="bash")
            
            steps = []
            
            if not skip_tts:
                steps.append(("Step 1: 성우/자막", ["core_v2/engine/muhyup_factory.py", SCRIPT_PATH]))
                steps.append(("Step 1-1: 병합", ["core_v2/01-1_file_merger.py"]))
            else:
                logs.append("⏭️ [Skip] 성우/자막 생성 단계를 건너뜁니다.\n")
            
            steps.extend([
                ("Step 2: 이미지 생성", ["core_v2/02_visual_director_96.py", "--count", str(int(image_count))]),
                ("Step 3: 영상 변환", ["core_v2/03-1_cinematic_v3_vintage.py"]),
                ("Step 4: BGM 믹싱", ["core_v2/04_bgm_master.py"]),
                ("Step 5: 효과음", ["core_v2/05_audio_layer_factory.py"]),
                ("Step 7: 최종 합본", ["core_v2/07_master_integration.py"])
            ])
            
            python_exe = sys.executable
            
            for step_name, cmd in steps:
                logs.append(f"\n🚀 [{step_name}] 시작...")
                log_container.code("".join(logs), language="bash")
                
                full_cmd = [python_exe] + cmd
                
                try:
                    process = subprocess.Popen(
                        full_cmd, 
                        stdout=subprocess.PIPE, 
                        stderr=subprocess.STDOUT, 
                        text=True, 
                        cwd=PROJECT_ROOT,
                        encoding='utf-8',
                        errors='replace'
                    )
                    
                    for line in process.stdout:
                        logs.append(line)
                        # Limit log size to prevent UI freeze
                        if len(logs) > 1000: logs = logs[-1000:]
                        log_container.code("".join(logs), language="bash")
                        
                    process.wait()
                    
                    if process.returncode == 0:
                        logs.append(f"✅ [{step_name}] 완료!\n")
                    else:
                        logs.append(f"❌ [{step_name}] 실패 (Code: {process.returncode})\n")
                        log_container.code("".join(logs), language="bash")
                        st.error("작업 중 오류가 발생했습니다.")
                        break
                        
                except Exception as e:
                    logs.append(f"🔥 오류: {str(e)}\n")
                    log_container.code("".join(logs), language="bash")
                    break
            
            else: # If loop finished without break
                st.success("✨ 모든 작업이 완료되었습니다! 다운로드 폴더를 확인하세요.")
                st.balloons()
            
            # [Download Button Logic]
            final_video_path = get_latest_video()
            if final_video_path and os.path.exists(final_video_path):
                st.markdown("### 📥 결과물 다운로드")
                st.info(f"생성된 파일: {os.path.basename(final_video_path)}")
                try:
                    with open(final_video_path, "rb") as file:
                        btn = st.download_button(
                            label="📥 영상 다운로드하기 (Click)",
                            data=file,
                            file_name=os.path.basename(final_video_path),
                            mime="video/mp4",
                            type="primary"
                        )
                except Exception as e:
                    st.error(f"다운로드 준비 중 오류: {e}")
            else:
                st.warning("⚠️ 생성된 영상을 찾을 수 없습니다. (경로 확인 필요)")

# --- TAB 2: SETTINGS ---
with tab2:
    st.header("API 키 설정")
    conf = load_config()
    
    with st.form("config_form"):
        col_api1, col_api2 = st.columns(2)
        with col_api1:
            api_eleven = st.text_input("ElevenLabs API Key", value=conf.get("ElevenLabs_API_KEY", ""), type="password")
            api_azure = st.text_input("Azure Speech Key", value=conf.get("Azure_Speech_Key", ""), type="password")
        with col_api2:
            api_gemini = st.text_input("Gemini API Key", value=conf.get("Gemini_API_KEY", ""), type="password")
            api_region = st.text_input("Azure Region", value=conf.get("Azure_Region", "koreacentral"))
            
        submitted = st.form_submit_button("💾 설정 저장")
        
        if submitted:
            save_config(api_eleven, api_gemini, api_azure, api_region)
            st.success("키 설정이 저장되었습니다!")

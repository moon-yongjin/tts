import gradio as gr
import os
import json
import subprocess
import sys
import threading
import time

# [Paths]
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CORE_DIR = os.path.join(BASE_DIR, "core_v2")
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")
SCRIPT_PATH = os.path.join(BASE_DIR, "SCRIPT_INPUT.txt")
OUTPUT_DIR = os.path.join(os.path.expanduser("~"), "Downloads")

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
    return "✅ 설정이 저장되었습니다!"

# [Helper: Run Script]
def run_process_step(step_name, command, log_queue=None):
    yield f"🚀 [{step_name}] 시작...\n"
    
    # Python executable verification
    python_exe = sys.executable
    
    full_cmd = [python_exe] + command
    
    try:
        process = subprocess.Popen(
            full_cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.STDOUT, 
            text=True, 
            cwd=BASE_DIR,
            encoding='utf-8',
            errors='replace'
        )
        
        for line in process.stdout:
            yield line
            
        process.wait()
        if process.returncode == 0:
            yield f"✅ [{step_name}] 완료!\n\n"
        else:
            yield f"❌ [{step_name}] 실패 (Exit Code: {process.returncode})\n\n"
            
    except Exception as e:
        yield f"🔥 치명적 오류 발생: {str(e)}\n"

# [Main Logic: Generate All]
def generate_all(script_text, image_count):
    # 1. Save Script
    try:
        # Save as CP949 for Windows compatibility if needed, but UTF-8 is safer for Python internal use
        # However, the core scripts might expect specific encoding.
        # Let's stick to UTF-8 for the system that runs this UI.
        with open(SCRIPT_PATH, "w", encoding="utf-8") as f:
            f.write(script_text)
    except Exception as e:
        yield f"❌ 대본 저장 실패: {str(e)}"
        return

    log_history = ""
    
    steps = [
        ("Step 1: 성우/자막", ["core_v2/engine/muhyup_factory.py", SCRIPT_PATH]),
        ("Step 1-1: 병합", ["core_v2/01-1_file_merger.py"]),
        ("Step 2: 이미지 생성", ["core_v2/02_visual_director_96.py", "--count", str(int(image_count))]),
        ("Step 3: 영상 변환", ["core_v2/03-1_cinematic_v3_vintage.py"]),
        ("Step 4: BGM 믹싱", ["core_v2/04_bgm_master.py"]),
        ("Step 5: 효과음", ["core_v2/05_audio_layer_factory.py"]),
        ("Step 7: 최종 합본", ["core_v2/07_master_integration.py"])
    ]

    for step_name, cmd in steps:
        for log_line in run_process_step(step_name, cmd):
            log_history += log_line
            yield log_history

    yield log_history + "\n✨ 모든 작업이 완료되었습니다!"

# [UI Initializer]
def init_ui():
    conf = load_config()
    default_script = ""
    if os.path.exists(SCRIPT_PATH):
        try:
            with open(SCRIPT_PATH, "r", encoding="utf-8") as f:
                default_script = f.read()
        except: pass

    with gr.Blocks(title="무협 비디오 생성기", theme=gr.themes.Soft()) as app:
        gr.Markdown("# 🐉 무협 비디오 자동 생성기 (Web UI)")
        
        with gr.Tabs():
            # [Tab 1: Main Generator]
            with gr.Tab("🎬 비디오 생성"):
                with gr.Row():
                    with gr.Column(scale=2):
                        script_input = gr.Textbox(
                            label="대본 입력 (여기에 내용을 붙여넣으세요)", 
                            value=default_script, 
                            lines=15,
                            placeholder="최강호 사장. 그는 민수 씨가..."
                        )
                        image_count = gr.Number(label="이미지 생성 개수 (0=자동)", value=10, precision=0)
                        gen_btn = gr.Button("🚀 영상 생성 시작", variant="primary", size="lg")
                    
                    with gr.Column(scale=3):
                        logs = gr.TextArea(label="작업 로그", lines=20, interactive=False, autoscroll=True)
                
                gen_btn.click(generate_all, inputs=[script_input, image_count], outputs=logs)

            # [Tab 2: Settings]
            with gr.Tab("⚙️ 설정 (API Key)"):
                gr.Markdown("### API 키 설정 (config.json)")
                with gr.Row():
                    api_eleven = gr.Textbox(label="ElevenLabs Key", value=conf.get("ElevenLabs_API_KEY", ""), type="password")
                    api_gemini = gr.Textbox(label="Gemini API Key", value=conf.get("Gemini_API_KEY", ""), type="password")
                with gr.Row():
                    api_azure = gr.Textbox(label="Azure Speech Key", value=conf.get("Azure_Speech_Key", ""), type="password")
                    api_region = gr.Textbox(label="Azure Region", value=conf.get("Azure_Region", "koreacentral"))
                
                save_btn = gr.Button("💾 설정 저장")
                status_msg = gr.Textbox(label="상태", interactive=False)
                
                save_btn.click(save_config, inputs=[api_eleven, api_gemini, api_azure, api_region], outputs=status_msg)

    return app

if __name__ == "__main__":
    ui = init_ui()
    # Auto-open browser
    ui.queue().launch(inbrowser=True, server_name="0.0.0.0")

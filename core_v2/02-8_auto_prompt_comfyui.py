import os
import sys
import json
import time
import shutil
import subprocess
import re
import urllib.request
from pathlib import Path
from datetime import timedelta
from google import genai
from google.genai import types

# --- [설정 및 경로] ---
BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent
CONFIG_PATH = ROOT_DIR / "config.json"
GUIDELINES_PATH = BASE_DIR / "whisk_prompt_guidelines.md"
COMFYUI_URL = "http://127.0.0.1:8188"
OUTPUT_DIR = ROOT_DIR / "ComfyUI" / "output"
DOWNLOADS_DIR = Path.home() / "Downloads" / "Script_Scenes_Dynamic"
DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)

# 오류 기록 파일
ERROR_LOG_PATH = BASE_DIR / "error_history.json"

# --- [헬퍼 함수] ---

def load_config():
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Config 로드 실패: {e}")
        return {}

def get_error_history():
    if ERROR_LOG_PATH.exists():
        try:
            with open(ERROR_LOG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return []
    return []

def save_error_history(history):
    with open(ERROR_LOG_PATH, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

def check_comfyui_alive():
    try:
        urllib.request.urlopen(f"{COMFYUI_URL}/system_stats", timeout=2)
        return True
    except:
        return False

def check_consecutive_errors(error_msg):
    history = get_error_history()
    if history and (error_msg in history[-1] or history[-1] in error_msg):
        print("\n" + "!" * 50)
        print("🚨 동일/유사 오류가 2회 연속 발생했습니다!")
        print(f"현재 오류: {error_msg}")
        print("지침에 따라 실행을 중단하고 사용자와 상의합니다.")
        print("!" * 50)
        sys.exit(1)
    
    history.append(error_msg)
    if len(history) > 10: history.pop(0)
    save_error_history(history)

# --- [STT 파트: MLX-Whisper] ---

def format_timestamp(seconds):
    td = timedelta(seconds=seconds)
    total_seconds = int(td.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60
    milliseconds = int(td.microseconds / 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{milliseconds:03d}"

def split_subtitle_text(text, max_len=12):
    words = text.split()
    chunks = []
    current_chunk = []
    current_len = 0
    for word in words:
        if len(word) > max_len:
            if current_chunk:
                chunks.append(" ".join(current_chunk))
                current_chunk = []
                current_len = 0
            for i in range(0, len(word), max_len):
                chunks.append(word[i:i+max_len])
            continue
        add_len = len(word) + (1 if current_chunk else 0)
        if current_len + add_len > max_len:
            chunks.append(" ".join(current_chunk))
            current_chunk = [word]
            current_len = len(word)
        else:
            current_chunk.append(word)
            current_len += add_len
    if current_chunk:
        chunks.append(" ".join(current_chunk))
    return chunks

def transcribe_file(file_path):
    print(f"📝 [STEP 1] 자막 생성 및 받아쓰기 시작 (MLX-Whisper)...")
    try:
        import mlx_whisper
    except ImportError:
        check_consecutive_errors("mlx_whisper 라이브러리가 설치되어 있지 않습니다.")
        return None, None
    model_name = "mlx-community/whisper-large-v3-turbo"
    base_name = Path(file_path).stem
    try:
        result = mlx_whisper.transcribe(str(file_path), path_or_hf_repo=model_name, language="ko")
        if not result.get("segments"):
            check_consecutive_errors("자막 추출 결과가 비어있습니다.")
            return None, None
        transcript = result["text"].strip()
        srt_content = ""
        global_count = 1
        for segment in result.get("segments", []):
            full_text = segment["text"].strip()
            start_time = segment["start"]
            end_time = segment["end"]
            duration = end_time - start_time
            sub_chunks = split_subtitle_text(full_text, max_len=12)
            if len(sub_chunks) <= 1:
                srt_content += f"{global_count}\n{format_timestamp(start_time)} --> {format_timestamp(end_time)}\n{full_text}\n\n"
                global_count += 1
            else:
                total_chars = sum(len(c) for c in sub_chunks)
                current_start = start_time
                for chunk in sub_chunks:
                    chunk_ratio = len(chunk) / total_chars
                    current_end = current_start + (duration * chunk_ratio)
                    srt_content += f"{global_count}\n{format_timestamp(current_start)} --> {format_timestamp(current_end)}\n{chunk}\n\n"
                    current_start = current_end
                    global_count += 1
        srt_path = DOWNLOADS_DIR / f"{base_name}_{int(time.time())}.srt"
        with open(srt_path, "w", encoding="utf-8") as f:
            f.write(srt_content)
        print(f"✅ 자막 생성 완료: {srt_path.name}")
        return srt_content, srt_path
    except Exception as e:
        check_consecutive_errors(f"Transcription Error: {str(e)}")
        return None, None

# --- [프롬프트 생성 파트: Gemini] ---

def get_prompts_from_gemini(transcript):
    print(f"🤖 [STEP 2] 프롬프트 추출 중 (Gemini)...")
    config = load_config()
    api_keys = [config.get("Gemini_API_KEY"), config.get("Gemini_API_KEY_2"), config.get("Gemini_API_KEY_3")]
    api_keys = [k for k in api_keys if k]
    if not api_keys:
        check_consecutive_errors("사용 가능한 Gemini API Key가 없습니다.")
        return []

    input_dir = Path(os.environ.get("CURRENT_INPUT_DIR", BASE_DIR))
    potential_guidelines = [
        input_dir / f"{os.environ.get('CURRENT_INPUT_STEM')}_guidelines.md",
        input_dir / "guidelines.md",
        GUIDELINES_PATH
    ]
    guidelines = ""
    for path in potential_guidelines:
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                guidelines = f.read()
                print(f"📗 지침 적용: {path.name}")
                break
    
    prompt = f"""
    당신은 거칠고 표현력이 강한 '수채화 화가' 스타일의 프롬프트 엔지니어입니다.
    오직 아래 [자막 대본]의 **실제 내용과 흐름**에만 기반하여 이미지 프롬프트를 생성하십시오.
    
    [핵심 지침]
    1. **일상적 외로움 (Mundane Loneliness)**: 초현실적이고 거대한 비유보다는 **'평범한 일상을 살아가며 느끼는 문득문득한 외로움'**에 집중하십시오. (예: 만원 지하철 창에 비친 멍한 얼굴, 혼자 차려 먹는 정갈하지만 쓸쓸한 식탁, 비 오는 거리에서 든 우산 등)
    2. **내면의 위축 (Lack of Confidence)**: 대놓고 슬픈 표정보다는 **살짝 굽은 어깨, 먼 곳을 응시하는 시선, 사람들 틈에서 조금은 어색해 보이는 성인의 뒷모습** 등으로 '자신감 결여'를 섬세하게 묘사하십시오.
    3. **연령 및 의상 제한**: **아기/어린이/한복 절대 금지.** 반드시 세련된 현대식 의상을 입은 한국인 성인으로만 묘사하십시오. 어린 시절 이야기도 성인의 관찰이나 소품을 통한 회상으로만 풀어내십시오.
    4. **수량 고정**: 반드시 정확히 14개의 시각적 장면을 생성하십시오.
    5. **글자 금지**: **화면 내에 어떠한 글씨, 자막, 텍스트, 간판, 낙서도 나타나지 않게 하십시오.** 이미지 자체에 텍스트 요소를 절대 포함하지 마십시오.
    6. **스타일**: Watercolor painting, rough brushstrokes, modern casual vibe, melancholic yet realistic atmosphere.
    7. **형식**: 모든 프롬프트는 'Watercolor painting'으로 시작하고 "1:1 aspect ratio, square composition, no text, no subtitles"으로 끝나야 합니다.
    8. **언어**: 프롬프트는 영어로 작성하십시오.
    
    [가이드라인]
    {guidelines}
    
    [자막 대본 (SRT)]
    {transcript}
    
    [응답 형식: 오직 JSON 리스트로만 응답]
    """

    for i, key in enumerate(api_keys):
        try:
            client = genai.Client(api_key=key)
            response = client.models.generate_content(
                model='gemini-2.0-flash',
                contents=prompt,
                config=types.GenerateContentConfig(response_mime_type='application/json')
            )
            prompts = json.loads(response.text)
            print(f"✨ {len(prompts)}개의 프롬프트 추출 완료.")
            return prompts
        except Exception as e:
            print(f"⚠️ API Key #{i+1} 실패... ({str(e)})")
    return []

# --- [ComfyUI 파트] ---

def queue_prompt(prompt_workflow):
    p = {"prompt": prompt_workflow}
    data = json.dumps(p).encode('utf-8')
    req = urllib.request.Request(f"{COMFYUI_URL}/prompt", data=data)
    try:
        return json.loads(urllib.request.urlopen(req).read())
    except Exception as e:
        check_consecutive_errors(f"ComfyUI Connection Error: {str(e)}")
        return None

def push_to_comfyui(prompts):
    print(f"🚀 [STEP 3] ComfyUI로 프롬프트 전송 시작 (총 {len(prompts)}개)...")
    workflow_template = {
      "12": {"inputs": {"unet_name": "z_image_turbo-Q5_K_M.gguf"}, "class_type": "UnetLoaderGGUF"},
      "13": {"inputs": {"clip_name": "qwen_3_4b_fp8_mixed.safetensors", "type": "qwen_image", "device": "default"}, "class_type": "CLIPLoader"},
      "15": {"inputs": {"vae_name": "ae.safetensors"}, "class_type": "VAELoader"},
      "11": {"inputs": {"width": 640, "height": 640, "batch_size": 1}, "class_type": "EmptySD3LatentImage"},
      "18": {"inputs": {"text": "", "clip": ["13", 0]}, "class_type": "CLIPTextEncode"},
      "10": {"inputs": {"text": "foreigner, westerner, caucasian, blonde, hanbok, traditional dress, baby, infant, child, kid, text, watermark, low quality, blurry, subtitles, word, letter, alphabet, sign, signage, writing", "clip": ["13", 0]}, "class_type": "CLIPTextEncode"},
      "16": {"inputs": {"seed": 101, "steps": 6, "cfg": 1.0, "sampler_name": "euler", "scheduler": "simple", "denoise": 1.0, "model": ["12", 0], "positive": ["18", 0], "negative": ["10", 0], "latent_image": ["11", 0]}, "class_type": "KSampler"},
      "17": {"inputs": {"samples": ["16", 0], "vae": ["15", 0]}, "class_type": "VAEDecode"},
      "9": {"inputs": {"filename_prefix": "AutoGen", "images": ["17", 0]}, "class_type": "SaveImage"}
    }

    for i, p_text in enumerate(prompts):
        wf = json.loads(json.dumps(workflow_template))
        wf["18"]["inputs"]["text"] = p_text
        wf["16"]["inputs"]["seed"] = int(time.time() % 100000) + i
        wf["9"]["inputs"]["filename_prefix"] = f"AutoGen_{i:02d}"
        print(f"   [Queue] Scene {i+1}...")
        if not queue_prompt(wf): break
        time.sleep(0.5)

def main():
    if len(sys.argv) < 2:
        print("❌ 사용법: python 02-8_auto_prompt_comfyui.py <파일경로>")
        sys.exit(1)
    input_file = sys.argv[1]
    if not os.path.exists(input_file):
        print(f"❌ 파일을 찾을 수 없습니다: {input_file}")
        sys.exit(1)
    if not check_comfyui_alive():
        check_consecutive_errors("ComfyUI 서버 접근 불가.")
    
    os.environ["CURRENT_INPUT_DIR"] = str(Path(input_file).parent)
    os.environ["CURRENT_INPUT_STEM"] = Path(input_file).stem

    transcript, srt_path = transcribe_file(input_file)
    if not transcript: return

    prompts = get_prompts_from_gemini(transcript)
    if not prompts: return

    push_to_comfyui(prompts)
    save_error_history([])
    print(f"\n✨ 파이프라인 완료!")

if __name__ == "__main__":
    main()

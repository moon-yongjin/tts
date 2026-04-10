import os
import shutil
import time
import re
import json
from gradio_client import Client, handle_file
from pathlib import Path
from pydub import AudioSegment
import google.generativeai as genai

# ==========================================================
# [사용자 설정 구역]
# ==========================================================
PROJ_ROOT = Path("/Users/a12/projects/tts")
CORE_V2 = PROJ_ROOT / "core_v2"
DOWNLOAD_DIR = Path.home() / "Downloads"
SFX_DIR = CORE_V2 / "Library" / "sfx"

# 1. 참조 오디오
REF_AUDIO_PATH = CORE_V2 / "supertone_cloned_test.wav"

# 2. 대본 및 출력 설정
SCRIPT_PATH = PROJ_ROOT / "대본.txt"
OUTPUT_FILENAME = "Qwen_Cloning_Final.wav"
OUTPUT_PATH = DOWNLOAD_DIR / OUTPUT_FILENAME

# 3. 모델 설정
SPACE_ID = "furaidosu/Qwen3-TTS"
INSTRUCT = "신뢰감 있는 뉴스 아나운서 톤으로 정갈하고 힘 있게 낭독하세요."

# 4. API 설정 (SFX 용)
CONFIG_PATH = PROJ_ROOT / "config.json"
# ==========================================================

def load_gemini_key():
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                config = json.load(f)
                return config.get("Gemini_API_KEY")
        except: pass
    return None

def split_text(text, max_len=150):
    """문장 단위로 텍스트 분할"""
    sentences = re.split(r'([.!?]\s*)', text)
    chunks = []
    current_chunk = ""
    for i in range(0, len(sentences), 2):
        sentence = sentences[i]
        punctuation = sentences[i+1] if i+1 < len(sentences) else ""
        full_sentence = sentence + punctuation
        if len(current_chunk) + len(full_sentence) <= max_len:
            current_chunk += full_sentence
        else:
            if current_chunk: chunks.append(current_chunk.strip())
            current_chunk = full_sentence
    if current_chunk:
        chunks.append(current_chunk.strip())
    return [c for c in chunks if c]

def format_srt_time(ms):
    s, ms = divmod(ms, 1000)
    m, s = divmod(s, 60)
    h, m = divmod(m, 60)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

def pick_sfx_ai(model, text_chunk, sfx_list):
    if not text_chunk.strip() or not sfx_list: return None
    
    names = ", ".join([os.path.splitext(f)[0] for f in sfx_list])
    prompt = f"""
    뉴스/다큐멘터리 오디오 디렉터로서, 다음 지문에 가장 어울리는 효과음(SFX)을 선택하세요.
    [지문] "{text_chunk}"
    [SFX 목록] {names}
    [가이드] 
    1. 지문의 분위기나 동작을 살릴 소리를 하나 고르세요. 없으면 'None'이라고 하세요.
    2. 부연 설명 없이 확장자 제외 파일명만 딱 하나 답변하세요.
    """
    try:
        response = model.generate_content(prompt)
        choice = response.text.strip().lower()
        if "none" in choice: return None
        for f in sfx_list:
            if os.path.splitext(f)[0].lower() in choice:
                return f
    except: pass
    return None

def run_cloning_with_sfx():
    if not REF_AUDIO_PATH.exists():
        print(f"❌ 참조 오디오를 찾을 수 없습니다: {REF_AUDIO_PATH}")
        return

    if not SCRIPT_PATH.exists():
        print(f"❌ 대본 파일을 찾을 수 없습니다: {SCRIPT_PATH}")
        return

    # API 키 로드
    gemini_key = load_gemini_key()
    model = None
    if gemini_key:
        genai.configure(api_key=gemini_key)
        model = genai.GenerativeModel('gemini-2.0-flash')
        print("🔑 Gemini API 로드 완료 (자동 SFX 활성화)")

    with open(SCRIPT_PATH, "r", encoding="utf-8") as f:
        text_content = f.read().strip()

    chunks = split_text(text_content)
    print(f"🚀 [Qwen-Cloning] 총 {len(chunks)}개 파트로 나누어 생성 시작...")
    
    client = Client(SPACE_ID)
    combined_audio = AudioSegment.empty()
    srt_entries = []
    current_ms = 0
    
    for i, chunk in enumerate(chunks):
        print(f"🎙️  [{i+1}/{len(chunks)}] 파트 생성 중: {chunk[:30]}...")
        success = False
        retries = 2
        
        while not success and retries >= 0:
            try:
                result = client.predict(
                    chunk, "Korean", handle_file(str(REF_AUDIO_PATH)),
                    INSTRUCT, "1.7B", api_name="/generate_voice_clone"
                )
                audio_temp_path = result[0]
                if audio_temp_path and os.path.exists(audio_temp_path):
                    part_audio = AudioSegment.from_wav(audio_temp_path)
                    duration = len(part_audio)
                    
                    # SRT 엔트리 추가
                    start_time = format_srt_time(current_ms)
                    end_time = format_srt_time(current_ms + duration)
                    srt_entries.append(f"{i+1}\n{start_time} --> {end_time}\n{chunk}\n")
                    
                    combined_audio += part_audio
                    current_ms += duration
                    success = True
                    print(f"   ✅ 파트 {i+1} 완료.")
                else:
                    retries -= 1
                    time.sleep(2)
            except Exception as e:
                retries -= 1
                time.sleep(2)
        
        if not success: break

    if len(combined_audio) > 0:
        # 1. SRT 저장
        srt_path = OUTPUT_PATH.with_suffix(".srt")
        with open(srt_path, "w", encoding="utf-8") as f:
            f.writelines("\n".join(srt_entries))
        print(f"📝 자막 생성 완료: {srt_path}")

        # 2. SFX 오버레이 (Gemini 활성화 시)
        if model and SFX_DIR.exists():
            print("🔊 AI SFX 자동 믹싱 시작...")
            sfx_files = [f for f in os.listdir(SFX_DIR) if f.lower().endswith(('.mp3', '.wav'))]
            last_sfx_time = -10000
            sfx_count = 0
            
            # SRT 정보를 바탕으로 SFX 배치
            current_pos = 0
            for i, chunk in enumerate(chunks):
                # 10초 간격 유지
                if current_pos - last_sfx_time >= 10000:
                    sfx_file = pick_sfx_ai(model, chunk, sfx_files)
                    if sfx_file:
                        try:
                            sfx_path = SFX_DIR / sfx_file
                            sfx_audio = AudioSegment.from_file(sfx_path).normalize() - 15
                            if len(sfx_audio) > 5000: sfx_audio = sfx_audio[:5000].fade_out(1000)
                            combined_audio = combined_audio.overlay(sfx_audio, position=current_pos)
                            print(f"   🔔 SFX 추가: {sfx_file} (@ {current_pos/1000:.1f}s)")
                            sfx_count += 1
                            last_sfx_time = current_pos
                        except: pass
                
                # 다음 위치로 이동 (대략적인 오디오 길이 반영을 위해 실제 생성 결과를 써야함)
                # 여기서는 chunks와 srt_entries가 1:1 대응하므로 srt_entries의 시간을 파싱하거나
                # 위 생성 루프에서 sfx를 바로 넣는게 정확함. 
                # 하지만 구조상 여기서 하는게 깔끔하므로 srt_entries에서 시간을 가져옴.
                try:
                    time_line = srt_entries[i].split('\n')[1]
                    start_str = time_line.split(' --> ')[0]
                    h, m, s_ms = start_str.split(':')
                    s, ms = s_ms.split(',')
                    current_pos = (int(h)*3600 + int(m)*60 + int(s))*1000 + int(ms)
                except: pass

        combined_audio.export(OUTPUT_PATH, format="wav")
        print(f"\n✨ 모든 작업 완료! 결과 파일: {OUTPUT_PATH}")
    else:
        print("\n❌ 오디오 생성 실패.")

if __name__ == "__main__":
    run_cloning_with_sfx()

import os
import re
import sys
import json
import time
from pydub import AudioSegment
import google.generativeai as genai

# [경로 설정]
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(BASE_DIR)
DOWNLOADS_DIR = os.path.join(os.path.expanduser("~"), "Downloads")
LIB_DIR = os.path.join(BASE_DIR, "Library")
SFX_DIR = os.path.join(LIB_DIR, "sfx")
BGM_DIR = os.path.join(LIB_DIR, "bgm")

# [API Key Pool & Rotation]
class GeminiPool:
    def __init__(self, primary_key, additional_keys_path):
        self.keys = [primary_key]
        if os.path.exists(additional_keys_path):
            try:
                with open(additional_keys_path, "r", encoding="utf-8") as f:
                    api_data = json.load(f)
                    for k, v in api_data.items():
                        if "GEMINI" in k.upper() and v not in self.keys:
                            self.keys.append(v)
            except: pass
        
        self.current_idx = 0
        self.configure_current()
        print(f"🔑 [API Pool] 총 {len(self.keys)}개의 Gemini 키가 로드되었습니다.")

    def configure_current(self):
        genai.configure(api_key=self.keys[self.current_idx])
        self.model = genai.GenerativeModel('gemini-2.0-flash')

    def rotate(self):
        self.current_idx = (self.current_idx + 1) % len(self.keys)
        self.configure_current()
        print(f"🔄 [API Rotation] 키를 교체합니다. (Key index: {self.current_idx})")

# [Config 로드 및 Pool 초기화]
PRIMARY_KEY = None
CONFIG_PATH = os.path.join(ROOT_DIR, "config.json")
API_KEYS_PATH = os.path.join(BASE_DIR, "api_keys.json")
AUDIO_SETTINGS = {}

if os.path.exists(CONFIG_PATH):
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            config = json.load(f)
            PRIMARY_KEY = config.get("Gemini_API_KEY")
            AUDIO_SETTINGS = config.get("audio_settings", {})
    except: pass

if not PRIMARY_KEY:
    print("❌ 기본 Gemini API Key를 찾을 수 없습니다."); sys.exit(1)

pool = GeminiPool(PRIMARY_KEY, API_KEYS_PATH)

def get_latest_full_narration():
    """가장 최근에 생성된 원본 합본 음성을 찾습니다."""
    # [개선] 더 넓은 범위의 파일명을 찾도록 필터 완화 (.wav 지원)
    candidates = [os.path.join(DOWNLOADS_DIR, f) for f in os.listdir(DOWNLOADS_DIR) 
                  if f.lower().endswith((".mp3", ".wav")) 
                  and "-reverted-" not in f
                  and "_V3-" not in f
                  and "_AI_SFX" not in f
                  and not f.startswith(".")]
    
    if not candidates: return None
    
    # 1순위: _Full_Merged 나 대본_Stable_ 이 포함된 것 우선
    priority = [c for c in candidates if "_Full_Merged" in os.path.basename(c) or "대본_Stable_" in os.path.basename(c)]
    if priority: return max(priority, key=os.path.getmtime)
    
    # 2순위: 그냥 가장 최신 파일
    return max(candidates, key=os.path.getmtime)

def clean_script(text):
    text = re.sub(r'\[(BGM|묘사|지문|설명|배경|음악|CHAPTER|챕터|SFX|효과음):?.*?\]', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\(.*?\)', '', text)
    return text.strip()

def get_audio_list(dir_path):
    if not os.path.exists(dir_path): return []
    return [f for f in os.listdir(dir_path) if f.lower().endswith((".mp3", ".wav"))]

# [기록 및 중복 방지]
selection_history = {"SFX": [], "BGM": []}

def pick_audio_ai(text_chunk, file_list, audio_type="SFX", retry_limit=3):
    if not text_chunk.strip(): return None
    
    # 셔플링하여 AI에게 매번 다른 순서로 보여줌
    import random
    import copy
    shuffled_list = copy.deepcopy(file_list)
    random.shuffle(shuffled_list)
    names = ", ".join([os.path.splitext(f)[0] for f in shuffled_list])
    
    # 최근 사용된 항목은 피하도록 유도
    history_limit = 10 if audio_type == "SFX" else 2
    recent_list = selection_history[audio_type][-history_limit:]
    recent = ", ".join([os.path.splitext(x)[0] for x in recent_list])
    blacklist_hint = f"\n(최근 사용된 항목: {recent} - **절대로** 똑같은 소리를 연속해서 쓰지 말고, 목록에 있는 다른 다양한 소리를 사용하세요.)" if recent else ""

    if audio_type == "SFX":
        instruction = f"목록에는 무려 {len(shuffled_list)}개의 다양한 효과음이 있습니다. 지문의 동작(발걸음, 칼소리, 문소리, 숨소리 등)뿐만 아니라 '분위기(바람, 새소리, 천둥 등)'를 살릴 수 있는 소리를 아주 적극적으로, 풍부하게 골라주세요."
    else:
        instruction = "지문의 전반적인 감정과 긴장도에 어울리는 배경음악을 선택해주세요."

    prompt = f"""
동화/무협 드라마의 오디오 디렉터로서, 다음 지문에 가장 어울리는 {audio_type}를 선택하세요.

[지문]
"{text_chunk}"

[{audio_type} 목록]
{names}
{blacklist_hint}

[가이드라인]
1. {instruction}
2. 반드시 목록에 있는 파일명만 정확히 답변하세요 (확장자 제외).
3. "NONE"은 정말로 어떠한 소리도 어울리지 않을 때만 사용하되, 가급적이면 분위기를 띄울 수 있는 소리를 목록에서 하나 반드시 선택하세요.
4. 부연 설명 없이 파일명만 단답형으로 출력하세요.
"""
    for attempt in range(retry_limit):
        try:
            # Temperature를 0.7로 높게 설정하여 다양성 극대화
            response = pool.model.generate_content(prompt, generation_config=genai.types.GenerationConfig(temperature=0.7))
            choice = response.text.strip().replace("'", "").replace('"', '').lower()
            if "none" in choice: return None
            
            for f in shuffled_list:
                fname = os.path.splitext(f)[0].lower()
                if fname == choice or (len(choice) >= 4 and choice in fname) or (len(fname) >= 4 and fname in choice):
                    selection_history[audio_type].append(f)
                    return f
            return None
        except Exception as e:
            if "429" in str(e) or "Resource exhausted" in str(e):
                pool.rotate()
                time.sleep(1 + attempt)
                continue
            return None
    return None

def srt_time_to_ms(time_str):
    h, m, s_ms = time_str.split(':')
    s, ms = s_ms.split(',')
    return (int(h) * 3600 + int(m) * 60 + int(s)) * 1000 + int(ms)

def parse_srt(srt_path):
    if not srt_path or not os.path.exists(srt_path): return []
    events = []
    with open(srt_path, 'r', encoding='utf-8-sig') as f:
        content = f.read()
    blocks = re.split(r'\n\s*\n', content.strip())
    for block in blocks:
        lines = block.splitlines()
        if len(lines) >= 3:
            times = re.findall(r'(\d{2}:\d{2}:\d{2},\d{3})', lines[1])
            if len(times) >= 2:
                start_ms = srt_time_to_ms(times[0])
                end_ms = srt_time_to_ms(times[1])
                text = " ".join(lines[2:])
                events.append({'start_ms': start_ms, 'end_ms': end_ms, 'text': text})
    return events

def run_ai_director_v3_7():
    print("🎬 [AI SFX & BGM Director V3-9] 정밀 배치 시작")
    
    # [Config] 설정값 로드
    sfx_interval_ms = AUDIO_SETTINGS.get("sfx_interval", 10) * 1000
    bgm_interval_ms = AUDIO_SETTINGS.get("bgm_interval", 30) * 1000
    sfx_vol_offset = AUDIO_SETTINGS.get("sfx_volume_offset", -10)
    bgm_vol_offset = AUDIO_SETTINGS.get("bgm_volume_offset", -30)

    base_audio_path = get_latest_full_narration()
    if not base_audio_path:
        print("❌ 마스터 음성 파일을 찾을 수 없습니다."); return
    
    print(f"🎤 대상 음성: {os.path.basename(base_audio_path)}")
    
    # 대응하는 SRT 파일 찾기
    srt_path = base_audio_path.rsplit('.', 1)[0] + ".srt"
    if not os.path.exists(srt_path):
        # 최신 SRT 중 가장 비슷한 것 찾기
        all_srt = [os.path.join(DOWNLOADS_DIR, f) for f in os.listdir(DOWNLOADS_DIR) if f.lower().endswith(".srt")]
        if all_srt:
            srt_path = max(all_srt, key=os.path.getmtime)
    
    if not os.path.exists(srt_path):
        print("❌ 자막(SRT) 파일을 찾을 수 없습니다."); return
    
    print(f"📝 자막 분석 중: {os.path.basename(srt_path)}")
    srt_events = parse_srt(srt_path)
    
    # [개선] from_file로 wav/mp3 공용 지원
    base_audio = AudioSegment.from_file(base_audio_path)
    audio_duration_ms = len(base_audio)
    
    sfx_list = get_audio_list(SFX_DIR)
    bgm_list = get_audio_list(BGM_DIR)
    final_audio = base_audio

    # --- [BGM Pass] ---
    print(f"🎸 BGM 배치 중 ({bgm_interval_ms/1000:.1f}s 간격)...")
    bgm_count = 0
    last_bgm_time = -bgm_interval_ms - 10000 
    
    for i, event in enumerate(srt_events):
        current_time = event['start_ms']
        if current_time - last_bgm_time < bgm_interval_ms: continue
        
        chunk_text = event['text']
        if i + 1 < len(srt_events): chunk_text += " " + srt_events[i+1]['text']
        
        bgm_file = pick_audio_ai(chunk_text, bgm_list, "BGM")
        if bgm_file:
            bgm_path = os.path.join(BGM_DIR, bgm_file)
            try:
                raw_bgm = AudioSegment.from_file(bgm_path)
                normalized_bgm = raw_bgm.normalize(headroom=2.0)
                bgm_audio = normalized_bgm + bgm_vol_offset

                duration_needed = bgm_interval_ms 
                if i + 5 < len(srt_events):
                    duration_needed = srt_events[i+5]['start_ms'] - current_time
                
                duration_needed = min(duration_needed, audio_duration_ms - current_time)
                if duration_needed < 1000: continue

                bgm_seg = (bgm_audio * (duration_needed // len(bgm_audio) + 1))[:duration_needed]
                bgm_seg = bgm_seg.fade_in(2000).fade_out(2000)
                final_audio = final_audio.overlay(bgm_seg, position=current_time)
                print(f"   🎸 BGM: {bgm_file} @ {current_time/1000:.1f}s (Vol: {bgm_vol_offset}dB)")
                bgm_count += 1
                last_bgm_time = current_time
            except: pass

    # --- [SFX Pass] ---
    print(f"🔊 SFX 배치 중 ({sfx_interval_ms/1000:.1f}s 간격)...")
    sfx_count = 0
    last_sfx_time = -sfx_interval_ms
    
    for event in srt_events:
        current_time = event['start_ms']
        if current_time - last_sfx_time < sfx_interval_ms: continue
        
        sfx_file = pick_audio_ai(event['text'], sfx_list, "SFX")
        if sfx_file:
            sfx_path = os.path.join(SFX_DIR, sfx_file)
            try:
                raw_sfx = AudioSegment.from_file(sfx_path)
                normalized_sfx = raw_sfx.normalize(headroom=1.0)
                sfx_audio = normalized_sfx + sfx_vol_offset

                if len(sfx_audio) > 5000: sfx_audio = sfx_audio[:5000].fade_out(1000)
                
                final_audio = final_audio.overlay(sfx_audio, position=current_time)
                print(f"   🔊 SFX: {sfx_file} @ {current_time/1000:.1f}s (Vol: {sfx_vol_offset}dB)")
                sfx_count += 1
                last_sfx_time = current_time
            except: pass

    # 저장
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    base_name = os.path.basename(base_audio_path).rsplit('.', 1)[0].split("_V3")[0].split("_AI_SFX")[0]
    # 확장자는 mp3로 변환하여 출력 (용량 및 호환성)
    output_filename = f"{base_name}_SFX_V3-9_{timestamp}.mp3"
    output_path = os.path.join(DOWNLOADS_DIR, output_filename)
    
    final_audio = final_audio.normalize(headroom=0.1)
    final_audio.export(output_path, format="mp3", bitrate="192k")
    print(f"🏁 최종 결과물: {output_path} (BGM:{bgm_count}, SFX:{sfx_count})")

if __name__ == "__main__":
    run_ai_director_v3_7()

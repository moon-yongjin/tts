import os
import re
import sys
import json
import time
import requests
from pydub import AudioSegment

# [경로 설정]
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(BASE_DIR)
DOWNLOADS_DIR = os.path.join(os.path.expanduser("~"), "Downloads")
LIB_DIR = os.path.join(BASE_DIR, "Library")
SFX_DIR = os.path.join(LIB_DIR, "sfx")

# [LM Studio 설정]
LM_STUDIO_URL = "http://127.0.0.1:1234/v1/chat/completions"
MODEL_ID = "qwen/qwen2.5-vl-7b"

# [Config 로드]
AUDIO_SETTINGS = {}
CONFIG_PATH = os.path.join(ROOT_DIR, "config.json")

if os.path.exists(CONFIG_PATH):
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            config = json.load(f)
            AUDIO_SETTINGS = config.get("audio_settings", {})
    except: pass

def get_latest_full_narration():
    """가장 최근에 생성된 원본 합본 음성을 찾습니다."""
    candidates = [os.path.join(DOWNLOADS_DIR, f) for f in os.listdir(DOWNLOADS_DIR) 
                  if f.lower().endswith((".mp3", ".wav")) 
                  and "-reverted-" not in f
                  and "_V3-" not in f
                  and "_LOCAL_ONLY_V4" not in f
                  and not f.startswith(".")]
    if not candidates: return None
    
    priority = [c for c in candidates if "_Full_Merged" in os.path.basename(c) or "대본_Stable_" in os.path.basename(c) or "인라인듀얼_결과물_" in os.path.basename(c)]
    if priority: return max(priority, key=os.path.getmtime)
    
    return max(candidates, key=os.path.getmtime)

def clean_script(text):
    text = re.sub(r'\[(BGM|묘사|지문|설명|배경|음악|CHAPTER|챕터|SFX|효과음):?.*?\]', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\(.*?\)', '', text)
    return text.strip()

def get_audio_list(dir_path):
    if not os.path.exists(dir_path): return []
    return [f for f in os.listdir(dir_path) if f.lower().endswith((".mp3", ".wav"))]

selection_history = {"SFX": []}

def pick_audio_ai(text_chunk, file_list, retry_limit=2):
    """100% 로컬 모델(LM Studio)만 사용하여 효과음을 선택합니다."""
    if not text_chunk.strip(): return None
    import random
    import copy
    shuffled_list = copy.deepcopy(file_list)
    random.shuffle(shuffled_list)
    
    # [맥락 필터링] 드라마 장르에 어울리지 않는 소리들 제외
    excluded_keywords = ["motorcycle", "bike", "revving", "skid", "dragon", "tiger", "lion", "sword_clash", "battle", "war_horn", "monster", "magic"]
    filtered_list = []
    for f in shuffled_list:
        fname = os.path.splitext(f)[0].lower()
        if any(k in fname for k in excluded_keywords): continue
        if len(fname) >= 30 and re.match(r'^[0-9a-f]+$', fname): continue
        filtered_list.append(f)
    
    names = ", ".join([os.path.splitext(f)[0] for f in filtered_list])
    
    recent_list = selection_history["SFX"][-15:]
    recent = ", ".join([os.path.splitext(x)[0] for x in recent_list])
    blacklist_hint = f"\n(최근 사용: {recent})" if recent else ""

    prompt = f"""
    당신은 **최고의 현대 휴먼 드라마 오디오 디렉터**입니다. 
    현재 지문은 '변호사와 아내의 사연'이며, 분위기는 **감성적이고 일상적**입니다. 
    비유적 표현(예: 용이 난다, 호랑이 같다)에 속지 말고 **실제 장면의 상황**에 맞는 소리를 고르세요.
    
    [지문] "{text_chunk}"
    [SFX 목록] {names} {blacklist_hint}
    
    [작업 가이드]
    1. 먼저 이 지문의 **상황과 감정**을 한 문장으로 분석하세요. (예: 아내의 헌신적인 사랑, 주인공의 결연한 의지 등)
    2. 그 상황에 가장 어울리는 일상적 소리를 SFX 목록에서 하나만 고르세요.
    3. 적당한 게 없다면 반드시 'none'이라고 하세요.
    4. **답변 형식**: "이유: [분석내용] / 결과: [파일명]" (확장자 제외)
    """
    
    for attempt in range(retry_limit):
        try:
            lm_payload = {
                "model": MODEL_ID,
                "messages": [
                    {"role": "system", "content": "You are a professional audio director for human drama. Analyze the scene first, then provide the filename."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.3 # 더 일관되게
            }
            lm_res = requests.post(LM_STUDIO_URL, json=lm_payload, timeout=30)
            
            if lm_res.status_code == 200:
                raw_res = lm_res.json()['choices'][0]['message']['content'].strip()
                print(f"   💡 [Local Thought] {raw_res.split('/')[0] if '/' in raw_res else raw_res}")
                
                # 결과 부분 추출
                choice = raw_res.split('/')[-1].replace('결과:', '').strip().replace("'", "").replace('"', '').lower()
                
                if "none" in choice:
                    print(f"   💻 [Local LLM] No suitable SFX.")
                    return None
                
                for f in filtered_list:
                    fname = os.path.splitext(f)[0].lower()
                    if fname == choice or (len(choice) >= 3 and choice in fname):
                        selection_history["SFX"].append(f)
                        print(f"   💻 [Local LLM] Selected: {f}")
                        return f
                print(f"   ⚠️ [Local LLM] Choice '{choice}' not matched in list.")
            else:
                print(f"   ⚠️ [Local LLM Error] HTTP {lm_res.status_code}")
        except Exception as e:
            print(f"   ❌ [Local LLM Error] {e}")
            time.sleep(1)
            
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
                events.append({'start_ms': start_ms, 'text': " ".join(lines[2:])})
    return events

def run_sfx_only_director():
    print(f"🎬 [Pure Local SFX Director V4] 100% 로컬 모델 가동 ({MODEL_ID})")
    
    sfx_interval_ms = AUDIO_SETTINGS.get("sfx_interval", 10) * 1000
    sfx_vol_offset = AUDIO_SETTINGS.get("sfx_only_volume_offset", -7)
    ambient_fn = AUDIO_SETTINGS.get("ambient_sound", "coffee_shop.mp3")
    ambient_vol = AUDIO_SETTINGS.get("ambient_volume_offset", -30)

    base_audio_path = get_latest_full_narration()
    if not base_audio_path:
        print("❌ 마스터 음성 파일을 찾을 수 없습니다."); return
    
    print(f"🎤 대상 음성: {os.path.basename(base_audio_path)}")
    srt_path = base_audio_path.rsplit('.', 1)[0] + ".srt"
    
    if not os.path.exists(srt_path):
        all_srt = [os.path.join(DOWNLOADS_DIR, f) for f in os.listdir(DOWNLOADS_DIR) if f.lower().endswith(".srt")]
        if all_srt: srt_path = max(all_srt, key=os.path.getmtime)
    
    if not os.path.exists(srt_path):
        print("❌ 자막(SRT) 파일을 찾을 수 없습니다."); return
    
    print(f"📝 자막 분석 중: {os.path.basename(srt_path)}")
    srt_events = parse_srt(srt_path)
    
    base_audio = AudioSegment.from_file(base_audio_path)
    sfx_list = get_audio_list(SFX_DIR)
    final_audio = base_audio
    
    if ambient_fn:
        print(f"☕ 앰비언트({ambient_fn}) 적용 중 ({ambient_vol}dB)...")
        try:
            ambient_path = os.path.join(SFX_DIR, ambient_fn)
            if os.path.exists(ambient_path):
                ambient_audio = AudioSegment.from_file(ambient_path) + ambient_vol
                total_ms = len(final_audio)
                loop_count = (total_ms // len(ambient_audio)) + 1
                full_ambient = (ambient_audio * loop_count)[:total_ms].fade_in(2000).fade_out(2000)
                final_audio = final_audio.overlay(full_ambient)
        except Exception as e: print(f"   ⚠️ 앰비언트 오류: {e}")

    print(f"🔊 SFX 배치 중 ({sfx_interval_ms/1000:.1f}s 주기)...")
    sfx_count = 0
    last_sfx_time = -sfx_interval_ms
    
    for event in srt_events:
        current_time = event['start_ms']
        # [수정] 첫 30초 동안은 효과음(SFX)을 배치하지 않음 (유저 지침)
        if current_time < 30000: continue
        
        if current_time - last_sfx_time < sfx_interval_ms: continue
        
        sfx_file = pick_audio_ai(event['text'], sfx_list)
        if sfx_file:
            sfx_path = os.path.join(SFX_DIR, sfx_file)
            try:
                raw_sfx = AudioSegment.from_file(sfx_path)
                sfx_audio = raw_sfx.normalize(headroom=1.0) + sfx_vol_offset
                if len(sfx_audio) > 5000: sfx_audio = sfx_audio[:5000].fade_out(1000)
                final_audio = final_audio.overlay(sfx_audio, position=current_time)
                print(f"   🔊 SFX 배치 완료: {sfx_file} @ {current_time/1000:.1f}s")
                sfx_count += 1
                last_sfx_time = current_time
            except: pass

    timestamp = time.strftime("%Y%m%d_%H%M%S")
    base_name = os.path.basename(base_audio_path).rsplit('.', 1)[0].split("_V3")[0]
    output_filename = f"{base_name}_SFX_LOCAL_ONLY_V4_{timestamp}.mp3"
    output_path = os.path.join(DOWNLOADS_DIR, output_filename)
    
    final_audio = final_audio.normalize(headroom=0.1)
    final_audio.export(output_path, format="mp3", bitrate="192k")
    print(f"🏁 최종 결과물 (100% 로컬): {output_path} (SFX:{sfx_count})")

if __name__ == "__main__":
    run_sfx_only_director()

if __name__ == "__main__":
    run_sfx_only_director()

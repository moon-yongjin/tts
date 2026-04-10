import os
import re
import sys
import time
import random
from pydub import AudioSegment

# [설정]
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DOWNLOADS_DIR = os.path.join(os.path.expanduser("~"), "Downloads")
LIB_DIR = os.path.join(BASE_DIR, "Library")
SFX_DIR = os.path.join(LIB_DIR, "sfx")
if not os.path.exists(SFX_DIR):
    SFX_DIR = os.path.join(BASE_DIR, "sfx")

# [고도화] 효과음 중복 방지 히스토리
sfx_history = []
MAX_HISTORY = 30

def get_unique_random_sfx(candidates, history=None):
    if not candidates: return None
    if len(candidates) == 1: return candidates[0]
    
    # 히스토리에 없는 것들 위주로 필터링
    filtered = [c for c in candidates if c not in sfx_history]
    if not filtered: # 다 한 번씩 썼다면 히스토리 초기화 느낌으로 전체에서 선택
        filtered = candidates
        
    choice = random.choice(filtered)
    sfx_history.append(choice)
    if len(sfx_history) > MAX_HISTORY:
        sfx_history.pop(0)
    return choice

def get_latest_srt():
    srt_files = [os.path.join(DOWNLOADS_DIR, f) for f in os.listdir(DOWNLOADS_DIR) 
                 if f.lower().endswith(".srt")]
    if not srt_files: return None
    return max(srt_files, key=os.path.getmtime)

def srt_time_to_ms(srt_time_str):
    h, m, s_ms = srt_time_str.split(':')
    s, ms = s_ms.split(',')
    return (int(h) * 3600 + int(m) * 60 + int(s)) * 1000 + int(ms)

# AI 엔진 연결
sys.path.append(os.path.join(BASE_DIR, "engine"))
try:
    import sfx_generator
except ImportError:
    sfx_generator = None

def parse_sfx_from_srt(srt_path):
    if not os.path.exists(srt_path): return [], 0
    sfx_events = []
    max_ms = 0
    
    with open(srt_path, "r", encoding="utf-8-sig") as f:
        content = f.read().strip()
    
    available_sfx = {}
    if os.path.exists(SFX_DIR):
        for f in os.listdir(SFX_DIR):
            name_no_ext = os.path.splitext(f)[0].lower()
            available_sfx[name_no_ext] = f

    # SRT 블록 찾기
    content = content.replace('\r', '')
    blocks = re.split(r'\n{2,}', content)
    
    # [변경] 전체 텍스트 비율 분석(부정확) -> 자막 블록 단위 정밀 분석(정확)
    
    # 1. 키워드 맵 (sfx_generator에서 가져옴)
    keyword_map = {
        "오토바이": "motorcycle", "바이크": "motorcycle", "엔진": "engine",
        "빗소리": "rain", "비": "rain", "천둥": "thunder", "뇌우": "thunder",
        "발자국": "footstep", "걷는": "footstep", "뛰는": "run",
        "문": "door", "여는": "open", "닫는": "close", "노크": "knock",
        "유리": "glass", "깨지는": "shatter", "파편": "debris",
        "총": "gun", "발사": "shot", "폭발": "explosion", "붐": "boom",
        "칼": "sword", "검": "sword", "휘두르는": "whoosh", "베는": "slash",
        "바람": "wind", "폭풍": "storm", "산들바람": "breeze",
        "물": "water", "강": "river", "파도": "wave", "첨벙": "splash",
        "비명": "scream", "소리치는": "shout", "숨소리": "breath",
        "심장": "heartbeat", "두근": "heartbeat",
        "종": "bell", "시계": "clock", "초침": "tick",
        "불": "fire", "타는": "burn", "장작": "wood",
        "휘익": "휘익", "휙": "휘익", "글씨": "글씨", "띵": "띵",
        "펀치": "펀치", "라쳇": "라쳇", "방구": "방구", "띠롱": "띠롱",
        "찰깍": "찰깍", "깜빡": "깜빡",
    }
    
    # 2. 자막 블록별로 순회하며 태그/키워드 찾기
    for block in blocks:
        lines = block.strip().splitlines()
        if len(lines) >= 3:
            times = re.findall(r'(\d{2}:\d{2}:\d{2},\d{3})', lines[1])
            if times:
                start_ms = srt_time_to_ms(times[0])
                # [수정] max_ms를 자막 막바지 시간으로 업데이트하여 전체 길이 확보
                if len(times) > 1:
                    max_ms = max(max_ms, srt_time_to_ms(times[1]))
                else:
                    max_ms = max(max_ms, start_ms)
                
                text_content = " ".join(lines[2:])
                
                # A. [SFX:...] 태그 찾기
                tag_matches = list(re.finditer(r'\[(SFX|효과음):([^\]]+)\]', text_content))
                
                if tag_matches:
                    for tm in tag_matches:
                        tag_value = tm.group(2).strip()
                        # [변경] 복잡한 시간 계산 제거 -> 그냥 자막 시작 시간에 배치
                        sfx_time = start_ms 
                        
                        # 파일 매칭 시도
                        found_file = None
                        clean_val = sfx_generator.clean_sfx_name(tag_value) if sfx_generator else tag_value
                        
                        # [변경] 단순 1:1 매칭 대신, 다양성을 위해 '유사 파일군' 검색 후 랜덤 선택
                        # 1순위: 직접 매칭 (포함된 파일 검색)
                        candidates = [f for f in available_sfx.values() if clean_val in f.lower()]
                        if candidates:
                             found_file = random.choice(candidates) # 랜덤 선택으로 중복 회피
                        
                        # 2순위: 키워드 매칭 (AI)
                        elif sfx_generator:
                            found_file = sfx_generator.find_best_match_sfx(tag_value, list(available_sfx.values()))
                            if found_file: found_file = found_file[0] if isinstance(found_file, tuple) else found_file

                        if found_file:
                            sfx_events.append({'time': sfx_time, 'file': found_file})

                # B. 키워드 자동 찾기 (태그 없을 때만 실행 -> Rich 모드: 태그 있어도 추가 실행 가능하도록 변경)
                # [사용자 요청] 풍성한 사운드: 한 줄에 여러 개 허용 (break 제거)
                
                found_keywords = []
                for kor, eng in keyword_map.items():
                    # [변경] 단순 포함(in) 대신 정규식을 사용하여 명확히 독립된 단어일 때만 매칭
                    # 한국어 특성상 완벽한 word boundary는 어렵지만, 앞뒤에 문장 부호나 공백 등이 있을 때 우선시
                    pattern = rf'({re.escape(kor)})'
                    matches_in_text = list(re.finditer(pattern, text_content))
                    
                    for m in matches_in_text:
                        k_idx = m.start()
                        
                        # [검증] "비단실", "비웃음" 등에서 "비"만 걸러내는 로직
                        # 키워드 앞뒤 문자가 한글이면 스킵 (예: '비' 앞뒤가 한글이면 단어의 일부로 판단)
                        if len(kor) == 1:
                            if k_idx > 0 and '가' <= text_content[k_idx-1] <= '힣': continue
                            if k_idx + 1 < len(text_content) and '가' <= text_content[k_idx+1] <= '힣': continue

                        sfx_time = start_ms + (k_idx * 120)
                        max_ms = max(max_ms, sfx_time)
                        
                        is_duplicate = False
                        for ev in sfx_events:
                            if abs(ev['time'] - sfx_time) < 1000: # 최소 1초 간격 유지
                                is_duplicate = True
                                break
                        if is_duplicate: continue

                        # [변경] 파일명 매칭 시 단어 경계 확인 (rain 이 train에 매칭되지 않도록)
                        # '_' 로 구분된 단어 중 하나가 일치하거나 전체가 일치하는 경우만
                        matches = []
                        for f_name in available_sfx.values():
                            parts = f_name.lower().replace('.', '_').split('_')
                            if eng.lower() in parts:
                                matches.append(f_name)
                        
                        if matches:
                            # [고도화] 중복 방지 랜덤 선택
                            best_file = get_unique_random_sfx(matches)
                            sfx_events.append({'time': sfx_time, 'file': best_file})
                            found_keywords.append(kor)

    # 파싱된 결과에서 중복 제거 및 시간순 정렬
    unique_events = []
    seen = set()
    for ev in sorted(sfx_events, key=lambda x: x['time']):
        key = (ev['time'], ev['file'])
        if key not in seen:
            unique_events.append(ev)
            seen.add(key)
    
    # 10초 간격 규칙 (SFX/앰비언스 채우기 고도화)
    # [고도화] 피아노/첼로 잔향(Immersion) 우선 선택 로직
    filler_keywords = ["ambient", "ambi", "night", "wind", "rain", "clock", "tick", "breath", "cricket", "forest", "fire", "crackle"]
    priority_keywords = ["piano", "cello", "note", "resonance"]
    
    available_fillers = []
    preferred_fillers = []
    
    if os.path.exists(SFX_DIR):
        for f in os.listdir(SFX_DIR):
            f_lower = f.lower()
            if "exclude" in f_lower: continue # 명시적 제외 파일 스킵
            
            if any(k in f_lower for k in priority_keywords):
                preferred_fillers.append(f)
            elif any(k in f_lower for k in filler_keywords):
                available_fillers.append(f)
    
    # [고도화] 선호 소리(피아노 등)가 없으면 기본값 보완
    if not preferred_fillers:
        preferred_fillers = ["ambient_piano_01.mp3", "ambient_cello_01.mp3"]
    
    final_events = []
    last_t = 0
    
    # 1. 이벤트 사이의 갭 채우기
    for ev in sorted(unique_events, key=lambda x: x['time']):
        while ev['time'] - last_t > 10000:
            gap = random.randint(8000, 12000)
            last_t += gap
            if ev['time'] - last_t < 1000: break
            
            # [수정] 악기음(피아노/첼로) 편중 해소: 확률 80% -> 30%로 조정
            if random.random() < 0.3 and preferred_fillers:
                filler = get_unique_random_sfx(preferred_fillers)
            elif available_fillers:
                filler = get_unique_random_sfx(available_fillers)
            else:
                filler = get_unique_random_sfx(preferred_fillers)
                
            final_events.append({'time': last_t, 'file': filler, 'is_filler': True})
        final_events.append(ev)
        last_t = max(last_t, ev['time'])
    
    # 2. 마지막 이벤트 이후 채우기
    while max_ms - last_t > 10000:
        gap = random.randint(8000, 12000)
        last_t += gap
        if max_ms - last_t < 2000: break
        
        # [수정] 마지막 구간도 악기음 확률 30%로 하향
        if random.random() < 0.3 and preferred_fillers:
            filler = get_unique_random_sfx(preferred_fillers)
        else:
            filler = get_unique_random_sfx(available_fillers or preferred_fillers)
            
        final_events.append({'time': last_t, 'file': filler, 'is_filler': True})
            
    unique_events = final_events

    return unique_events, max_ms + 2000 

def create_background_audio():
    print("🎨 [Audio Layer Factory] SFX 및 앰비언스 전용 파일 생성을 시작합니다...")
    
    # [변경] 통합된(Merged) 파일 처리로 변경
    now = time.time()
    srt_files = []
    # [개선] 더 넓은 범위의 자막 파일 찾기
    all_srts = [f for f in os.listdir(DOWNLOADS_DIR) if f.lower().endswith(".srt") and not f.startswith(".")]
    
    # 1순위: 최근 파일 중 슈퍼톤/마스터 키워드 포함
    priority_srts = [f for f in all_srts if any(k in f for k in ["_Full_Merged", "슈퍼톤", "대본_Stable", "Audio_Full"])]
    if priority_srts:
        latest_priority = max([os.path.join(DOWNLOADS_DIR, f) for f in priority_srts], key=os.path.getmtime)
        srt_files.append(os.path.basename(latest_priority))
    
    # 만약 위 우선순위로 못 찾으면, 그냥 가장 최신 SRT
    if not srt_files and all_srts:
         latest = max([os.path.join(DOWNLOADS_DIR, f) for f in all_srts], key=os.path.getmtime)
         srt_files.append(os.path.basename(latest))

    if not srt_files:
        print("❌ 처리할 자막 파일(.srt)을 찾을 수 없습니다.")
        return

    print(f"📂 발견된 파일: {len(srt_files)}개")

    # [사용자 요청] 덮어쓰기 방지: 파일명에 타임스탬프 추가
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    print(f"🕒 현재 작업 시간: {timestamp}")

    for srt_filename in srt_files:
        print(f"\n📄 [처리 중] {srt_filename}")
        srt_file = os.path.join(DOWNLOADS_DIR, srt_filename)
    
        # 2. SFX 및 총 길이 분석
        print(f"   🔍 대본 분석 및 효과음 추출 중...")
        sfx_events, total_duration_ms = parse_sfx_from_srt(srt_file)
        
        # [자동 보강] 만약 태그가 하나도 없다면, AI를 통해 보강 시도
        if not sfx_events and sfx_generator:
            print("   💡 태그가 발견되지 않아 AI 자동 효과음 분석을 시도합니다...")
            with open(srt_file, "r", encoding="utf-8-sig") as f:
                raw_srt = f.read()
            # AI로 태그가 삽입된 대본 생성
            processed_script = sfx_generator.auto_insert_sfx_tags(raw_srt)
            # 임시 파일로 저장하여 다시 파싱
            temp_srt = srt_file + ".tmp"
            with open(temp_srt, "w", encoding="utf-8") as f: f.write(processed_script)
            sfx_events, total_duration_ms = parse_sfx_from_srt(temp_srt)
            os.remove(temp_srt)
            print(f"   ✨ AI가 {len(sfx_events)}개의 효과음을 추천했습니다.")
        
        # [보정] SRT 길이 vs 실제 음성 파일 길이 비교
        # [유연한 매칭] 자막 파일명과 100% 일치하지 않더라도, 가장 관련성 높은 오디오 파일을 찾습니다.
        audio_exts = [".wav", ".mp3"]
        audio_file = None
        
        # 0순위: 파일명 완전 일치 확인
        for ext in audio_exts:
            check_file = srt_file.replace(".srt", ext)
            if os.path.exists(check_file):
                audio_file = check_file
                break
        
        if not audio_file:
            # 1순위: 'Reverted' (배경음 포함) 파일 검색
            base_name_only = os.path.splitext(srt_filename)[0]
            reverted_candidates = [
                f for f in os.listdir(DOWNLOADS_DIR) 
                if f.startswith(base_name_only) and "-reverted-" in f and f.endswith(".mp3")
            ]
            if reverted_candidates:
                latest_bgm_file = max([os.path.join(DOWNLOADS_DIR, f) for f in reverted_candidates], key=os.path.getmtime)
                print(f"   🔍 배경음 포함 파일(Reverted) 발견: {os.path.basename(latest_bgm_file)}")
                mp3_file = latest_bgm_file
            else:
                # 2순위: 성우 이름이나 특정 키워드가 포함된 가장 최신 MP3 검색
                # (예: Qwen_Sohee_..._2201_효과음합본... 같은 파일도 후보가 됨)
                match = re.search(r'(Qwen|Azure|Sohee|Azure\+Sohee|Audio_Full_Merged)', srt_filename, re.I)
                prefix = match.group(0) if match else ""
                
                all_audio_files = [os.path.join(DOWNLOADS_DIR, f) for f in os.listdir(DOWNLOADS_DIR) 
                             if f.lower().endswith(tuple(audio_exts)) and not f.startswith(".")]
                
                # 키워드가 포함된 파일들 중 가장 최신 것
                if prefix:
                    keyword_candidates = [f for f in all_audio_files if prefix.lower() in os.path.basename(f).lower()]
                    if keyword_candidates:
                        audio_file = max(keyword_candidates, key=os.path.getmtime)
                        print(f"   ℹ️ 이름 불일치로 성우 키워드({prefix}) 기반 최신 파일 선택: {os.path.basename(audio_file)}")
                    elif all_audio_files:
                        audio_file = max(all_audio_files, key=os.path.getmtime)
                        print(f"   ⚠️ 키워드 매칭 실패로 가장 최신 오디오 선택: {os.path.basename(audio_file)}")
                elif all_audio_files:
                    audio_file = max(all_audio_files, key=os.path.getmtime)
                    print(f"   ⚠️ 정보 부족으로 가장 최신 오디오 선택: {os.path.basename(audio_file)}")
        base_audio = None
        
        if audio_file and os.path.exists(audio_file):
            # [사용자 요청] 원본 음성 백업
            import shutil
            ext = os.path.splitext(audio_file)[1]
            backup_path = audio_file.replace(ext, f"_backup_{timestamp}{ext}")
            shutil.copy2(audio_file, backup_path)
            print(f"   💾 원본 백업 완료: {os.path.basename(backup_path)}")
 
            try:
                # from_file handles wav, mp3 based on file extension automatically
                voice_audio = AudioSegment.from_file(audio_file)
                base_audio = voice_audio
                voice_duration_ms = len(voice_audio)
                if voice_duration_ms > total_duration_ms:
                    total_duration_ms = voice_duration_ms + 1000
            except: pass

        # 3. 오디오 트랙 준비 (믹스용/순수SFX용 분리)
        # [수정] 사용자의 요청: 원본과 섞이지 않은 별도의 순수 효과음 트랙 생성
        pure_sfx_track = AudioSegment.silent(duration=total_duration_ms)
        
        if base_audio:
            current_len = len(base_audio)
            if current_len < total_duration_ms:
                silence_gap = AudioSegment.silent(duration=total_duration_ms - current_len)
                mix_track = base_audio + silence_gap
                print(f"   📏 원본 음성 연장: {current_len/1000:.1f}s -> {total_duration_ms/1000:.1f}s")
            else:
                mix_track = base_audio
            print("   🎤 원본 목소리 트랙 위에 효과음을 합성합니다. (합본용)")
        else:
            mix_track = AudioSegment.silent(duration=total_duration_ms)
            print(f"   ⚠️ 원본 목소리가 없어 빈 트랙({total_duration_ms/1000:.1f}s)에 효과음만 생성합니다.")

        # 4. SFX 오버레이
        sfx_count = 0
        for event in sfx_events:
            sfx_path = os.path.join(SFX_DIR, event['file'])
            try:
                # [고도화] 볼륨에도 랜덤성 부여 (-3dB ~ +3dB 범위의 편차)
                random_vol = random.uniform(-3, 2)
                volume_adj = (-12 if event.get('is_filler') else -6) + random_vol
                
                sfx_audio = AudioSegment.from_file(sfx_path) + volume_adj
                
                # [고도화] 위치(time)에도 미세한 랜덤 오프셋 (+/- 100ms) 부여
                jitter = random.randint(-150, 150)
                final_pos = max(0, event['time'] + jitter)
                
                # [중요] 두 트랙에 각각 오버레이
                mix_track = mix_track.overlay(sfx_audio, position=final_pos)
                pure_sfx_track = pure_sfx_track.overlay(sfx_audio, position=final_pos)
                
                filler_tag = "[FILLER] " if event.get('is_filler') else ""
                print(f"   ➕ {filler_tag}SFX: {event['file']} @ {final_pos/1000:.1f}s (Vol: {volume_adj:.1f}dB)")
                sfx_count += 1
            except: pass
            
        if sfx_count == 0:
            print("   ℹ️ 추가된 효과음이 없습니다.")

        # 5. 저장 (두 종류 파일 생성)
        mix_track = mix_track.normalize(headroom=0.1)
        pure_sfx_track = pure_sfx_track.normalize(headroom=0.1)
        
        base_name = os.path.splitext(srt_filename)[0]
        out_ext = os.path.splitext(audio_file)[1] if audio_file else ".mp3"
        fmt = out_ext.replace(".", "").lower()
        
        # A. 합본 파일
        output_filename = f"{base_name}_효과음합본_{timestamp}{out_ext}"
        output_path = os.path.join(DOWNLOADS_DIR, output_filename)
        
        # B. 순수 효과음 파일
        pure_filename = f"{base_name}_배경음SFX_{timestamp}{out_ext}"
        pure_path = os.path.join(DOWNLOADS_DIR, pure_filename)

        if fmt == "wav":
             mix_track.export(output_path, format="wav")
             pure_sfx_track.export(pure_path, format="wav")
        else:
             mix_track.export(output_path, format="mp3", bitrate="192k")
             pure_sfx_track.export(pure_path, format="mp3", bitrate="192k")
             
        if os.path.exists(pure_path):
            print(f"   ✅ 순수 효과음 출력 완료: {pure_path}")
        if os.path.exists(output_path):
            print(f"   ✅ 합본 출력 완료: {output_path}")

if __name__ == "__main__":
    create_background_audio()

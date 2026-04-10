import os
import re
import sys
import time
from pydub import AudioSegment

# [설정] FFmpeg 및 경로
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FFMPEG_DIR = os.path.join(BASE_DIR, "ffmpeg", "ffmpeg-2026-01-07-git-af6a1dd0b2-essentials_build", "bin")
FFMPEG_EXE = "ffmpeg"
FFPROBE_EXE = "ffprobe"

# Pydub 설정
AudioSegment.converter = FFMPEG_EXE
AudioSegment.ffprobe = FFPROBE_EXE
os.environ["PATH"] += os.pathsep + FFMPEG_DIR

DOWNLOADS_DIR = os.path.join(os.path.expanduser("~"), "Downloads")
LIB_DIR = os.path.join(BASE_DIR, "Library")
SFX_DIR = os.path.join(LIB_DIR, "sfx")
if not os.path.exists(SFX_DIR):
    SFX_DIR = os.path.join(BASE_DIR, "sfx")

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
    
    # [AI 보강] 전체 텍스트 수집 및 밀도 체크
    all_text_list = []
    timestamp_map = [] # [(start_ms, char_acc), ...]

    current_acc = 0
    for block in blocks:
        lines = block.strip().splitlines()
        if len(lines) >= 3:
            times = re.findall(r'(\d{2}:\d{2}:\d{2},\d{3})', lines[1])
            if times:
                start_ms = srt_time_to_ms(times[0])
                line_text = " ".join(lines[2:])
                all_text_list.append(line_text)
                timestamp_map.append((start_ms, current_acc))
                current_acc += len(line_text) + 1

    full_text = " ".join(all_text_list)
    
    # AI SFX 보강 (sfx_generator 사용)
    if sfx_generator and full_text:
        print(f"   🤖 [AI SFX] 대본 분석 및 밀도 체크 중 (글자수: {len(full_text)})")
        # 이 과정에서 35자당 1개 효과음이 보강됨
        full_text_with_ai = sfx_generator.process_script_sfx(full_text, output_dir=SFX_DIR)
        
        # 보강된 텍스트에서 태그와 텍스트 위치 분석하여 시간 매핑
        # [SFX:name] 태그들의 위치를 찾고, timestamp_map을 이용하여 가장 가까운 시작 시간을 배정
        matches = list(re.finditer(r'\[SFX:([^\]]+)\]', full_text_with_ai))
        
        # re.finditer의 인덱스는 태그를 포함한 길이이므로, 순수 텍스트 인덱스로 변환 필요
        # 하지만 간단하게: 태그가 나타난 순서대로 timestamp_map의 인덱스를 비례해서 매칭
        for m in matches:
            tag_name = m.group(1).strip().lower()
            tag_pos = m.start()
            
            # 태그 문자열들을 제거한 순수 텍스트에서의 위치 추정 (비례식 사용)
            ratio = tag_pos / len(full_text_with_ai)
            target_ms = int(ratio * (timestamp_map[-1][0] if timestamp_map else 0))
            
            # 가장 가까운 자막 시작 시간 찾기 (보정)
            best_ms = target_ms
            for ms, acc in timestamp_map:
                if acc / (current_acc or 1) > ratio:
                    best_ms = ms
                    break
            
            # 파일 확인 및 이벤트 추가
            found_file = None
            if tag_name in available_sfx:
                found_file = available_sfx[tag_name]
            else:
                # 새로 생성되었을 수도 있으므로 폴더 다시 확인
                new_path = os.path.join(SFX_DIR, f"{tag_name}.mp3")
                if os.path.exists(new_path):
                    found_file = f"{tag_name}.mp3"
            
            if found_file:
                sfx_events.append({'time': best_ms, 'file': found_file})
                max_ms = max(max_ms, best_ms)

    # 파싱된 결과에서 중복 제거 및 시간순 정렬
    unique_events = []
    seen = set()
    for ev in sorted(sfx_events, key=lambda x: x['time']):
        key = (ev['time'], ev['file'])
        if key not in seen:
            unique_events.append(ev)
            seen.add(key)
    
    # 총 길이는 SRT의 마지막 시간 기준
    last_block = blocks[-1].splitlines()
    if len(last_block) >= 2:
        last_times = re.findall(r'(\d{2}:\d{2}:\d{2},\d{3})', last_block[1])
        if len(last_times) >= 2:
            max_ms = max(max_ms, srt_time_to_ms(last_times[1]))

    return unique_events, max_ms + 2000 

def create_background_audio():
    print("🎨 [Audio Layer Factory] SFX 및 앰비언스 전용 파일 생성을 시작합니다...")
    
    # [변경] 단일 최신 파일 대신, part 별 일괄 처리 (최근 5분 이내)
    now = time.time()
    srt_files = []
    for f in os.listdir(DOWNLOADS_DIR):
        if f.lower().endswith(".srt") and "_part" in f:
            full_path = os.path.join(DOWNLOADS_DIR, f)
            if (now - os.path.getmtime(full_path)) < 3600: # [수정] 1시간(3600초) 이내
                srt_files.append(f)
    
    srt_files.sort(key=lambda x: int(re.search(r'part(\d+)', x).group(1)) if re.search(r'part(\d+)', x) else 0)
    
    if not srt_files:
        print("❌ 처리할 'part' 자막 파일을 찾을 수 없습니다.")
        return

    print(f"📂 발견된 파일: {len(srt_files)}개")

    # [사용자 요청] 카운터 002부터 시작
    current_counter = 2

    for srt_filename in srt_files:
        print(f"\n📄 [처리 중] {srt_filename} (Output ID: {current_counter:03d})")
        srt_file = os.path.join(DOWNLOADS_DIR, srt_filename)
    
        # 2. SFX 및 총 길이 분석
        sfx_events, total_duration_ms = parse_sfx_from_srt(srt_file)
        
        # [보정] SRT 길이 vs 실제 음성 파일 길이 비교 (더 긴 쪽 기준)
        mp3_file = srt_file.replace(".srt", ".mp3")
        if os.path.exists(mp3_file):
            try:
                voice_audio = AudioSegment.from_mp3(mp3_file)
                voice_duration_ms = len(voice_audio)
                if voice_duration_ms > total_duration_ms:
                    total_duration_ms = voice_duration_ms + 1000 # 1초 여유
            except: pass

        # 3. 빈 오디오 트랙 생성 (침묵, 자막 길이만큼)
        bg_track = AudioSegment.silent(duration=total_duration_ms)

        # [사용자 요청] 배경음(Ambience) 제거 -> 순수 효과음만 배치
        # 4. SFX 오버레이
        sfx_count = 0
        for event in sfx_events:
            sfx_path = os.path.join(SFX_DIR, event['file'])
            try:
                sfx_audio = AudioSegment.from_mp3(sfx_path) - 5
                bg_track = bg_track.overlay(sfx_audio, position=event['time'])
                print(f"   ➕ SFX: {event['file']} @ {event['time']/1000:.1f}s")
                sfx_count += 1
            except: pass
            
        if sfx_count == 0:
            print("   ℹ️ 추가된 효과음이 없습니다 (빈 파일 생성됨)")

        # 5. 저장 (002, 003... 카운팅 적용)
        # 노멀라이즈는 효과음 피크를 치지 않게 주의 (배경음 없으므로 헤드룸 넉넉히)
        bg_track = bg_track.normalize(headroom=1.0)
        
        base_name = os.path.splitext(srt_filename)[0]
        # 출력 파일명: 002_원래이름_효과음.mp3
        output_filename = f"{current_counter:03d}_{base_name}_배경_효과음_레이어.mp3"
        output_path = os.path.join(DOWNLOADS_DIR, output_filename)
        
        bg_track.export(output_path, format="mp3", bitrate="192k")
        print(f"   ✅ 생성 완료: {output_filename}")
        
        current_counter += 1

if __name__ == "__main__":
    create_background_audio()

import os
import re
import sys
import time
from pydub import AudioSegment

# [설정] FFmpeg 및 경로
FFMPEG_EXE = r"C:\Users\moori\Downloads\ffmpeg-2026-01-07-git-af6a1dd0b2-essentials_build\ffmpeg-2026-01-07-git-af6a1dd0b2-essentials_build\bin\ffmpeg"
FFMPEG_DIR = os.path.dirname(FFMPEG_EXE)
AudioSegment.converter = FFMPEG_EXE
AudioSegment.ffprobe = os.path.join(FFMPEG_DIR, "ffprobe")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOADS_DIR = os.path.join(os.path.expanduser("~"), "Downloads")
SFX_DIR = os.path.join(BASE_DIR, "Library", "sfx")
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

    blocks = re.split(r'\n\s*\n', content)
    for block in blocks:
        lines = block.splitlines()
        if len(lines) >= 3:
            times = re.findall(r'(\d{2}:\d{2}:\d{2},\d{3})', lines[1])
            if len(times) >= 2:
                start_ms = srt_time_to_ms(times[0])
                end_ms = srt_time_to_ms(times[1])
                max_ms = max(max_ms, end_ms)
                
                text = " ".join(lines[2:])
                tags = re.findall(r'\[SFX:\s*([^\]]+)\]', text)
                for tag in tags:
                    tag_clean = tag.strip().lower()
                    found_file = None
                    for sfx_key, sfx_file in available_sfx.items():
                        if tag_clean in sfx_key or sfx_key in tag_clean:
                            found_file = sfx_file
                            break
                    if found_file:
                        sfx_events.append({'time': start_ms, 'file': found_file})
    
    return sfx_events, max_ms + 2000 # 여유분 2초

def create_background_audio():
    print("🎨 [Audio Layer Factory] SFX 및 앰비언스 전용 파일 생성을 시작합니다...")
    
    # 1. SRT 파일 찾기
    srt_file = get_latest_srt()
    if not srt_file:
        print("❌ 최근 SRT 파일을 찾을 수 없습니다. (Downloads 폴더 확인)")
        return
    
    print(f"📄 분석 대상 자막: {os.path.basename(srt_file)}")
    
    # 2. SFX 및 총 길이 분석
    sfx_events, total_duration_ms = parse_sfx_from_srt(srt_file)
    print(f"🔊 감지된 SFX 포인트: {len(sfx_events)}개")
    print(f"⏱️ 예상 오디오 길이: {total_duration_ms/1000:.1f}초")

    # 3. 빈 오디오 트랙 생성
    bg_track = AudioSegment.silent(duration=total_duration_ms)

    # 4. 앰비언스 깔기 (루프)
    ambi_file = os.path.join(SFX_DIR, "night_ambi.mp3")
    if not os.path.exists(ambi_file):
        ambi_file = os.path.join(SFX_DIR, "wind_storm.mp3")
    
    if os.path.exists(ambi_file):
        print(f"🌿 앰비언스 적용: {os.path.basename(ambi_file)} (볼륨 -15dB)")
        ambi_audio = AudioSegment.from_mp3(ambi_file) - 15
        # 전체 길이에 맞춰 루프로 오버레이
        bg_track = bg_track.overlay(ambi_audio, loop=True)
    else:
        print("⚠️ 앰비언스 파일을 찾을 수 없어 빈 배경으로 진행합니다.")

    # 5. SFX 오버레이
    for event in sfx_events:
        sfx_path = os.path.join(SFX_DIR, event['file'])
        try:
            sfx_audio = AudioSegment.from_mp3(sfx_path) - 5
            bg_track = bg_track.overlay(sfx_audio, position=event['time'])
            print(f"   ➕ SFX 추가: {event['file']} @ {event['time']/1000:.1f}s")
        except:
            print(f"   ❌ SFX 로드 실패: {event['file']}")

    # 6. 최종 노멀라이즈 및 출력
    print("⚙️ 오디오 밸런싱 및 인코딩 중...")
    bg_track = bg_track.normalize(headroom=0.5)
    
    output_filename = os.path.basename(srt_file).replace(".srt", "_배경_효과음_레이어.mp3")
    output_path = os.path.join(DOWNLOADS_DIR, output_filename)
    
    bg_track.export(output_path, format="mp3", bitrate="192k")
    print(f"\n✨ 완료! 별도 오디오 파일이 생성되었습니다:")
    print(f"📍 {output_path}")

if __name__ == "__main__":
    create_background_audio()

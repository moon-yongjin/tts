import os
import re
import sys
import datetime
import shutil
from pydub import AudioSegment

# [설정]
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOADS_DIR = os.path.join(os.path.expanduser("~"), "Downloads")
FFMPEG_EXE = "ffmpeg"
FFPROBE_EXE = "ffprobe"
BACKUP_BASE = os.path.join(os.path.expanduser("~"), "muhyup_backups", "merged_parts")

# Pydub 설정
AudioSegment.converter = FFMPEG_EXE
AudioSegment.ffprobe = FFPROBE_EXE
os.environ["PATH"] += os.pathsep + os.path.dirname(FFMPEG_EXE)

def srt_time_to_ms(time_str):
    h, m, s_ms = time_str.split(':')
    s, ms = s_ms.split(',')
    return (int(h) * 3600 + int(m) * 60 + int(s)) * 1000 + int(ms)

def format_time_ms(ms):
    total_seconds = ms / 1000
    h = int(total_seconds // 3600)
    m = int((total_seconds % 3600) // 60)
    s = int(total_seconds % 60)
    ms_part = int(ms % 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms_part:03d}"

def merge_files():
    print("🚀 [File Merger] 다운로드 폴더의 분할된 음성/자막 합치기 시작...")
    
    # 1. 파일 그룹 찾기 (partX 패턴, 최근 10분 이내)
    now = datetime.datetime.now().timestamp()
    all_files = os.listdir(DOWNLOADS_DIR)
    
    files = []
    for f in all_files:
        if "_part" in f and (f.endswith(".mp3") or f.endswith(".wav") or f.endswith(".srt")):
            full_path = os.path.join(DOWNLOADS_DIR, f)
            mtime = os.path.getmtime(full_path)
            if (now - mtime) < 600: # 600초(10분) 이내 파일만
                files.append(f)
    
    if not files:
        print("❌ 합칠 파일(최근 10분 이내 part*.mp3/srt)을 찾을 수 없습니다.")
        return

    # 그룹핑: { '파일명_timestamp': {'mp3': [], 'srt': []} }
    groups = {}
    for f in files:
        base_name = f.split("_part")[0]
        if base_name not in groups: groups[base_name] = {'audio': [], 'srt': []}
        if f.endswith(".mp3") or f.endswith(".wav"): groups[base_name]['audio'].append(f)
        elif f.endswith(".srt"): groups[base_name]['srt'].append(f)

    # 각 그룹별 병합 수행
    for base_name, data in groups.items():
        audios = sorted(data['audio'], key=lambda x: int(re.search(r'part(\d+)', x).group(1)))
        srts = sorted(data['srt'], key=lambda x: int(re.search(r'part(\d+)', x).group(1)))
        
        if not audios: continue
        
        print(f"\n📂 처리 중: {base_name} (Audio: {len(audios)}개, SRT: {len(srts)}개)")
        
        # --- [MP3 병합] ---
        combined_audio = AudioSegment.empty()
        part_durations = [] # 각 파트의 지속시간 저장 (자막 타이밍 계산용)
        
        # [File Size Check] 0바이트거나 너무 작은 파일(1KB 미만)은 스킵
        valid_audios = []
        for audio_file in audios:
            path = os.path.join(DOWNLOADS_DIR, audio_file)
            if os.path.getsize(path) < 100: # 100 byte 미만은 확실히 오류
                print(f"   ⚠️ 경고: 손상된 파일 감지됨 (Skipping): {audio_file}")
            else:
                valid_audios.append(audio_file)
        
        if not valid_audios:
            print(f"   ❌ 유효한 오디오 파일이 없어 '{base_name}' 그룹을 건너뜁니다.")
            continue

        for audio_file in valid_audios:
            path = os.path.join(DOWNLOADS_DIR, audio_file)
            print(f"   ➕ 오디오 병합: {audio_file}")
            try:
                if audio_file.endswith(".mp3"):
                    segment = AudioSegment.from_mp3(path)
                else:
                    segment = AudioSegment.from_wav(path)
                combined_audio += segment
                part_durations.append(len(segment))
            except Exception as e:
                print(f"   ❌ 오디오 디코딩 실패 ({audio_file}): {e}")
                print(f"   ⛔ 이 그룹({base_name})의 병합을 중단합니다.")
                part_durations = None # 플래그
                break
        
        if part_durations is None: continue # 병합 실패 시 스킵

        output_mp3_name = f"{base_name}_Full_Merged.mp3"
        output_mp3_path = os.path.join(DOWNLOADS_DIR, output_mp3_name)
        combined_audio.export(output_mp3_path, format="mp3", bitrate="192k")
        print(f"   ✅ 오디오 저장 완료: {output_mp3_name}")
        
        # --- [SRT 병합 및 시간 보정] ---
        if srts:
            merged_srt_content = []
            srt_idx = 1
            current_time_offset = 0 # 현재 파트까지의 누적 시간 오프셋
            
            for i, srt_file in enumerate(srts):
                path = os.path.join(DOWNLOADS_DIR, srt_file)
                print(f"   📝 자막 병합: {srt_file} (Offset: {current_time_offset/1000:.1f}s)")
                
                with open(path, "r", encoding="utf-8-sig") as f:
                    content = f.read().strip()
                
                blocks = re.split(r'\n\s*\n', content)
                for block in blocks:
                    lines = block.splitlines()
                    if len(lines) >= 3:
                        times = re.findall(r'(\d{2}:\d{2}:\d{2},\d{3})', lines[1])
                        if len(times) >= 2:
                            start_ms = srt_time_to_ms(times[0]) + current_time_offset
                            end_ms = srt_time_to_ms(times[1]) + current_time_offset
                            text = "\n".join(lines[2:])
                            
                            merged_srt_content.append(f"{srt_idx}\n{format_time_ms(start_ms)} --> {format_time_ms(end_ms)}\n{text}\n\n")
                            srt_idx += 1
                
                # 다음 파트를 위해 오프셋 증가 (실제 오디오 길이 기반)
                if i < len(part_durations):
                    current_time_offset += part_durations[i]
            
            output_srt_name = f"{base_name}_Full_Merged.srt"
            output_srt_path = os.path.join(DOWNLOADS_DIR, output_srt_name)
            with open(output_srt_path, "w", encoding="utf-8-sig") as f:
                f.writelines(merged_srt_content)
            print(f"   ✅ 자막 저장 완료: {output_srt_name}")
            
        # --- [백업 및 삭제 (NEW)] ---
        try:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = os.path.join(BACKUP_BASE, f"{base_name}_{timestamp}")
            if not os.path.exists(backup_dir):
                os.makedirs(backup_dir)
            
            print(f"   📦 소스 파일 백업 중: {os.path.basename(backup_dir)}")
            merged_sources = audios + srts
            for s_file in merged_sources:
                s_path = os.path.join(DOWNLOADS_DIR, s_file)
                if os.path.exists(s_path):
                    shutil.copy2(s_path, os.path.join(backup_dir, s_file))
            
            print(f"   🧹 소스 파일 삭제 중 (Downloads 폴더 정리)...")
            for s_file in merged_sources:
                s_path = os.path.join(DOWNLOADS_DIR, s_file)
                if os.path.exists(s_path):
                    os.remove(s_path)
            print(f"   ✨ {base_name} 정리 완료.")
            
        except Exception as e:
            print(f"   ⚠️ 백업/삭제 중 오류 발생 (하지만 병합은 성공함): {e}")
            
    print(f"\n✨ 모든 병합 작업이 완료되었습니다!")

if __name__ == "__main__":
    merge_files()

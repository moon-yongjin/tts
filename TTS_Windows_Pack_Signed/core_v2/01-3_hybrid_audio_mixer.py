import os
import re
import json
import time
from pydub import AudioSegment

# [설정] 
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJ_ROOT = os.path.dirname(SCRIPT_DIR)
DOWNLOADS_DIR = os.path.join(os.path.expanduser("~"), "Downloads")
QWEN_DIALOGUE_DIR = os.path.join(DOWNLOADS_DIR, "무협_대사_일레븐렙스")

def get_latest_azure_assets():
    """가장 최근에 생성된 아주라(Azure) 음성 및 SRT 찾기"""
    # 아주라 합본 파일 패턴: *_Full_Merged.mp3 또는 *_part1.mp3 (짧은 대본의 경우)
    voice_files = [f for f in os.listdir(DOWNLOADS_DIR) 
                   if f.endswith(".mp3") and ("_Full_Merged" in f or "_part" in f)]
    if not voice_files: return None, None
    
    latest_voice = max([os.path.join(DOWNLOADS_DIR, f) for f in voice_files], key=os.path.getmtime)
    
    # 대응하는 SRT 파일 찾기 (.mp3 -> .srt)
    latest_srt = latest_voice.rsplit('.', 1)[0] + ".srt"
    
    if not os.path.exists(latest_srt):
        print(f"⚠️ SRT 파일을 찾을 수 없습니다: {latest_srt}")
        return latest_voice, None
        
    return latest_voice, latest_srt

def parse_srt(srt_path):
    """SRT 파일을 파싱하여 시간과 텍스트 정보를 리스트로 반환"""
    if not srt_path: return []
    with open(srt_path, "r", encoding="utf-8-sig") as f:
        content = f.read().strip()
    
    blocks = re.split(r'\n\s*\n', content)
    entries = []
    for block in blocks:
        lines = block.splitlines()
        if len(lines) >= 3:
            # 00:00:01,500 --> 00:00:04,200
            time_match = re.findall(r'(\d{2}:\d{2}:\d{2},\d{3})', lines[1])
            if len(time_match) == 2:
                start_ms = srt_time_to_ms(time_match[0])
                end_ms = srt_time_to_ms(time_match[1])
                text = " ".join(lines[2:]).strip()
                entries.append({"start": start_ms, "end": end_ms, "text": text})
    return entries

def srt_time_to_ms(time_str):
    h, m, s_ms = time_str.split(':')
    s, ms = s_ms.split(',')
    return int(h)*3600000 + int(m)*60000 + int(s)*1000 + int(ms)

def normalize_text(text):
    return re.sub(r'[^a-zA-Z가-힣0-9]', '', text).lower()

def run_hybrid_mixing():
    print("🎬 [STEP 01-2] 하이브리드 음성 믹싱 시작 (아주라 + 퀜)")
    
    azure_mp3, azure_srt = get_latest_azure_assets()
    if not azure_mp3 or not azure_srt:
        print("❌ 아주라(Azure) 생성 자산을 찾을 수 없습니다. (01번 공정 먼저 실행 필요)")
        return

    print(f"🎙️ 아주라 나레이션: {os.path.basename(azure_mp3)}")
    print(f"📄 아주라 자막: {os.path.basename(azure_srt)}")

    # 자막 파싱
    srt_entries = parse_srt(azure_srt)
    
    # 퀜 대사 파일 목록 로드
    if not os.path.exists(QWEN_DIALOGUE_DIR):
        print("❌ 퀜 대사 폴더가 없습니다.")
        return
        
    dialogue_files = sorted([f for f in os.listdir(QWEN_DIALOGUE_DIR) if f.endswith(".mp3") and f[0].isdigit()])
    if not dialogue_files:
        print("❌ 퀜 대사 파일이 없습니다.")
        return

    # 오디오 로드
    main_audio = AudioSegment.from_mp3(azure_mp3)
    final_audio = main_audio

    print(f"📦 총 {len(dialogue_files)}개의 퀜 대사 매칭 시작...")

    applied_count = 0
    for d_file in dialogue_files:
        d_path = os.path.join(QWEN_DIALOGUE_DIR, d_file)
        # 파일명에서 텍스트 추출 (순번_텍스트.mp3 형식)
        # 001_아니제수씨.mp3 -> 아니제수씨
        d_name_clean = normalize_text(re.sub(r'^\d+_', '', d_file).replace(".mp3", ""))
        
        # SRT에서 매칭되는 구간 찾기
        matched_entry = None
        for entry in srt_entries:
            entry_norm = normalize_text(entry["text"])
            # 퀜 대사 텍스트가 자막 텍스트의 일부이거나 그 반대일 때 매칭
            if d_name_clean in entry_norm or entry_norm in d_name_clean:
                matched_entry = entry
                break
        
        if matched_entry:
            print(f"✅ 매칭 성공: {d_file} -> {matched_entry['text'][:20]}...")
            d_audio = AudioSegment.from_mp3(d_path)
            
            # [개선 1] 볼륨 평준화 (Normalizing)
            # 아주라 대비 퀜 대사가 너무 작거나 크지 않게 조정 (-20dBFS 수준)
            target_dbfs = -20.0
            change_in_dbfs = target_dbfs - d_audio.dBFS
            d_audio = d_audio.apply_gain(change_in_dbfs)
            
            # [개선 2] 페이드 인/아웃 추가 (매끄러운 전환)
            d_audio = d_audio.fade_in(50).fade_out(50)
            
            # [개선 3] 아주라 목세리 제거 구간 정밀 조정
            # 아주라의 원래 구간(SRT 기준)을 먼저 무음 처리한 뒤, 그 위에 퀜 대사를 얹음
            # 이렇게 하면 퀜 대사가 짧더라도 아주라 목소리가 중간에 튀어나오지 않음
            start = matched_entry["start"]
            duration_orig = matched_entry["end"] - matched_entry["start"]
            
            # 1. 먼저 해당 구간의 아주라 목소리를 완전히 죽인 '무음 레이어' 생성
            silence_segment = AudioSegment.silent(duration=duration_orig)
            final_audio = final_audio.overlay(silence_segment, position=start, gain_during_overlay=-120)
            
            # 2. 그 위에 퀜 대사 overlay (이미 부드러운 전환을 위해 페이드 처리됨)
            final_audio = final_audio.overlay(d_audio, position=start)
            applied_count += 1
        else:
            print(f"⚠️ 매칭 실패: {d_file} (자막에서 대사 내용을 찾을 수 없음)")

    # 최종 저장
    # .mp3 확장자 앞에 _Hybrid_Final을 붙임
    output_name = os.path.basename(azure_mp3).rsplit('.', 1)[0] + "_Hybrid_Final.mp3"
    output_path = os.path.join(DOWNLOADS_DIR, output_name)
    final_audio.export(output_path, format="mp3", bitrate="192k")

    print(f"\n✨ 하이브리드 성우 믹싱 완료!")
    print(f"📍 결과물: {output_path} ({applied_count}/{len(dialogue_files)} 대사 적용됨)")

if __name__ == "__main__":
    run_hybrid_mixing()

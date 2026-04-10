import os
import sys
import re
import json
import time
import datetime
import tempfile
import azure.cognitiveservices.speech as speechsdk
from pydub import AudioSegment

# [1. 환경 및 경로 설정]
sys.stdout.reconfigure(encoding='utf-8')

ENGINE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJ_ROOT = os.path.dirname(ENGINE_DIR)
DOWNLOADS_DIR = os.path.join(os.path.expanduser("~"), "Downloads")
LIB_DIR = os.path.join(PROJ_ROOT, "Library")

# Azure Speech 설정
SPEECH_KEY = "21HfTF65JeOoI5mqoW5NfPYZcmG114R7AFzrjbk5HLRE4fqIua7NJQQJ99CAACNns7RXJ3w3AAAYACOGMfRn"
SPEECH_REGION = "koreacentral"
VOICE_NAME = "ko-KR-JiMinNeural" 

# FFmpeg 설정 (pydub용)
FFMPEG_EXE = "ffmpeg"
AudioSegment.converter = FFMPEG_EXE

# --- [2. 텍스트 보정 및 유틸리티] ---

def apply_srt_adjustment(srt_path, original_script_part):
    """SRT 자막을 원본 대본과 대조하여 SFX 태그 등을 복원"""
    if not os.path.exists(srt_path): return
    
    def normalize(text):
        return re.sub(r'[^a-zA-Z가-힣0-9]', '', str(text)).lower()

    # 1. 원본 대본 단순화 (매칭용)
    clean_text = re.sub(r'\[(대사|묘사|지문|설명|챕터|CHAPTER).*?\]', ' ', original_script_part, flags=re.IGNORECASE)
    clean_text = re.sub(r'\(.*?\)', ' ', clean_text)
    # SFX 태그는 지우지 않고 매칭에 활용하거나, 위치를 추적해야 함. 
    # 하지만 V1 방식은 '단어' 단위 매칭 후 원본 텍스트를 가져오는 방식임.
    script_words = clean_text.split()
    script_norm = [normalize(w) for w in script_words]

    # 2. SRT 파싱
    with open(srt_path, "r", encoding="utf-8-sig") as f:
        srt_content = f.read().strip()
    
    blocks = re.split(r'\n\s*\n', srt_content)
    srt_entries = []
    srt_all_norm = []
    
    for block in blocks:
        lines = block.splitlines()
        if len(lines) >= 3:
            text = " ".join(lines[2:])
            words = text.split()
            srt_entries.append({'num': lines[0], 'time': lines[1], 'text': text, 'words': words})
            srt_all_norm.extend([normalize(w) for w in words])

    if not script_words or not srt_entries: return

    # 3. SequenceMatcher로 매칭하여 원본 텍스트(태그 포함) 복원
    import difflib
    sm = difflib.SequenceMatcher(None, script_norm, srt_all_norm)
    srt_to_script = {}
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag in ('equal', 'replace'):
            for offset in range(min(i2-i1, j2-j1)):
                srt_to_script[j1 + offset] = i1 + offset

    # 4. SRT 재구성
    corrected_blocks = []
    word_ptr = 0
    last_script_idx = -1
    
    for entry in srt_entries:
        indices = [srt_to_script.get(word_ptr + k) for k in range(len(entry['words'])) if (word_ptr + k) in srt_to_script]
        word_ptr += len(entry['words'])
        
        if indices:
            start, end = min(indices), max(indices)
            if start <= last_script_idx: start = last_script_idx + 1
            
            # 자막 글자수 제한(14자)을 고려하여 원본에서 가져올 범위를 조절해야 함
            # 단순 매칭 시 원본의 긴 문장을 가져와버릴 위험이 있음.
            # 여기서는 'SFX 태그 복원'이 핵심이므로, 매칭된 단어 주변의 태그를 포함시키는 것이 목표.
            
            # 안전하게: 원본 단어들을 가져오되, 너무 길어지지 않게 주의
            # V1 방식을 그대로 쓰면 14자 제한이 깨질 수 있음.
            # 따라서, 여기서는 '단어'만 원본으로 교체하되, SFX 태그는 별도로 처리하는게 이상적임.
            # 하지만 사용자 요청은 "원래는 됐다" 이므로 V1 로직을 최대한 따르되 길이 체크 추가.
            
            if start <= end:
                # 원본 텍스트 조각 가져오기
                restored_words = script_words[start:end+1]
                # SFX 태그가 포함되어 있는지 확인
                entry_text = " ".join(restored_words)
                last_script_idx = end
            else: entry_text = entry['text']
        else: entry_text = entry['text']
        
        corrected_blocks.append(f"{entry['num']}\n{entry['time']}\n{entry_text}\n\n")

    with open(srt_path, "w", encoding="utf-8-sig") as f:
        f.writelines(corrected_blocks)

def clean_for_output(text):
    # 음성 합성용 텍스트 정리 (태그 제거)
    text = re.sub(r'\[(BGM|묘사|지문|설명|배경|음악|CHAPTER|챕터|SFX):?.*?\]', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\(.*?\)', '', text)
    symbols = ['*', '-', '#', '@', '+', '=', '>', '<', '|', '/', '\\', '^']
    for s in symbols: text = text.replace(s, '')
    return text.strip()

def format_time(ticks):
    total_seconds = ticks / 10000000
    h = int(total_seconds // 3600)
    m = int((total_seconds % 3600) // 60)
    s = int(total_seconds % 60)
    ms = int((total_seconds * 1000) % 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

# --- [3. 메인 TTS 생성 엔진 - 스마트 하이브리드] ---

def generate_voice_qwen(text, filename, download_dir):
    """로컬 Qwen-TTS Bridge 호출"""
    output_path = os.path.join(download_dir, f"{filename}.mp3")
    
    BRIDGE_DIR = os.path.join(PROJ_ROOT, "bridge")
    REQUEST_FILE = os.path.join(BRIDGE_DIR, "qwen_request.json")
    RESULT_FILE = os.path.join(BRIDGE_DIR, "qwen_result.json")
    
    if not os.path.exists(BRIDGE_DIR): os.makedirs(BRIDGE_DIR)
    if os.path.exists(RESULT_FILE): os.remove(RESULT_FILE)

    request_data = {"text": text, "output_name": f"Hybrid_Diag_{filename}.mp3"}

    with open(REQUEST_FILE, "w", encoding="utf-8") as f:
        json.dump(request_data, f, ensure_ascii=False, indent=2)
    
    start_wait = time.time()
    while time.time() - start_wait < 60:
        if os.path.exists(RESULT_FILE):
            with open(RESULT_FILE, "r", encoding="utf-8") as f:
                result = json.load(f)
            if result.get("status") == "success":
                temp_audio = result.get("audio")
                if temp_audio and os.path.exists(temp_audio):
                    import shutil
                    shutil.copy2(temp_audio, output_path)
                    return True
        time.sleep(0.5)
    return False

def generate_segment_azure(text, temp_audio_path, start_ticks_offset=0, start_idx=1):
    speech_config = speechsdk.SpeechConfig(subscription=SPEECH_KEY, region=SPEECH_REGION)
    speech_config.set_speech_synthesis_output_format(speechsdk.SpeechSynthesisOutputFormat.Audio48Khz192KBitRateMonoMp3)
    
    clean_text = clean_for_output(text)
    if not clean_text: return [], 0, start_idx
    
    ssml_text = f'''
    <speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="ko-KR">
        <voice name="{VOICE_NAME}">
            <prosody rate="-8.00%" pitch="-3.00%">{clean_text}</prosody>
        </voice>
    </speak>
    '''

    audio_config = speechsdk.audio.AudioOutputConfig(filename=temp_audio_path)
    synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)

    srt_entries = []
    current_words = []
    current_start_ticks = None
    last_end_ticks = 0
    current_idx = start_idx

    def word_boundary_handler(evt):
        nonlocal current_words, current_start_ticks, last_end_ticks, current_idx
        word = evt.text.strip()
        if not word: return
        
        if current_words:
            if len(" ".join(current_words + [word])) > 14:
                adjusted_start = current_start_ticks + start_ticks_offset
                adjusted_end = last_end_ticks + start_ticks_offset
                srt_entries.append(f"{current_idx}\n{format_time(adjusted_start)} --> {format_time(adjusted_end)}\n{' '.join(current_words)}\n\n")
                current_words, current_start_ticks, current_idx = [], None, current_idx + 1

        last_end_ticks = evt.audio_offset + int(evt.duration.total_seconds() * 10000000)
        if not current_words: current_start_ticks = evt.audio_offset
        current_words.append(word)
        
        if any(word.endswith(p) for p in ['.', '?', '!', '~']):
            adjusted_start = current_start_ticks + start_ticks_offset
            adjusted_end = last_end_ticks + start_ticks_offset
            srt_entries.append(f"{current_idx}\n{format_time(adjusted_start)} --> {format_time(adjusted_end)}\n{' '.join(current_words)}\n\n")
            current_words, current_start_ticks, current_idx = [], None, current_idx + 1

    synthesizer.synthesis_word_boundary.connect(word_boundary_handler)
    result = synthesizer.speak_ssml_async(ssml_text).get()

    if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        if current_words:
            adjusted_start = current_start_ticks + start_ticks_offset
            adjusted_end = last_end_ticks + start_ticks_offset
            srt_entries.append(f"{current_idx}\n{format_time(adjusted_start)} --> {format_time(adjusted_end)}\n{' '.join(current_words)}\n\n")
            current_idx += 1
        return srt_entries, last_end_ticks, current_idx
    return [], 0, current_idx

def partition_script(text):
    """나레이션과 따옴표 대사를 순서대로 분리"""
    # 따옴표 패턴 (이중, 단일 포함)
    pattern = r'(["“”\'‘’].*?["“”\'‘’])'
    parts = re.split(pattern, text, flags=re.DOTALL)
    
    blocks = []
    for p in parts:
        p = p.strip()
        if not p: continue
        is_dialogue = (p.startswith(('"', '“', "'", '‘')) and p.endswith(('"', '”', "'", '’')))
        blocks.append({"text": p, "is_dialogue": is_dialogue})
    return blocks

def run_smart_hybrid_factory(script_text, output_path):
    blocks = partition_script(script_text)
    print(f"📦 대본 분석 완료: 총 {len(blocks)}개 블록 (나레이션/대사 분리)")

    combined_audio = AudioSegment.empty()
    all_srt_entries = []
    total_ms = 0
    current_idx = 1
    
    # 대사 전용 임시 폴더
    diag_dir = os.path.join(DOWNLOADS_DIR, "Hybrid_Dialogue_Parts")
    if not os.path.exists(diag_dir): os.makedirs(diag_dir)

    with tempfile.TemporaryDirectory() as tmp_dir:
        for i, block in enumerate(blocks):
            text = block["text"]
            is_diag = block["is_dialogue"]
            
            print(f"🎙️ [{i+1}/{len(blocks)}] {'[대사]' if is_diag else '[나레이션]'} 처리 중: {text[:30]}...")
            
            seg_audio = None
            seg_srt = []
            
            if is_diag:
                # 퀜(Qwen)으로 대사 생성
                clean_text = text.strip('"“”\'‘’').strip()
                # 문장 끝에 마침표가 없으면 추가하여 자연스러운 갈무리 유도
                if not clean_text.endswith(('.', '!', '?', '~')):
                    clean_text += "."
                
                tmp_name = f"part_{i:03d}"
                success = generate_voice_qwen(clean_text, tmp_name, diag_dir)
                
                if success:
                    seg_audio_path = os.path.join(diag_dir, f"{tmp_name}.mp3")
                    seg_audio = AudioSegment.from_mp3(seg_audio_path)
                    
                    # 볼륨 평준화 (-20dBFS)
                    target_dbfs = -20.0
                    seg_audio = seg_audio.apply_gain(target_dbfs - seg_audio.dBFS)
                    seg_audio = seg_audio.fade_in(50).fade_out(50)
                    
                    # [추가] 대사 끝난 후 쉬는 템포 (0.5초 무음) 추가
                    seg_audio = seg_audio + AudioSegment.silent(duration=500)
                    
                    # 대사 전용 SRT 엔트리 (통으로 하나)
                    start_time = format_time(total_ms * 10000)
                    end_time = format_time((total_ms + len(seg_audio)) * 10000)
                    seg_srt.append(f"{current_idx}\n{start_time} --> {end_time}\n{text}\n\n")
                    current_idx += 1
            else:
                # 아주라(Azure)로 나레이션 생성
                tmp_audio_path = os.path.join(tmp_dir, f"azure_{i:03d}.mp3")
                srt_part, last_ticks, next_idx = generate_segment_azure(text, tmp_audio_path, total_ms * 10000, current_idx)
                
                if os.path.exists(tmp_audio_path) and os.path.getsize(tmp_audio_path) > 0:
                    seg_audio = AudioSegment.from_mp3(tmp_audio_path)
                    seg_srt = srt_part
                    current_idx = next_idx
                else:
                    print(f"⚠️ 아주라 생성 건너뜀 (내용 없음 또는 생성 실패): {text[:20]}...")

            if seg_audio is not None:
                combined_audio += seg_audio
                all_srt_entries.extend(seg_srt)
                total_ms += len(seg_audio)

    # 최종 저장
    combined_audio.export(output_path, format="mp3", bitrate="192k")
    srt_path = output_path.replace(".mp3", ".srt")
    with open(srt_path, "w", encoding="utf-8-sig") as f:
        f.writelines(all_srt_entries)
    
    print(f"✅ 스마트 하이브리드 합성 완료: {os.path.basename(output_path)}")

if __name__ == "__main__":
    target_file = sys.argv[1] if len(sys.argv) > 1 else os.path.join(PROJ_ROOT, "대본.txt")
    
    if os.path.exists(target_file):
        with open(target_file, "r", encoding="utf-8-sig") as f:
            script_text = f.read().strip()
        
        if script_text:
            timestamp = datetime.datetime.now().strftime("%m%d_%H%M")
            base_filename = os.path.splitext(os.path.basename(target_file))[0]
            output_name = f"{base_filename}_{timestamp}_SmartHybrid.mp3"
            output_path = os.path.join(DOWNLOADS_DIR, output_name)
            
            run_smart_hybrid_factory(script_text, output_path)
            print(f"✨ 모든 작업 완료! 결과물: {output_path}")
        else: print("❌ 대본이 비어 있습니다.")
    else: print(f"❌ 대본 없음: {target_file}")

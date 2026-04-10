import os
import re
import sys
import torch
import soundfile as sf
import numpy as np
from datetime import datetime
try:
    from pydub import AudioSegment
except ImportError:
    print("⚠️ pydub not found. Please install it with 'pip install pydub'")
    sys.exit(1)

# Add current directory to path so it can find qwen_tts
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from qwen_tts import Qwen3TTSModel

# [경로 설정]
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WORKSPACE_DIR = os.path.dirname(BASE_DIR)
DOWNLOADS_DIR = os.path.join(WORKSPACE_DIR, "Downloads")
os.makedirs(DOWNLOADS_DIR, exist_ok=True)

# [Qwen-TTS 모델 설정]
MODEL_ID = "Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice"

# [멀티 스피커 설정]
SPEAKER_NARRATION = "sohee"
INSTRUCT_NARRATION = "An extremely breathy and airy voice. The tone is solemn, tragic, and grave."

SPEAKER_DIALOGUE = "serena"
INSTRUCT_DIALOGUE = "A warm, rich, and expressive female voice. The tone is clear, engaging, and professional."

# [속도 설정]
SPEED_FACTOR = 1.30 # 1.30배속으로 상향

_tts_model = None

def get_tts_model():
    global _tts_model
    if _tts_model is None:
        print("📡 Qwen-TTS 멀티 스피커 엔진 가동 (bfloat16 + cuda)...")
        try:
            _tts_model = Qwen3TTSModel.from_pretrained(
                MODEL_ID,
                dtype=torch.bfloat16,
                device_map="cuda"
            )
        except Exception as e:
            print(f"⚠️ 로딩 실패 ({e}), 기본 모드로 재시도합니다...")
            _tts_model = Qwen3TTSModel.from_pretrained(MODEL_ID, device_map="auto")
    return _tts_model

def clean_for_output(text):
    text = re.sub(r'\[(BGM|묘사|지문|설명|배경|음악|CHAPTER|챕터|SFX):?.*?\]', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\[(대사|지문|묘사|설명)\]', '', text)
    text = re.sub(r'\(.*?\)', '', text)
    symbols = ['*', '-', '#', '@', '+', '=', '>', '<', '|', '/', '\\', '^']
    for s in symbols: text = text.replace(s, '')
    return text.strip()

def fix_initial_law(text):
    text = re.sub(r'(\d)\.(\d)', r'\1 쩜 \2', text)
    corrections = {"녀자": "여자", "래일": "내일", "리용": "이용", "량심": "양심", "력사": "역사", "련합": "연합"}
    for wrong, right in corrections.items(): text = text.replace(wrong, right)
    return text

def format_srt_time(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

def change_audio_speed(audio_segment, speed=1.0):
    if speed == 1.0: return audio_segment
    return audio_segment.speed_up(playback_speed=speed)

def parse_multi_speaker_text(text):
    # 따옴표(")를 기준으로 텍스트 분리
    # 예: 나레이션 "대사" 나레이션 "대사"
    pattern = r'("[^"]*")|([^"]+)'
    matches = re.finditer(pattern, text)
    
    segments = []
    for m in matches:
        dialogue = m.group(1)
        narration = m.group(2)
        
        if dialogue:
            content = dialogue.strip('"').strip()
            if content:
                segments.append({"type": "dialogue", "text": content})
        elif narration:
            content = narration.strip()
            if content:
                # 나레이션은 너무 길 수 있으므로 쉼표/마침표 기준으로 더 쪼갬 (배치 효율)
                sub_parts = re.split(r'(?<=[.!? ,])\s+', content)
                for p in sub_parts:
                    if p.strip():
                        segments.append({"type": "narration", "text": p.strip()})
    return segments

def generate_multi_speaker_batch(segments, tts):
    print(f"🚀 총 {len(segments)}개의 세그먼트 생성 시작 (멀티 스피커 배치 모드)...")
    
    # 스피커별로 그룹화하여 배치 처리
    narration_texts = []
    dialogue_texts = []
    segment_order = []  # 원래 순서 유지를 위한 인덱스
    
    for i, seg in enumerate(segments):
        cleaned = fix_initial_law(clean_for_output(seg["text"]))
        if seg["type"] == "narration":
            narration_texts.append(cleaned)
            segment_order.append(("narration", len(narration_texts) - 1))
        else:
            dialogue_texts.append(cleaned)
            segment_order.append(("dialogue", len(dialogue_texts) - 1))
    
    print(f"   📖 나레이션(소희): {len(narration_texts)}개")
    print(f"   💬 대사(세레나): {len(dialogue_texts)}개")
    
    # 배치 생성
    narration_wavs = []
    dialogue_wavs = []
    sr = None
    
    if narration_texts:
        print(f"🎙️ 나레이션 배치 생성 중 (소희)...")
        wavs, sr = tts.generate_custom_voice(
            text=narration_texts,
            speaker=SPEAKER_NARRATION,
            language="Korean",
            instruct=INSTRUCT_NARRATION
        )
        narration_wavs = wavs
    
    if dialogue_texts:
        print(f"🎙️ 대사 배치 생성 중 (세레나)...")
        wavs, sr = tts.generate_custom_voice(
            text=dialogue_texts,
            speaker=SPEAKER_DIALOGUE,
            language="Korean",
            instruct=INSTRUCT_DIALOGUE
        )
        dialogue_wavs = wavs
    
    # 원래 순서대로 재조립
    results = []
    for seg_type, idx in segment_order:
        if seg_type == "narration":
            results.append((narration_wavs[idx], sr, narration_texts[idx]))
        else:
            results.append((dialogue_wavs[idx], sr, dialogue_texts[idx]))
    
    return results

def merge_and_speed_up(parts_data, output_base_path, speed=1.0):
    print(f"\n📦 병합 및 {speed}배속 처리 시작...")
    try:
        combined_audio = AudioSegment.empty()
        combined_srt = ""
        current_offset_ms = 0
        srt_index = 1

        for i, (wav, sr, text) in enumerate(parts_data):
            temp_part_wav = f"temp_multi_{i}.wav"
            sf.write(temp_part_wav, wav, sr)
            audio_part = AudioSegment.from_wav(temp_part_wav)
            
            # 속도 조절
            if speed != 1.0:
                audio_part = change_audio_speed(audio_part, speed)
            
            combined_audio += audio_part
            duration_ms = len(audio_part)
            
            # SRT 자막 생성 (속도 조절된 시간 기준)
            sentences = re.split(r'(?<=[.!?])\s+', text)
            sentences = [s.strip() for s in sentences if s.strip()]
            total_chars = sum(len(s) for s in sentences)
            
            for sent in sentences:
                sent_duration_ms = (len(sent) / total_chars) * duration_ms if total_chars > 0 else 0
                start_sec = current_offset_ms / 1000.0
                end_sec = (current_offset_ms + sent_duration_ms) / 1000.0
                
                combined_srt += f"{srt_index}\n{format_srt_time(start_sec)} --> {format_srt_time(end_sec)}\n{sent}\n\n"
                srt_index += 1
                current_offset_ms += sent_duration_ms
            
            if os.path.exists(temp_part_wav): os.remove(temp_part_wav)

        audio_out = output_base_path + ".mp3"
        srt_out = output_base_path + ".srt"
        
        combined_audio.export(audio_out, format="mp3", bitrate="192k")
        with open(srt_out, "w", encoding="utf-8-sig") as f:
            f.write(combined_srt)
            
        return audio_out, srt_out
    except Exception as e:
        print(f"❌ 병합 중 오류: {e}")
        return None, None

if __name__ == "__main__":
    target_file = sys.argv[1] if len(sys.argv) > 1 else "/workspace/대본.txt"
    if not os.path.exists(target_file):
        print(f"❌ 대본 없음: {target_file}")
        sys.exit(1)

    with open(target_file, "r", encoding="utf-8") as f:
        full_text = f.read().strip()
    
    segments = parse_multi_speaker_text(full_text)
    tts = get_tts_model()
    
    audio_results = generate_multi_speaker_batch(segments, tts)
    
    if audio_results:
        timestamp = datetime.now().strftime("%m%d_%H%M")
        final_path = os.path.join(DOWNLOADS_DIR, f"Multi_Speaker_Turbo_{timestamp}")
        a_file, s_file = merge_and_speed_up(audio_results, final_path, speed=SPEED_FACTOR)
        
        if a_file:
            print(f"\n✨ 생성 완료!")
            print(f"   🔊 {os.path.basename(a_file)}")
            print(f"   📝 {os.path.basename(s_file)}")

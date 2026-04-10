from pydub import AudioSegment
import azure.cognitiveservices.speech as speechsdk
import os
import re
import sys
import datetime
import tempfile

# [1. 환경 및 경로 설정]
sys.stdout.reconfigure(encoding='utf-8')

ENGINE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJ_ROOT = os.path.dirname(ENGINE_DIR)
DOWNLOADS_DIR = os.path.join(os.path.expanduser("~"), "Downloads")
LIB_DIR = os.path.join(PROJ_ROOT, "Library")

# Azure Speech 설정
SPEECH_KEY = "21HfTF65JeOoI5mqoW5NfPYZcmG114R7AFzrjbk5HLRE4fqIua7NJQQJ99CAACNns7RXJ3w3AAAYACOGMfRn"
SPEECH_REGION = "koreacentral"
VOICE_NAME = "ko-KR-BongJinNeural" # 남성 성우 (봉진)

# speed = 1.2x (+20%)
PROSODY_RATE = "+20.00%"

# FFmpeg 설정 (pydub용)
FFMPEG_EXE = "ffmpeg"
AudioSegment.converter = FFMPEG_EXE

# --- [2. 텍스트 보정 및 유틸리티] ---

def clean_for_output(text):
    # 음성 합성용 텍스트 정리 (태그 제거)
    text = re.sub(r'\[(BGM|배경음|음악|묘사|지문|설명|배경|CHAPTER|챕터|SFX|효과음):?.*?\]', '', text, flags=re.IGNORECASE)
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

# --- [3. 메인 TTS 생성 엔진] ---

def generate_segment(text, temp_audio_path, start_ticks_offset=0, start_idx=1):
    speech_config = speechsdk.SpeechConfig(subscription=SPEECH_KEY, region=SPEECH_REGION)
    speech_config.set_speech_synthesis_output_format(speechsdk.SpeechSynthesisOutputFormat.Audio48Khz192KBitRateMonoMp3)
    
    clean_text = clean_for_output(text)
    if not clean_text: return [], 0, 0
    
    ssml_text = f'''
    <speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="ko-KR">
        <voice name="{VOICE_NAME}">
            <prosody rate="{PROSODY_RATE}" pitch="0.00%">{clean_text}</prosody>
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

def run_v2_single_output(script_text, output_path):
    # 3000자 단위로 안전하게 분할
    chunks, segment = [], ""
    for line in script_text.splitlines():
        if len(segment) + len(line) > 3000:
            chunks.append(segment.strip())
            segment = line + "\n"
        else: segment += line + "\n"
    if segment: chunks.append(segment.strip())

    combined_audio = AudioSegment.empty()
    all_srt_entries = []
    total_ticks_offset = 0
    current_idx = 1

    with tempfile.TemporaryDirectory() as tmp_dir:
        for i, chunk in enumerate(chunks):
            print(f"🎙️ [Part {i+1}/{len(chunks)}] Azure 생성 중 (남성/1.2배속)...")
            tmp_audio_path = os.path.join(tmp_dir, f"part_{i}.mp3")
            
            srt_part, last_ticks, next_idx = generate_segment(chunk, tmp_audio_path, total_ticks_offset, current_idx)
            
            if os.path.exists(tmp_audio_path):
                segment_audio = AudioSegment.from_mp3(tmp_audio_path)
                combined_audio += segment_audio
                all_srt_entries.extend(srt_part)
                total_ticks_offset += int(len(segment_audio) * 10000)
                current_idx = next_idx

    # 저장
    combined_audio.export(output_path, format="mp3", bitrate="192k")
    srt_path = output_path.replace(".mp3", ".srt")
    with open(srt_path, "w", encoding="utf-8-sig") as f:
        f.writelines(all_srt_entries)
    
    print(f"✅ 최종 파일 생성 완료: {os.path.basename(output_path)}")

if __name__ == "__main__":
    target_file = sys.argv[1] if len(sys.argv) > 1 else os.path.join(PROJ_ROOT, "대본.txt")
    print(f"📖 대본 파일을 읽는 중: {target_file}")
    
    if os.path.exists(target_file):
        with open(target_file, "r", encoding="utf-8") as f:
            script_text = f.read().strip()
        
        if script_text:
            timestamp = datetime.datetime.now().strftime("%m%d_%H%M")
            base_filename = os.path.splitext(os.path.basename(target_file))[0]
            output_name = f"{base_filename}_Azure_Male_Fast_{timestamp}.mp3"
            output_path = os.path.join(DOWNLOADS_DIR, output_name)
            
            print(f"🚀 [Mu-hyup 01-2] 아주르 남성 1.2배속 생성 시작")
            run_v2_single_output(script_text, output_path)
            print(f"✨ 작업 완료! 파일 위치: {DOWNLOADS_DIR}")
        else: print("❌ 대본 내용이 비어 있습니다.")
    else: print(f"❌ 대본 파일을 찾을 수 없습니다: {target_file}")

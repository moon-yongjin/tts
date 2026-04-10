import azure.cognitiveservices.speech as speechsdk
import os
import re
import sys
import os

# [경로 설정]
ENGINE_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(ENGINE_DIR)
sys.path.append(ENGINE_DIR)

# from pydub import AudioSegment
# import sfx_generator

# [1. 환경 및 경로 설정]
sys.stdout.reconfigure(encoding='utf-8')

# ⚠️ FFmpeg 경로 설정 (사용자 요청: 순수 음성/자막 생성 시 불필요하므로 비활성화)
# FFMPEG_PATH = r"C:\Users\moori\Downloads\ffmpeg-2026-01-07-git-af6a1dd0b2-essentials_build\ffmpeg-2026-01-07-git-af6a1dd0b2-essentials_build\bin\ffmpeg"
# FFMPEG_DIR = os.path.dirname(FFMPEG_PATH)

# if os.path.exists(FFMPEG_PATH):
#     AudioSegment.converter = FFMPEG_PATH
#     AudioSegment.ffmpeg = FFMPEG_PATH
#     AudioSegment.ffprobe = os.path.join(FFMPEG_DIR, "ffprobe")
#     os.environ["PATH"] += os.pathsep + FFMPEG_DIR
#     print(f"✅ FFmpeg/FFprobe 로드 성공")

# Azure Speech 설정
SPEECH_KEY = "21HfTF65JeOoI5mqoW5NfPYZcmG114R7AFzrjbk5HLRE4fqIua7NJQQJ99CAACNns7RXJ3w3AAAYACOGMfRn"
SPEECH_REGION = "koreacentral"
VOICE_NAME = "ko-KR-JiMinNeural" 

# [경로 설정]
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LIB_DIR = os.path.join(BASE_DIR, "Library")
SFX_DIR = os.path.join(LIB_DIR, "sfx")
PROJ_ROOT = os.path.join(LIB_DIR, "projects")

# [SFX 매핑]
SFX_MAP = {
    'WOOD_DOOR': 'wood_door.mp3',
    'WOOD_STICK': 'wood_stick.mp3',
    'COIN_DROP': 'coin_drop.mp3',
    'FATHER_SOB': 'father_sob.mp3',
    'SPLASH_DEEP': 'splash_deep.mp3',
    'PAGODA_BELL': 'temple_bell.mp3',
    'SEA_WAVES': 'sea_waves.mp3',
    'WIND_STORM': 'wind_storm.mp3',
    'SHIP_CREAK': 'ship_creak.mp3',
    'NIGHT_AMBI': 'night_ambi.mp3',
    'UNDERWATER': 'underwater.mp3',
}

# --- [2. 텍스트 처리 및 보정 함수] ---

def clean_for_output(text):
    text = re.sub(r'\[(BGM|묘사|지문|설명|배경|음악|CHAPTER|챕터):?.*?\]', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\[(대사|지문|묘사|설명)\]', '', text)
    text = re.sub(r'\(.*?\)', '', text)
    text = re.sub(r'\[SFX\]\s*:.*?(?=\[|$|\n\n)', '', text, flags=re.IGNORECASE)
    symbols = ['*', '-', '#', '@', '+', '=', '>', '<', '|', '/', '\\', '^']
    for s in symbols: text = text.replace(s, '')
    return text.strip()

def fix_ryul_yeol(text):
    def replace_func(match):
        pre_char, target = match.group(1), match.group(2)
        if not (0xAC00 <= ord(pre_char) <= 0xD7A3): return pre_char + target
        batchim = (ord(pre_char) - 0xAC00) % 28
        if batchim == 0 or batchim == 4:
            if target == '률': return pre_char + '율'
            if target == '렬': return pre_char + '열'
        else:
            if target == '율': return pre_char + '률'
            if target == '열': return pre_char + '렬'
        return pre_char + target
    return re.sub(r'([가-힣])([률율렬열])', replace_func, text)

def fix_initial_law(text):
    text = re.sub(r'(\d)\.(\d)', r'\1 쩜 \2', text)
    corrections = {"녀자": "여자", "래일": "내일", "리용": "이용", "량심": "양심", "력사": "역사", "련합": "연합"}
    for wrong, right in corrections.items(): text = text.replace(wrong, right)
    return fix_ryul_yeol(text)

def format_time(ticks):
    total_seconds = ticks / 10000000
    hours = int(total_seconds // 3600)
    minutes = int((total_seconds % 3600) // 60)
    seconds = int(total_seconds % 60)
    milliseconds = int((total_seconds * 1000) % 1000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"

# --- [3. 메인 TTS 생성 및 믹싱 함수] ---

def generate_voice(text, output_path, start_index=1):
    speech_config = speechsdk.SpeechConfig(subscription=SPEECH_KEY, region=SPEECH_REGION)
    speech_config.set_speech_synthesis_output_format(speechsdk.SpeechSynthesisOutputFormat.Audio48Khz192KBitRateMonoMp3)
    
    text = re.sub(r'(\[)?\s*\d{2}:\d{2}(:\d{2})?(\s*~\s*\d{2}:\d{2}(:\d{2})?)?(\])?', '', text)
    text = re.sub(r'\b\d{4,}\b', '', text)
    text = clean_for_output(text)
    if not text.strip(): return 0
    
    text = fix_initial_law(text)
    ssml_ready = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    
    sfx_matches = []
    def protect_sfx(m):
        sfx_matches.append(m.group(0)); return f"__SFX__{len(sfx_matches)-1}__"
    ssml_ready = re.sub(r'\[SFX:[^\]]+\]', protect_sfx, ssml_ready)

    styles = {'대사': 'pitch="+21.00%" rate="+0.00%"', '속삭임': 'volume="-40.00%" rate="-10.00%"', '호통': 'volume="+30.00%" pitch="+0.00%"'}
    def apply_style(m):
        t, c = m.group(1), m.group(2)
        return f'<prosody {styles.get(t, "")}>{c}</prosody>' if t in styles else m.group(0)

    ssml_ready = re.sub(r'\((대사|속삭임|호통)\)\s*"([^"]+)"', apply_style, ssml_ready)
    # ssml_ready = re.sub(r'(?<!>)"([^"]+)"', r'<prosody pitch="+21.00%" rate="+0.00%">"\1"</prosody>', ssml_ready)

    custom_pron = {"안방": "안빵", "손바닥": "손빠닥", "문고리": "문꼬리", "속셈": "속쌤", "탕약": "탕냑", "가락지": "가락찌", "내쫓다": "내쫃따", "죄값이": "죄깝시", "명줄을": "명쭐을", "녀자": "여자", "송곳이": "송고시", "열쇠": "열쐬"}
    inverse_pron = {v: k for k, v in custom_pron.items()}
    for k, v in custom_pron.items(): ssml_ready = ssml_ready.replace(k, f'<sub alias="{v}">{k}</sub>')

    def restore_sfx(m): return sfx_matches[int(m.group(1))]
    ssml_ready = re.sub(r'__SFX__(\d+)__', restore_sfx, ssml_ready)
    
    def create_bookmark(m):
        content = m.group(1).replace('"', "&quot;").replace("'", "&apos;")
        return f'<bookmark mark="SFX:{content}"/>'
    ssml_ready = re.sub(r'\[SFX:([^\]]+)\]', create_bookmark, ssml_ready)

    ssml_text = f'<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="ko-KR"><voice name="{VOICE_NAME}"><prosody rate="-10.00%" pitch="-5.00%">{ssml_ready}</prosody></voice></speak>'

    audio_config = speechsdk.audio.AudioOutputConfig(filename=output_path)
    synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)

    srt_entries, current_words = [], []
    current_start_ticks, last_end_ticks = None, 0
    mixing_plan = []
    current_idx = start_index

    def word_boundary_handler(evt):
        nonlocal current_words, current_start_ticks, last_end_ticks, current_idx
        raw_word = evt.text
        pure_word = re.sub(r'[^a-zA-Z가-힣0-9]', '', raw_word)
        restored = inverse_pron.get(pure_word, pure_word)
        target_text = raw_word.replace(pure_word, restored)
        clean_word = clean_for_output(target_text).strip()
        if not clean_word: return
        
        if current_words:
            if len(" ".join(current_words + [clean_word])) > 12:
                srt_entries.append(f"{current_idx}\n{format_time(current_start_ticks)} --> {format_time(last_end_ticks)}\n{' '.join(current_words)}\n\n")
                current_words, current_start_ticks, current_idx = [], None, current_idx + 1

        last_end_ticks = evt.audio_offset + int(evt.duration.total_seconds() * 10000000)
        if not current_words: current_start_ticks = evt.audio_offset
        current_words.append(clean_word)
        
        if any(clean_word.endswith(p) for p in ['.', '?', '!', '~']):
            srt_entries.append(f"{current_idx}\n{format_time(current_start_ticks)} --> {format_time(last_end_ticks)}\n{' '.join(current_words)}\n\n")
            current_words, current_start_ticks, current_idx = [], None, current_idx + 1

    def bookmark_handler(evt):
        raw_tag = evt.text.replace("SFX:", "")
        filename = SFX_MAP.get(raw_tag, f"{raw_tag}.mp3")
        sfx_path = os.path.join(SFX_DIR, filename)
        if os.path.exists(sfx_path):
            mixing_plan.append({'time': evt.audio_offset // 10000, 'file': sfx_path})
            print(f"📍 SFX 예약: {raw_tag}")

    synthesizer.synthesis_word_boundary.connect(word_boundary_handler)
    synthesizer.bookmark_reached.connect(bookmark_handler)

    print(f"\n──────────────────────────────────────────────────")
    print(f"🎙️ 생성 시작: {os.path.basename(output_path)}")
    print(f"📖 대본 내용:\n{text}")
    print(f"──────────────────────────────────────────────────\n")
    result = synthesizer.speak_ssml_async(ssml_text).get()

    if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        if current_words:
            srt_entries.append(f"{current_idx}\n{format_time(current_start_ticks)} --> {format_time(last_end_ticks)}\n{' '.join(current_words)}\n\n")
            current_idx += 1
        
        with open(output_path.replace(".mp3", ".srt"), "w", encoding="utf-8-sig") as f: f.writelines(srt_entries)
        
        # [사용자 요청 반영] SFX 믹싱 비활성화 (순수 음성/자막 생성 집중)
        # if mixing_plan:
        #     try:
        #         main_audio = AudioSegment.from_mp3(output_path)
        #         for item in mixing_plan:
        #             sfx = AudioSegment.from_mp3(item['file']) - 5
        #             main_audio = main_audio.overlay(sfx, position=item['time'])
        #         main_audio.export(output_path, format="mp3")
        #     except Exception as e: print(f"⚠️ 믹싱 오류: {e}")
        
        print(f"✅ 완성: {os.path.basename(output_path)}")
        return current_idx - start_index
    return 0

# --- [4. 실행 진입점] ---

if __name__ == "__main__":
    target_file = sys.argv[1] if len(sys.argv) > 1 else "대본.txt"
    
if __name__ == "__main__":
    target_file = sys.argv[1] if len(sys.argv) > 1 else "대본.txt"
    
    if os.path.exists(target_file):
        script_path = os.path.abspath(target_file)
    else:
        script_path = os.path.join(os.path.dirname(__file__), target_file)

    if os.path.exists(script_path):
        print(f"📄 대본 파일 로드: {script_path}")
        with open(script_path, "r", encoding="utf-8") as f: 
            script_text = f.read().strip()
        
        if script_text:
            # 텍스트 분할 (2000자 단위)
            chunks, segment = [], ""
            for line in script_text.splitlines():
                if len(segment) + len(line) > 2000:
                    chunks.append(segment.strip())
                    segment = line + "\n"
                else: 
                    segment += line + "\n"
            if segment: chunks.append(segment.strip())
            
            # 프로젝트 폴더 설정
            project_dir = os.path.join(PROJ_ROOT, os.path.splitext(os.path.basename(target_file))[0])
            if not os.path.exists(project_dir): 
                os.makedirs(project_dir)

            # 자막 인덱스 초기화
            global_sub_idx = 1
            
            for i, chunk in enumerate(chunks):
                if not chunk.strip(): continue
                
                from datetime import datetime
                timestamp = datetime.now().strftime("%m%d_%H%M")
                base_name = f"{os.path.splitext(os.path.basename(target_file))[0]}_{timestamp}"
                part_name = f"{base_name}_part{i+1}.mp3"
                
                # ✅ 수정: 파일을 다운로드 폴더에 직접 저장
                full_path = os.path.join(os.environ['USERPROFILE'], 'Downloads', part_name)
                
                print(f"🚀 Part {i+1} 진행 중 (자막: 1번부터)")
                
                # ✅ 수정: 캡컷 호환성을 위해 무조건 1번부터 시작 (global_sub_idx 대신 1 고정)
                generate_voice(chunk, full_path, start_index=1)

            print(f"\n✨ 모든 작업이 완료되었습니다! 결과물 위치: {os.path.join(os.environ['USERPROFILE'], 'Downloads')}")
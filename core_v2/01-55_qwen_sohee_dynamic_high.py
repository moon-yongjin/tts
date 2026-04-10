import os
import sys
import time
import re
import datetime
import numpy as np
import soundfile as sf
import tempfile
from pydub import AudioSegment
import mlx.core as mx
from mlx_audio.tts import load 

# ==========================================================
# [사용자 설정 구역] - Step 01-55: 고속 + 다이나믹 피치
# ==========================================================

# 1. 목소리 기본 설정
SPEAKER = "sohee"

# 2. 기본 속도 및 피치
SPEED = 1.2              # 1.0이 기본 속도 (사장님 요청: 1.2)
PITCH_NARRATION = -1.5   # 나레이션 (할머니 톤)
PITCH_DIALOGUE = 1.5     # 대사 (밝고 생기 있는 톤)

# 3. 문장 사이 쉬는 시간 (ms)
PAUSE_MS = 600           # 속도가 빠르므로 쉼표도 조금 단축

# 4. 연기 지시문 (AI에게 내리는 명령)
INSTRUCT = "70대 이상의 나이가 지긋한 할머니 목소리로 연기하세요. 상황에 따라 감정을 실어 자연스럽게 낭독하세요."

# 5. 생성 파라미터
GEN_KWARGS = {
    "temperature": 0.0,
    "top_p": 1.0,
    "repetition_penalty": 1.5
}
# ==========================================================

# [1. 환경 및 경로 설정]
sys.stdout.reconfigure(encoding='utf-8')

ENGINE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJ_ROOT = os.path.dirname(ENGINE_DIR)
DOWNLOADS_DIR = os.path.join(os.path.expanduser("~"), "Downloads")
MODEL_ID = "mlx-community/Qwen3-TTS-12Hz-1.7B-CustomVoice-bf16"

class dialogue_aware_qwen_generator:
    def __init__(self):
        print(f"🚀 [LOCAL] Step 01-55 엔진 가동 중: {MODEL_ID}")
        self.model = load(MODEL_ID)
        print("✅ 모델 로딩 완료!")

    def is_dialogue(self, text):
        """
        따옴표 없이도 대사인지 판단하는 로직 (정교화)
        """
        # 1. 따옴표가 있으면 확실한 대사
        if '"' in text or "'" in text:
            return True
        
        # 2. 문장 끝 처리 (문장 부호 제거 후 판단)
        clean_text = text.strip()
        # 문장 끝의 . ! ? \s 제거
        end_stripped = re.sub(r'[.!?\s]+$', '', clean_text)
        
        # 구어체 종결어미 패턴 (끝이 요, 죠, 니, 나, 까, 라, 마 등으로 끝나는지)
        spoken_endings = [
            r'요$', r'죠$', r'니$', r'나$', r'까$', r'어$', r'가$', r'어라$', r'구나$', r'단다$', 
            r'마$', r'라$', r'군$', r'네$'
        ]
        
        if any(re.search(pattern, end_stripped) for pattern in spoken_endings):
            # 단, "~했죠", "~했었죠" 처럼 긴 서술형 나레이션은 제외할 수 있도록 보강
            # 여기서는 사용자 요청에 따라 최대한 대사로 인식하도록 설정
            return True
            
        # 3. 1인칭/2인칭 대명사 및 호칭 시작 패턴
        dialogue_keywords = [
            '아버지', '어머니', '언니', '형님', '자네', '너 ', '나 ', '우리', '제가', '제발', '여보', '자기야', '얘야'
        ]
        if any(clean_text.startswith(k) for k in dialogue_keywords):
            return True
            
        return False
    def clean_text(self, text):
        text = re.sub(r'\[(BGM|묘사|지문|설명|배경|음악|CHAPTER|챕터|SFX):?.*?\]', '', text, flags=re.IGNORECASE)
        # 괄호 지문 삭제
        text = re.sub(r'\(.*?\)', '', text)
        return text.strip()

    def split_segments(self, text):
        """대사와 나레이션을 분리하여 리스트로 반환"""
        # 따옴표 기준으로 먼저 분리
        raw_parts = re.split(r'(\".*?\")|(\'.*?\')', text)
        segments = []
        
        for p in raw_parts:
            if not p: continue
            p = p.strip()
            if not p: continue
            
            # 따옴표가 있는 경우
            if (p.startswith('"') and p.endswith('"')) or (p.startswith("'") and p.endswith("'")):
                segments.append({'text': p.strip('"\''), 'is_dialogue': True})
            else:
                # 따옴표 없는 구간은 문장 단위로 쪼개서 대사 여부 판별
                sentences = re.split(r'([.!?]\s+)', p)
                current_text = ""
                for i in range(0, len(sentences), 2):
                    s = sentences[i]
                    punct = sentences[i+1] if i+1 < len(sentences) else ""
                    combined = (s + punct).strip()
                    if not combined: continue
                    
                    is_dial = self.is_dialogue(combined)
                    segments.append({'text': combined, 'is_dialogue': is_dial})
                    
        return segments

    def format_srt_time(self, seconds):
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

    def shift_pitch(self, sound, semitones):
        if semitones == 0: return sound
        new_sample_rate = int(sound.frame_rate * (2.0 ** (semitones / 12.0)))
        return sound._spawn(sound.raw_data, overrides={'frame_rate': new_sample_rate}).set_frame_rate(sound.frame_rate)

    def run(self, script_path):
        if not os.path.exists(script_path):
            print(f"❌ 대본 파일을 찾을 수 없습니다: {script_path}")
            return

        with open(script_path, "r", encoding="utf-8") as f:
            full_text = f.read().strip()
        
        print(f"📄 대본 분석 완료 ({len(full_text)}자)")
        segments = self.split_segments(self.clean_text(full_text))
        print(f"📦 총 {len(segments)}개의 세그먼트를 생성합니다.")

        timestamp = datetime.datetime.now().strftime("%m%d_%H%M")
        base_filename = f"Qwen_Sohee_V1-55_" + timestamp
        
        combined_audio = AudioSegment.empty()
        srt_content = []
        current_time_ms = 0

        for i, seg in enumerate(segments):
            text = seg['text']
            is_dial = seg['is_dialogue']
            target_pitch = PITCH_DIALOGUE if is_dial else PITCH_NARRATION
            type_str = "[대사]" if is_dial else "[나레이션]"
            
            print(f"🎙️  [{i+1}/{len(segments)}] {type_str} (Pitch:{target_pitch}): {text[:20]}...")
            
            try:
                results = self.model.generate(
                    text=text, voice=SPEAKER, language="Korean", instruct=INSTRUCT, **GEN_KWARGS
                )
                
                segment_audio_mx = None
                for res in results:
                    if segment_audio_mx is None: segment_audio_mx = res.audio
                    else: segment_audio_mx = mx.concatenate([segment_audio_mx, res.audio])
                
                if segment_audio_mx is None: continue
                
                audio_np = np.array(segment_audio_mx)
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                    sf.write(tmp.name, audio_np, 24000)
                    audio_segment = AudioSegment.from_wav(tmp.name)
                os.unlink(tmp.name)

                # 피치 조절
                if target_pitch != 0:
                    audio_segment = self.shift_pitch(audio_segment, target_pitch)
                
                # 속도 조절 (피치 변경에 따른 속도 변화 상쇄 포함)
                pitch_speed_change = 2.0 ** (target_pitch / 12.0)
                final_speedup = SPEED / pitch_speed_change
                if final_speedup != 1.0:
                    if final_speedup > 1.0:
                        audio_segment = audio_segment.speedup(playback_speed=final_speedup, chunk_size=150, crossfade=25)
                    else:
                        new_rate = int(audio_segment.frame_rate / final_speedup)
                        audio_segment = audio_segment._spawn(audio_segment.raw_data, overrides={'frame_rate': new_rate}).set_frame_rate(audio_segment.frame_rate)

                # 쉼표(Pause)
                pause = AudioSegment.silent(duration=PAUSE_MS)
                
                # SRT 정보
                start_sec = current_time_ms / 1000.0
                duration_ms = len(audio_segment)
                end_sec = (current_time_ms + duration_ms) / 1000.0
                srt_content.append(f"{i+1}\n{self.format_srt_time(start_sec)} --> {self.format_srt_time(end_sec)}\n{text}\n")
                
                combined_audio += audio_segment + pause
                current_time_ms += duration_ms + PAUSE_MS
            except Exception as e:
                print(f"   ❌ 생성 중 오류 발생: {e}")

        final_mp3_path = os.path.join(DOWNLOADS_DIR, base_filename + ".mp3")
        final_srt_path = os.path.join(DOWNLOADS_DIR, base_filename + ".srt")
        
        combined_audio.export(final_mp3_path, format="mp3", bitrate="192k")
        with open(final_srt_path, "w", encoding="utf-8-sig") as f:
            f.write("\n".join(srt_content))
            
        print(f"\n✨ 생성 완료! (Speed:{SPEED}, P_Dial:{PITCH_DIALOGUE}, P_Narr:{PITCH_NARRATION})")
        print(f"📂 결과 MP3: {final_mp3_path}")
        print(f"📂 결과 SRT: {final_srt_path}")

if __name__ == "__main__":
    script = sys.argv[1] if len(sys.argv) > 1 else os.path.join(PROJ_ROOT, "대본.txt")
    gen = dialogue_aware_qwen_generator()
    gen.run(script)

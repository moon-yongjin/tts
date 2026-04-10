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

# [필요 환경 설정]
sys.stdout.reconfigure(encoding='utf-8')
DOWNLOADS_DIR = os.path.join(os.path.expanduser("~"), "Downloads")
MODEL_ID = "mlx-community/Qwen3-TTS-12Hz-1.7B-CustomVoice-bf16"
SPEAKER = "sohee"

# ==========================================================
# [자동 분리 설정] - 따옴표 안과 밖의 톤과 속도를 다르게 설정합니다.
# ==========================================================

# 1. 내레이션 (따옴표 밖) - 할머니 톤
NARRATION_PITCH = 0.0          # 기본 피치
NARRATION_SPEED = 1.1          # 1.1배속 (약간 빠르게)
NARRATION_INSTRUCT = "정확한 서울 표준어를 사용하는 70대 할머니 성우입니다. 중국어나 외국어 억양을 절대 섞지 말고 순수 한국어 어조로 차분하게 낭독하세요."

# 2. 대사 (따옴표 안) - 젊은 딸 톤
DIALOGUE_PITCH = 1.5           # 고음
DIALOGUE_SPEED = 1.0           # 정속
DIALOGUE_INSTRUCT = "서울 표준어를 사용하는 20대 여성 성우입니다. 중국어 억양을 절대 배제하고 날카로운 한국어 어조로 연기하세요."

PAUSE_MS = 800
# ==========================================================

class auto_modulating_generator:
    def __init__(self):
        print(f"🚀 [AUTO] 모델 로딩 중: {MODEL_ID}")
        self.model = load(MODEL_ID)
        print("✅ 로딩 완료!")

    def parse_script_by_quotes(self, text):
        """따옴표를 기준으로 내레이션과 대사를 자동 분리"""
        segments = []
        raw_parts = re.split(r'("(?:[^"]*)")', text)
        
        for part in raw_parts:
            part = part.strip()
            if not part: continue
            
            if part.startswith('"') and part.endswith('"'):
                content = part[1:-1].strip()
                segments.append({
                    "text": content,
                    "pitch": DIALOGUE_PITCH,
                    "speed": DIALOGUE_SPEED,
                    "instruct": DIALOGUE_INSTRUCT,
                    "type": "DIALOGUE"
                })
            else:
                segments.append({
                    "text": part,
                    "pitch": NARRATION_PITCH,
                    "speed": NARRATION_SPEED,
                    "instruct": NARRATION_INSTRUCT,
                    "type": "NARRATION"
                })
        return segments

    def shift_pitch(self, sound, semitones):
        if semitones == 0: return sound
        new_sample_rate = int(sound.frame_rate * (2.0 ** (semitones / 12.0)))
        return sound._spawn(sound.raw_data, overrides={'frame_rate': new_sample_rate}).set_frame_rate(sound.frame_rate)

    def run(self, script_path):
        if not os.path.exists(script_path):
            print(f"❌ 대본 없음: {script_path}")
            return

        with open(script_path, "r", encoding="utf-8") as f:
            full_text = f.read().strip()
            
        print("🔍 대본 분석 중 (피치/속도 자동 변조 모드)...")
        segments = self.parse_script_by_quotes(full_text)
        print(f"📦 총 {len(segments)}개의 세그먼트 분석 완료")

        timestamp = datetime.datetime.now().strftime("%m%d_%H%M")
        base_filename = f"Qwen_Hybrid_S1.1P1.5_" + timestamp
        
        combined_audio = AudioSegment.empty()

        for i, seg in enumerate(segments):
            text = seg["text"]
            pitch = seg["pitch"]
            speed = seg["speed"]
            instruct = seg["instruct"]
            seg_type = seg["type"]
            
            print(f"\n🎙️  세그먼트 {i+1} [{seg_type}]")
            print(f"   💬 텍스트: {text[:40]}...")
            print(f"   📉 피치: {pitch} / ⚡ 속도: {speed}")
            
            try:
                results = self.model.generate(
                    text=text, voice=SPEAKER, language="Korean", instruct=instruct, 
                    temperature=0.0, top_p=1.0, repetition_penalty=1.5
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

                # 1. 피치 변조
                if pitch != 0:
                    audio_segment = self.shift_pitch(audio_segment, pitch)

                # 2. 속도 변조 (피치 변경에 따른 속도 변화 보정 포함)
                pitch_speed_change = 2.0 ** (pitch / 12.0)
                final_speedup = speed / pitch_speed_change
                
                if final_speedup > 1.0:
                    audio_segment = audio_segment.speedup(playback_speed=final_speedup, chunk_size=150, crossfade=25)
                elif final_speedup < 1.0:
                    new_rate = int(audio_segment.frame_rate / final_speedup)
                    audio_segment = audio_segment._spawn(audio_segment.raw_data, overrides={'frame_rate': new_rate}).set_frame_rate(audio_segment.frame_rate)

                # 쉼표 추가
                combined_audio += audio_segment + AudioSegment.silent(duration=PAUSE_MS)
                
            except Exception as e:
                print(f"   ❌ 오류 발생: {e}")

        # 최종 저장
        final_mp3_path = os.path.join(DOWNLOADS_DIR, base_filename + ".mp3")
        combined_audio.export(final_mp3_path, format="mp3", bitrate="192k")
        print(f"\n✨ 하이브리드 자동 변조 생성 완료! 파일 확인: {final_mp3_path}")

if __name__ == "__main__":
    script = sys.argv[1] if len(sys.argv) > 1 else "/Users/a12/projects/tts/대본.txt"
    gen = auto_modulating_generator()
    gen.run(script)

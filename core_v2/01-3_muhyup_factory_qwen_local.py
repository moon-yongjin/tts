import os
import sys
import torch
import soundfile as sf
import time
import json
import re
from qwen_tts import Qwen3TTSModel
from datetime import datetime, UTC
from pydub import AudioSegment
import io

# [1. 환경 및 경로 설정]
sys.stdout.reconfigure(encoding='utf-8')

ENGINE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJ_ROOT = os.path.dirname(ENGINE_DIR)
DOWNLOADS_DIR = os.path.join(os.path.expanduser("~"), "Downloads")

# [Qwen-TTS 설정 (Stability Tuning)]
MODEL_ID = "Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice"
SPEAKER = "eric" # 남성 성우
# 안정성을 위해 한국어 전용 지침 강화 및 외국어 사용 금지 명시
INSTRUCT = "A deep, professional, and clear voice of a 40-year-old man. The tone is firm and authoritative. Speak strictly in Korean ONLY. Do not use any foreign languages or hallucinate other sounds."
SPEED_FACTOR = 1.2

# 생성 파라미터 튜닝 (안정성 위주)
GEN_KWARGS = {
    "temperature": 0.5,       # 낮을수록 안정적이고 일관됨 (기존 0.9)
    "top_p": 0.8,            # 샘플링 범위를 좁혀 헛소리 방지 (기존 1.0)
    "repetition_penalty": 1.2, # 반복되는 패턴이나 버벅임 방지 (기존 1.05)
    "do_sample": True
}

# FFmpeg 설정 (pydub용)
FFMPEG_EXE = "ffmpeg"
AudioSegment.converter = FFMPEG_EXE

class QwenLocalGenerator:
    def __init__(self):
        self.device = "mps" if torch.backends.mps.is_available() else "cpu"
        # Apple Silicon(M4 Pro)에서는 bfloat16이 최적입니다.
        self.dtype = torch.bfloat16 if self.device == "mps" else torch.float32
        print(f"📡 모델 로딩 중 ({self.device}, {self.dtype})...")
        
        self.tts_model = Qwen3TTSModel.from_pretrained(
            MODEL_ID, 
            device_map=self.device,
            torch_dtype=self.dtype, # 명시적 타입 지정으로 메모리 대역폭 절약
            low_cpu_mem_usage=True # 로드 시 RAM 사용량 최적화
        )
        print("✅ Qwen-TTS 로딩 완료!")

    def clean_text(self, text):
        text = re.sub(r'\[(BGM|묘사|지문|설명|배경|음악|CHAPTER|챕터|SFX):?.*?\]', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\[(대사|지문|묘사|설명)\]', '', text)
        text = re.sub(r'\(.*?\)', '', text)
        return text.strip()

    def format_srt_time(self, seconds):
        td = datetime.fromtimestamp(seconds, UTC)
        return td.strftime('%H:%M:%S,%f')[:-3]

    def split_chunks(self, text):
        # 문장 단위 및 쉼표 단위 분할 (마침표, 물음표, 느낌표, 쉼표 기준)
        chunks = re.split(r'(?<=[.,!?])\s*', text)
        return [c.strip() for c in chunks if c.strip()]

    def run(self, script_text, output_path):
        chunks = self.split_chunks(self.clean_text(script_text))
        print(f"📦 Total Chunks: {len(chunks)}")
        
        combined_audio = AudioSegment.empty()
        srt_entries = []
        current_time_ms = 0
        
        start_time = time.time()
        
        with torch.inference_mode():
            for i, chunk in enumerate(chunks):
                print(f"⏳ [{i+1}/{len(chunks)}] Generating: {chunk[:30]}...")
                
                # Qwen-TTS 생성 (튜닝된 파라미터 적용)
                wavs, sr = self.tts_model.generate_custom_voice(
                    text=chunk, 
                    speaker=SPEAKER, 
                    language="Korean", 
                    instruct=INSTRUCT,
                    **GEN_KWARGS
                )
                
                # BytesIO를 통해 pydub AudioSegment로 변환
                buf = io.BytesIO()
                sf.write(buf, wavs[0], sr, format='WAV')
                buf.seek(0)
                segment = AudioSegment.from_wav(buf)
                
                # 속도 조절 (SPEED_FACTOR)
                if SPEED_FACTOR != 1.0:
                    segment = segment.speedup(playback_speed=SPEED_FACTOR, chunk_size=150, crossfade=25)
                
                duration_ms = len(segment)
                
                # 머지 및 시간 업데이트
                combined_audio += segment
                
                # SRT 엔트리 추가
                start_sec = current_time_ms / 1000.0
                end_sec = (current_time_ms + duration_ms) / 1000.0
                srt_entries.append(f"{i + 1}\n{self.format_srt_time(start_sec)} --> {self.format_srt_time(end_sec)}\n{chunk}\n\n")
                
                current_time_ms += duration_ms

                # ✅ 문장 끝/쉼표에 따른 휴식 추가 (마지막 청크 제외)
                if i < len(chunks) - 1:
                    pause_ms = 0
                    if any(chunk.endswith(p) for p in ['.', '?', '!']):
                        pause_ms = 500 # 문장 끝: 0.5초
                    elif chunk.endswith(','):
                        pause_ms = 200 # 쉼표: 0.2초
                    else:
                        pause_ms = 100 # 기본 간격
                    
                    if pause_ms > 0:
                        combined_audio += AudioSegment.silent(duration=pause_ms)
                        current_time_ms += pause_ms

        # 파일 저장
        combined_audio.export(output_path, format="mp3", bitrate="192k")
        srt_path = output_path.replace(".mp3", ".srt")
        with open(srt_path, "w", encoding="utf-8-sig") as f:
            f.writelines(srt_entries)
            
        elapsed = time.time() - start_time
        print(f"✅ 생성 완료: {os.path.basename(output_path)} ({elapsed:.1f}s)")
        print(f"📂 경로: {output_path}")

if __name__ == "__main__":
    target_file = sys.argv[1] if len(sys.argv) > 1 else os.path.join(PROJ_ROOT, "대본.txt")
    
    if os.path.exists(target_file):
        with open(target_file, "r", encoding="utf-8") as f:
            script_text = f.read().strip()
        
        if script_text:
            timestamp = datetime.now().strftime("%m%d_%H%M")
            base_filename = os.path.splitext(os.path.basename(target_file))[0]
            output_name = f"{base_filename}_Qwen_Local_Sent_{timestamp}.mp3"
            output_path = os.path.join(DOWNLOADS_DIR, output_name)
            
            generator = QwenLocalGenerator()
            generator.run(script_text, output_path)
        else: print("❌ 대본 내용이 비어 있습니다.")
    else: print(f"❌ 대본 파일을 찾을 수 없습니다: {target_file}")

import os
import sys
import time
import re
import datetime
import tempfile
import numpy as np
import soundfile as sf
from pydub import AudioSegment
import mlx.core as mx
from mlx_audio.tts import load 

# [1. 환경 및 경로 설정]
sys.stdout.reconfigure(encoding='utf-8')

ENGINE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJ_ROOT = os.path.dirname(ENGINE_DIR)
DOWNLOADS_DIR = os.path.join(os.path.expanduser("~"), "Downloads")

# [Qwen-TTS MLX 설정]
MODEL_ID = "mlx-community/Qwen3-TTS-12Hz-1.7B-CustomVoice-8bit"

# 생성할 8명의 성우 리스트 (uncle_fu 제외)
# 모델 지원 목록: ['serena', 'vivian', 'uncle_fu', 'ryan', 'aiden', 'ono_anna', 'sohee', 'eric', 'dylan']
SPEAKERS = ["serena", "vivian", "ryan", "aiden", "ono_anna", "sohee", "eric", "dylan"]

# 3단계 방어: 극단적 언어 제약
INSTRUCT = """당신은 서울 표준어를 사용하는 성우입니다. 
중국어나 영어 억양을 절대 섞지 말고, 정확하고 단호한 한국어 어조로만 낭독하세요. 
차분하고 비장하게 읽으세요. 어떤 외국어도 섞지 마세요."""

SPEED_FACTOR = 1.1

# 극단적 결정론 설정
GEN_KWARGS = {
    "temperature": 0.0,      # 완전 결정론적 생성
    "top_p": 1.0,            # 최고 확률 토큰만 선택
    "repetition_penalty": 1.5 # 반복 및 이상 발음 억제
}

MAX_RETRIES = 2

class QwenMultiVoiceGenerator:
    def __init__(self):
        print(f"🚀 MLX 모델 로딩 중: {MODEL_ID}")
        self.model = load(MODEL_ID)

    def clean_text(self, text):
        text = re.sub(r'\[(BGM|묘사|지문|설명|배경|음악|CHAPTER|챕터|SFX):?.*?\]', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\(.*?\)', '', text)
        return text.strip()

    def split_chunks(self, text, max_chars=45):
        """텍스트를 자연스러운 청크로 분할 (01-3 방식)"""
        sentences = re.split(r'([.!?]\s*)', text)
        chunks = []
        current_chunk = ""
        
        for i in range(0, len(sentences), 2):
            sentence = sentences[i]
            punctuation = sentences[i+1] if i+1 < len(sentences) else ""
            full_sentence = sentence + punctuation
            
            if len(full_sentence) > max_chars:
                words = full_sentence.split()
                temp = ""
                for word in words:
                    if len(temp) + len(word) + 1 <= max_chars:
                        temp += word + " "
                    else:
                        if temp:
                            chunks.append(temp.strip())
                        temp = word + " "
                if temp:
                    chunks.append(temp.strip())
            else:
                if len(current_chunk) + len(full_sentence) <= max_chars:
                    current_chunk += full_sentence
                else:
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                    current_chunk = full_sentence
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        return [c for c in chunks if c]

    def generate_for_speaker(self, speaker, script_text, base_filename):
        timestamp = datetime.datetime.now().strftime("%m%d_%H%M")
        output_name = f"{base_filename}_{speaker}_{timestamp}.mp3"
        output_path = os.path.join(DOWNLOADS_DIR, output_name)
        
        chunks = self.split_chunks(self.clean_text(script_text))
        print(f"\n🎙️  성우 생성 시작: {speaker} ({len(chunks)} 청크)")
        
        combined_audio = AudioSegment.empty()
        
        for i, chunk in enumerate(chunks):
            print(f"   ⚡ [{speaker} {i+1}/{len(chunks)}] {chunk[:30]}...")
            
            # 생성 시도
            segment_audio_mx = None
            for attempt in range(MAX_RETRIES):
                try:
                    results = self.model.generate(
                        text=chunk, 
                        voice=speaker, 
                        language="Korean",
                        instruct=INSTRUCT,
                        **GEN_KWARGS
                    )
                    
                    segment_audio_mx = None
                    for res in results:
                        if segment_audio_mx is None:
                            segment_audio_mx = res.audio
                        else:
                            segment_audio_mx = mx.concatenate([segment_audio_mx, res.audio])
                    
                    if segment_audio_mx is not None:
                        break
                except Exception as e:
                    print(f"   ⚠️ 시도 {attempt + 1}: {e}")
            
            if segment_audio_mx is None:
                continue
                
            audio_np = np.array(segment_audio_mx)
            shared_buf = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
            sf.write(shared_buf.name, audio_np, 24000)
            shared_buf.close()
            
            segment = AudioSegment.from_wav(shared_buf.name)
            os.unlink(shared_buf.name)
            
            if SPEED_FACTOR != 1.0:
                segment = segment.speedup(playback_speed=SPEED_FACTOR, chunk_size=150, crossfade=25)
            
            combined_audio += segment
            
            # 쉼표
            pause_ms = 400 if any(chunk.endswith(p) for p in ['.', '?', '!']) else 150
            combined_audio += AudioSegment.silent(duration=pause_ms)

        combined_audio.export(output_path, format="mp3", bitrate="192k")
        print(f"✅ 완료: {output_name}")

    def run_all(self, script_text, target_file):
        base_filename = os.path.splitext(os.path.basename(target_file))[0]
        for speaker in SPEAKERS:
            self.generate_for_speaker(speaker, script_text, base_filename)

if __name__ == "__main__":
    target_file = sys.argv[1] if len(sys.argv) > 1 else os.path.join(PROJ_ROOT, "대본.txt")
    if os.path.exists(target_file):
        with open(target_file, "r", encoding="utf-8") as f:
            script_text = f.read().strip()
        
        generator = QwenMultiVoiceGenerator()
        generator.run_all(script_text, target_file)
    else:
        print(f"❌ 파일 없음: {target_file}")

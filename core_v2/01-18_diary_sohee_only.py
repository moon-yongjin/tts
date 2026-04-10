import os
import sys
import time
import re
import datetime
import tempfile
import numpy as np
import soundfile as sf
from pydub import AudioSegment
from pydub.effects import speedup
import mlx.core as mx
from mlx_audio.tts import load 

# [1. 환경 및 경로 설정]
sys.stdout.reconfigure(encoding='utf-8')

ENGINE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJ_ROOT = os.path.dirname(ENGINE_DIR)
DOWNLOADS_DIR = os.path.join(os.path.expanduser("~"), "Downloads")


# Qwen-TTS MLX 설정
MODEL_ID = "mlx-community/Qwen3-TTS-12Hz-1.7B-CustomVoice-bf16"
QWEN_VOICE = "sohee"

# Qwen용 파라미터 (다이어리 전용: 나즈막하고 차분한 톤)
QWEN_INSTRUCT = "당신은 70대 할머니 성우입니다. 정 많고 따뜻하면서도, 지난 세월의 고단함과 지혜가 묻어나는 인자한 말투로 천천히 인생 이야기를 들려주듯 낭독하세요."
GEN_KWARGS = {
    "max_tokens": 1024,
    "top_p": 1.0,
    "repetition_penalty": 1.5
}

SPEED_FACTOR = 0.9  # 할머니 톤에 맞춰 약간 천천히
PITCH_SHIFT = -0.15 # 약간 더 깊고 차분한 톤

def format_srt_time(ms):
    s, ms = divmod(ms, 1000)
    m, s = divmod(s, 60)
    h, m = divmod(m, 60)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

class SoheeDiaryGenerator:
    def __init__(self):
        print(f"🚀 Qwen BF16 모델 로딩 중: {MODEL_ID}")
        self.qwen_model = load(MODEL_ID)
        print("✅ Qwen 모델 로딩 완료!")

    def clean_text(self, text):
        text = re.sub(r'\[(BGM|묘사|지문|설명|배경|음악|CHAPTER|챕터|SFX):?.*?\]', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\(.*?\)', '', text)
        return text.strip()

    def parse_segments(self, text):
        # 다이어리 모드: 모든 텍스트를 하나의 세그먼트로 처리
        return [{"type": "narration", "text": text}]

    def split_chunks(self, text, max_chars=60):
        """사용자가 찍은 쉼표/마침표를 절대적으로 존중하여 분할 (병합 로직 제거)"""
        raw_chunks = re.split(r'([.!?,\n]\s*)', text)
        chunks = []
        for i in range(0, len(raw_chunks), 2):
            part = raw_chunks[i]
            punc = raw_chunks[i+1] if i+1 < len(raw_chunks) else ""
            full = (part + punc).strip()
            if not full: continue
            
            if len(full) > max_chars:
                # 60자가 넘는 경우에만 단어 단위로 쪼갬
                words = full.split()
                temp = ""
                for w in words:
                    if len(temp) + len(w) + 1 <= max_chars: temp += w + " "
                    else:
                        if temp: chunks.append(temp.strip())
                        temp = w + " "
                if temp: chunks.append(temp.strip())
            else:
                chunks.append(full)
        return [c for c in chunks if c]


    def generate_qwen(self, text, output_path):
        results = self.qwen_model.generate(
            text=text, voice=QWEN_VOICE, language="Korean",
            instruct=QWEN_INSTRUCT, **GEN_KWARGS
        )
        segment_audio_mx = None
        for res in results:
            if segment_audio_mx is None: segment_audio_mx = res.audio
            else: segment_audio_mx = mx.concatenate([segment_audio_mx, res.audio])
            
        if segment_audio_mx is not None:
            audio_np = np.array(segment_audio_mx)
            sf.write(output_path, audio_np, 24000)
            return True
        return False

    def run(self, script_text, base_filename):
        timestamp = datetime.datetime.now().strftime("%m%d_%H%M")
        output_name = f"{base_filename}_Sohee_{timestamp}.mp3"
        output_path = os.path.join(DOWNLOADS_DIR, output_name)
        
        segments = self.parse_segments(self.clean_text(script_text))
        print(f"📢 다이어리 모드: 소희 단독 음성 생성 시작 (느린 속도 + 낮은 피치)")
        
        combined_audio = AudioSegment.empty()
        all_srt_entries = []
        current_time_ms = 0
        srt_idx = 1
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            for idx, seg in enumerate(segments):
                is_diag = (seg["type"] == "dialogue")
                print(f"   [{idx+1}/{len(segments)}] {seg['type'].upper()}: {seg['text'][:20]}...")
                
                chunks = self.split_chunks(seg["text"])
                for chunk in chunks:
                    tmp_audio = os.path.join(tmp_dir, f"seg_{idx}_{srt_idx}.wav")
                    success = self.generate_qwen(chunk, tmp_audio)
                    
                    if success and os.path.exists(tmp_audio):
                        segment = AudioSegment.from_file(tmp_audio)
                        
                        # 속도 조절 (0.8배로 느리게)
                        if SPEED_FACTOR != 1.0:
                            segment = segment._spawn(segment.raw_data, overrides={
                                "frame_rate": int(segment.frame_rate * SPEED_FACTOR)
                            }).set_frame_rate(segment.frame_rate)
                        
                        # 피치 조절 (낮게)
                        if PITCH_SHIFT != 0:
                            new_sample_rate = int(segment.frame_rate * (2 ** PITCH_SHIFT))
                            segment = segment._spawn(segment.raw_data, overrides={
                                "frame_rate": new_sample_rate
                            }).set_frame_rate(segment.frame_rate)
                        
                        duration_ms = len(segment)
                        start_time = format_srt_time(current_time_ms)
                        end_time = format_srt_time(current_time_ms + duration_ms)
                        all_srt_entries.append(f"{srt_idx}\n{start_time} --> {end_time}\n{chunk}\n\n")
                        
                        combined_audio += segment
                        current_time_ms += duration_ms
                        srt_idx += 1
                        
                        pause_ms = 300
                combined_audio += AudioSegment.silent(duration=pause_ms)
                current_time_ms += pause_ms

        combined_audio.export(output_path, format="mp3", bitrate="192k")
        srt_path = output_path.replace(".mp3", ".srt")
        with open(srt_path, "w", encoding="utf-8-sig") as f:
            f.writelines(all_srt_entries)
            
        print(f"✅ 완료: {output_name}")
        print(f"✅ 자막 생성: {os.path.basename(srt_path)}")

if __name__ == "__main__":
    target_file = sys.argv[1] if len(sys.argv) > 1 else os.path.join(PROJ_ROOT, "대본.txt")
    if os.path.exists(target_file):
        with open(target_file, "r", encoding="utf-8") as f: script_text = f.read().strip()
        generator = SoheeDiaryGenerator()
        generator.run(script_text, os.path.splitext(os.path.basename(target_file))[0])

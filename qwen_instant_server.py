import os
import sys
import torch
import soundfile as sf
# import whisper (Removed for speed)
import time
import json
import re
from qwen_tts import Qwen3TTSModel
from datetime import datetime, UTC
from pydub import AudioSegment

# [경로 설정]
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BRIDGE_DIR = os.path.join(BASE_DIR, "bridge")
DOWNLOADS_DIR = os.path.join(os.path.expanduser("~"), "Downloads")
os.makedirs(BRIDGE_DIR, exist_ok=True)

# [Qwen-TTS 설정]
MODEL_ID = "Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice"
SPEAKER = "sohee"
INSTRUCT = "An extremely breathy and airy voice of a 40-year-old woman. The tone is solemn, tragic, and grave, as if speaking with a heavy heart."

# [Whisper 설정]
STT_MODEL_NAME = "base"

class QwenInstantServer:
    def __init__(self):
        if torch.cuda.is_available():
            self.device = "cuda"
            self.dtype = torch.bfloat16
        elif torch.backends.mps.is_available():
            self.device = "mps"
            self.dtype = torch.float16
        else:
            self.device = "cpu"
            self.dtype = torch.float32
        print(f"📡 모델 로딩 중 ({self.device}, {self.dtype})...")
        
        # 최적화된 로딩 (device_map 사용, dtype 사용)
        self.tts_model = Qwen3TTSModel.from_pretrained(
            MODEL_ID, 
            device_map=self.device,
            dtype=self.dtype
        )
        # self.stt_model = whisper.load_model(STT_MODEL_NAME) (Removed)
        print("✅ Qwen-TTS 로딩 완료! 즉시 생성이 가능합니다.")
        
        self.request_file = os.path.join(BRIDGE_DIR, "qwen_request.json")
        self.result_file = os.path.join(BRIDGE_DIR, "qwen_result.json")
        
        # 이전 찌꺼기 파일 제거
        if os.path.exists(self.request_file): os.remove(self.request_file)
        if os.path.exists(self.result_file): os.remove(self.result_file)

    def clean_text(self, text):
        text = re.sub(r'\[(BGM|묘사|지문|설명|배경|음악|CHAPTER|챕터|SFX):?.*?\]', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\[(대사|지문|묘사|설명)\]', '', text)
        text = re.sub(r'\(.*?\)', '', text)
        return text.strip()

    def format_srt_time(self, seconds):
        td = datetime.fromtimestamp(seconds, UTC)
        return td.strftime('%H:%M:%S,%f')[:-3]

    def split_text(self, text, max_chars=1000):
        sentences = re.split(r'(?<=[.!?])\s+', text)
        chunks = []
        current_chunk = ""
        for sentence in sentences:
            if len(current_chunk) + len(sentence) <= max_chars:
                current_chunk += (" " + sentence if current_chunk else sentence)
            else:
                if current_chunk: chunks.append(current_chunk.strip())
                current_chunk = sentence
        if current_chunk: chunks.append(current_chunk.strip())
        return chunks

    def process_request(self, data):
        text = data.get("text", "")
        output_name = data.get("output_name", f"Qwen_Output_{int(time.time())}.mp3")
        output_path = os.path.join(DOWNLOADS_DIR, output_name)
        
        if not text: return {"status": "error", "message": "Text is empty"}

        print(f"🎙️ [Processing] Text: {text[:50]}...")
        start_time = time.time()
        
        try:
            # 1. TTS 생성 (청크 단위 분할 및 병합)
            chunks = self.split_text(text, max_chars=1000)
            print(f"📦 Chunks: {len(chunks)}")
            
            combined_audio = AudioSegment.empty()
            sentences_for_srt = []
            
            with torch.inference_mode():
                for i, chunk in enumerate(chunks):
                    print(f"⏳ Part {i+1}/{len(chunks)} generating...")
                    # ✅ M4 Pro 전용: MPS 최적화 가속
                    wavs, sr = self.tts_model.generate_custom_voice(
                        text=chunk, speaker=SPEAKER, language="Korean", instruct=INSTRUCT
                    )
                    
                    import io
                    buf = io.BytesIO()
                    sf.write(buf, wavs[0], sr, format='WAV')
                    buf.seek(0)
                    segment = AudioSegment.from_wav(buf)
                    combined_audio += segment
                    
                    chunk_sentences = re.split(r'(?<=[.!?])\s+', self.clean_text(chunk))
                    sentences_for_srt.extend([s.strip() for s in chunk_sentences if s.strip()])
            
            tts_time = time.time() - start_time
            print(f"⚡ AI Generation Time: {tts_time:.1f}s")
            
            total_duration_ms = len(combined_audio)
            total_chars = sum(len(s) for s in sentences_for_srt)
            srt_path = output_path.replace(".mp3", ".srt")
            
            with open(srt_path, "w", encoding="utf-8-sig") as f:
                current_ms = 0
                for i, sent in enumerate(sentences_for_srt):
                    duration_ms = (len(sent) / total_chars) * total_duration_ms
                    start_sec = current_ms / 1000.0
                    end_sec = (current_ms + duration_ms) / 1000.0
                    f.write(f"{i + 1}\n{self.format_srt_time(start_sec)} --> {self.format_srt_time(end_sec)}\n{sent}\n\n")
                    current_ms += duration_ms

            combined_audio.export(output_path, format="mp3", bitrate="192k")
            
            elapsed = time.time() - start_time
            print(f"✅ Finished: {output_name} ({elapsed:.1f}s)")
            return {"status": "success", "audio": output_path, "srt": srt_path, "elapsed": elapsed}

        except Exception as e:
            import traceback
            err_msg = f"In-process Error: {str(e)}\n{traceback.format_exc()}"
            print(f"❌ {err_msg}")
            return {"status": "error", "message": err_msg}

    def run(self):
        print("\n" + "="*50)
        print("🚀 Qwen-TTS Instant Server is Running!")
        print(f"📍 Watching: {self.request_file}")
        print("="*50 + "\n")
        
        while True:
            if os.path.exists(self.request_file):
                result = None
                try:
                    # 파일이 완전히 써질 때까지 아주 잠시 대기
                    time.sleep(0.1)
                    with open(self.request_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    
                    os.remove(self.request_file)
                    result = self.process_request(data)
                        
                except Exception as e:
                    import traceback
                    err_msg = f"Server Loop Error: {str(e)}\n{traceback.format_exc()}"
                    print(f"❌ {err_msg}")
                    result = {"status": "error", "message": err_msg}
                
                if result:
                    with open(self.result_file, "w", encoding="utf-8") as f:
                        json.dump(result, f, ensure_ascii=False, indent=2)
            
            time.sleep(0.2)

if __name__ == "__main__":
    server = QwenInstantServer()
    server.run()

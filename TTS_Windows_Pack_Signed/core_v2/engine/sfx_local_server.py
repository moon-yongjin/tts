import os
import sys
import torch
import json
import time
import re
from audiocraft.models import AudioGen, MusicGen
from audiocraft.data.audio import audio_write
import torchaudio

# [경로 설정]
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BRIDGE_DIR = os.path.join(BASE_DIR, "bridge")
DOWNLOADS_DIR = os.path.join(os.path.expanduser("~"), "Downloads")
os.makedirs(BRIDGE_DIR, exist_ok=True)

class UnifiedAudioServer:
    def __init__(self):
        self.device = "mps" if torch.backends.mps.is_available() else "cpu"
        print(f"📡 통합 오디오 엔진 로딩 중 ({self.device})...")
        
        try:
            # 1. AudioGen (효과음) 로드
            print("🔊 AudioGen (SFX) 모델 로딩 중...")
            self.sfx_model = AudioGen.get_pretrained('facebook/audiogen-medium')
            self.sfx_model.set_generation_params(duration=5)
            
            # 2. MusicGen (BGM) 로드 (메모리 효율을 위해 small 사용)
            print("🎵 MusicGen (BGM) 모델 로딩 중...")
            self.bgm_model = MusicGen.get_pretrained('facebook/musicgen-small')
            self.bgm_model.set_generation_params(duration=15) # 기본 15초 생성
            
            print("✅ 모든 모델 로딩 완료! 효과음 및 BGM 생성이 가능합니다.")
        except Exception as e:
            print(f"❌ 모델 로딩 실패: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
        
        self.request_file = os.path.join(BRIDGE_DIR, "audio_request.json")
        self.result_file = os.path.join(BRIDGE_DIR, "audio_result.json")
        # 구버전 호환용 (sfx 전용)
        self.sfx_request_file = os.path.join(BRIDGE_DIR, "sfx_request.json")
        self.sfx_result_file = os.path.join(BRIDGE_DIR, "sfx_result.json")

    def process_request(self, data, is_legacy_sfx=False):
        req_type = data.get("type", "sfx") # "sfx" 또는 "music"
        prompt = data.get("prompt", data.get("text", ""))
        output_name = data.get("output_name", f"{req_type.upper()}_{int(time.time())}")
        duration = data.get("duration", 5 if req_type == "sfx" else 15)
        
        base_name = output_name.replace(".mp3", "")
        output_path = os.path.join(DOWNLOADS_DIR, f"{base_name}")
        
        if not prompt: return {"status": "error", "message": "Prompt is empty"}

        print(f"🚀 [Processing {req_type.upper()}] Prompt: {prompt} (Duration: {duration}s)")
        start_time = time.time()
        
        try:
            with torch.inference_mode():
                descriptions = [prompt]
                if req_type == "music":
                    self.bgm_model.set_generation_params(duration=duration)
                    wav = self.bgm_model.generate(descriptions)
                    sample_rate = self.bgm_model.sample_rate
                else:
                    self.sfx_model.set_generation_params(duration=duration)
                    wav = self.sfx_model.generate(descriptions)
                    sample_rate = self.sfx_model.sample_rate
                
                # 결과 저장
                audio_write(output_path, wav[0].cpu(), sample_rate, strategy="loudness", loudness_compressor=True)
                
            final_file = f"{output_path}.wav"
            
            # MP3로 변환
            from pydub import AudioSegment
            audio = AudioSegment.from_wav(final_file)
            mp3_final = f"{output_path}.mp3"
            audio.export(mp3_final, format="mp3", bitrate="192k")
            
            if os.path.exists(final_file): os.remove(final_file)

            elapsed = time.time() - start_time
            print(f"✅ Finished: {os.path.basename(mp3_final)} ({elapsed:.1f}s)")
            return {"status": "success", "audio": mp3_final, "elapsed": elapsed, "type": req_type}

        except Exception as e:
            import traceback
            err_msg = f"Audio Generation Error: {str(e)}\n{traceback.format_exc()}"
            print(f"❌ {err_msg}")
            return {"status": "error", "message": err_msg}

    def run(self):
        print("\n" + "="*50)
        print("🚀 Unified Local Audio (SFX + Music) Server is Running!")
        print(f"📍 Watching: {self.request_file}")
        print("="*50 + "\n")
        
        # 이전 찌꺼기 제거
        for f in [self.request_file, self.sfx_request_file]:
            if os.path.exists(f): os.remove(f)
        
        while True:
            # 1. 통합 요청 확인
            if os.path.exists(self.request_file):
                result = None
                try:
                    time.sleep(0.1)
                    with open(self.request_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    os.remove(self.request_file)
                    result = self.process_request(data)
                except Exception as e:
                    print(f"❌ Server Error: {e}")
                    result = {"status": "error", "message": str(e)}
                
                if result:
                    with open(self.result_file, "w", encoding="utf-8") as f:
                        json.dump(result, f, ensure_ascii=False, indent=2)

            # 2. 레거시 SFX 요청 확인 (호환성)
            if os.path.exists(self.sfx_request_file):
                result = None
                try:
                    time.sleep(0.1)
                    with open(self.sfx_request_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    os.remove(self.sfx_request_file)
                    data["type"] = "sfx" # 강제로 sfx 타입 지정
                    result = self.process_request(data, is_legacy_sfx=True)
                except Exception as e:
                    print(f"❌ Legacy Server Error: {e}")
                    result = {"status": "error", "message": str(e)}
                
                if result:
                    with open(self.sfx_result_file, "w", encoding="utf-8") as f:
                        json.dump(result, f, ensure_ascii=False, indent=2)
            
            time.sleep(0.5)

if __name__ == "__main__":
    server = UnifiedAudioServer()
    server.run()

import os
import sys
import time
import re
import datetime
import subprocess
from pydub import AudioSegment

# [1. 환경 및 경로 설정]
sys.stdout.reconfigure(encoding='utf-8')

ENGINE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJ_ROOT = os.path.dirname(ENGINE_DIR)
DOWNLOADS_DIR = os.path.join(os.path.expanduser("~"), "Downloads")
FISH_DIR = os.path.join(PROJ_ROOT, "fish-speech-s1")
PYTHON_EXE = os.path.join(FISH_DIR, "venv", "bin", "python")

# [Fish-Speech 설정]
REPO_DIR = os.path.join(FISH_DIR, "repo")
CHECKPOINT_DIR = os.path.join(REPO_DIR, "checkpoints", "fish-speech-1.5")
SPEED_FACTOR = 1.1

class FishSpeechGenerator:
    def __init__(self):
        print(f"📡 Fish-Speech S1 엔진 준비 완료")
        self.temp_dir = os.path.join(FISH_DIR, "temp_work")
        os.makedirs(self.temp_dir, exist_ok=True)

    def clean_text(self, text):
        text = re.sub(r'\[(BGM|묘사|지문|설명|배경|음악|CHAPTER|챕터|SFX):?.*?\]', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\(.*?\)', '', text)
        return text.strip()

    def split_chunks(self, text):
        chunks = re.split(r'(?<=[.,!?])\s*', text)
        return [c.strip() for c in chunks if c.strip()]

    def format_srt_time(self, seconds):
        td = datetime.datetime.fromtimestamp(seconds, datetime.UTC)
        return td.strftime('%H:%M:%S,%f')[:-3]

    def generate_chunk_audio(self, text, output_wav):
        """Fish-Speech S1 2단계 생성: Text -> Semantic -> Audio"""
        semantic_dir = os.path.join(self.temp_dir, "semantic")
        os.makedirs(semantic_dir, exist_ok=True)
        # 1단계: Text to Semantic (.npy)
        cmd_llama = [
            PYTHON_EXE, "-m", "fish_speech.models.text2semantic.inference",
            "--text", text,
            "--checkpoint-path", CHECKPOINT_DIR,
            "--output-dir", semantic_dir,
            "--device", "mps",
            "--no-compile"
        ]
        
        # 2단계: Semantic to Audio (.wav) - VQGAN Firefly
        cmd_vqgan = [
            PYTHON_EXE, "-m", "fish_speech.models.vqgan.inference",
            "--input-path", semantic_dir,
            "--output-path", output_wav,
            "--config-name", "s1_mini_firefly",
            "--checkpoint-path", os.path.join(CHECKPOINT_DIR, "firefly-gan-vq-fsq-8x1024-21hz-generator.pth"),
            "--device", "mps"
        ]
        
        try:
            # 기존 임시 파일들 정리
            for f in os.listdir(semantic_dir):
                if f.endswith(".npy"): os.remove(os.path.join(semantic_dir, f))
                
            # 실행
            start_time = time.time()
            result = subprocess.run(cmd_llama, cwd=REPO_DIR, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"❌ Text2Semantic 에러:\n{result.stderr}")
                return False
            
            # 생성된 .npy 파일 찾기 (보통 codes_0.npy 형식)
            npy_files = [f for f in os.listdir(semantic_dir) if f.endswith(".npy")]
            if not npy_files: 
                print("❌ Semantic 파일을 찾을 수 없습니다.")
                return False
            
            # 첫 번째 npy 파일 사용
            npy_path = os.path.join(semantic_dir, npy_files[0])
            cmd_vqgan[cmd_vqgan.index("--input-path") + 1] = npy_path
            
            subprocess.run(cmd_vqgan, check=True, capture_output=True, cwd=REPO_DIR)
            
            # RTF 계산 (약식: 청크 단위)
            if os.path.exists(output_wav):
                seg = AudioSegment.from_wav(output_wav)
                audio_dur = len(seg) / 1000.0
                gen_time = time.time() - start_time
                rtf = gen_time / audio_dur if audio_dur > 0 else 0
                print(f"   ⏱️ RTF: {rtf:.3f} (Gen: {gen_time:.2f}s, Audio: {audio_dur:.2f}s)")
                return True
            return False
        except subprocess.CalledProcessError as e:
            print(f"❌ Fish-Speech S1 에러: {e.stderr.decode()}")
            return False

    def run(self, script_text, output_path):
        chunks = self.split_chunks(self.clean_text(script_text))
        print(f"📦 Total Fish-Speech S1 Chunks: {len(chunks)}")
        
        combined_audio = AudioSegment.empty()
        srt_entries = []
        current_time_ms = 0
        
        start_time = time.time()
        
        for i, chunk in enumerate(chunks):
            print(f"🐟 [S1 {i+1}/{len(chunks)}] Generating: {chunk[:30]}...")
            
            temp_wav = os.path.join(self.temp_dir, f"chunk_{i}.wav")
            success = self.generate_chunk_audio(chunk, temp_wav)
            
            if success and os.path.exists(temp_wav):
                segment = AudioSegment.from_wav(temp_wav)
                
                # 속도 조절
                if SPEED_FACTOR != 1.0:
                    segment = segment.speedup(playback_speed=SPEED_FACTOR, chunk_size=150, crossfade=25)
                
                duration_ms = len(segment)
                combined_audio += segment
                
                # SRT
                start_sec = current_time_ms / 1000.0
                end_sec = (current_time_ms + duration_ms) / 1000.0
                srt_entries.append(f"{i + 1}\n{self.format_srt_time(start_sec)} --> {self.format_srt_time(end_sec)}\n{chunk}\n\n")
                
                current_time_ms += duration_ms
                
                # 휴식 추가
                if i < len(chunks) - 1:
                    pause_ms = 500 if any(chunk.endswith(p) for p in ['.', '?', '!']) else 200
                    combined_audio += AudioSegment.silent(duration=pause_ms)
                    current_time_ms += pause_ms
                
                os.unlink(temp_wav)
            else:
                print(f"⚠️ {i+1}번째 청크 생성 실패, 건너뜁니다.")

        # 저장
        combined_audio.export(output_path, format="mp3", bitrate="192k")
        srt_path = output_path.replace(".mp3", ".srt")
        with open(srt_path, "w", encoding="utf-8-sig") as f:
            f.writelines(srt_entries)
            
        elapsed = time.time() - start_time
        print(f"✅ Fish-Speech S1 완료: {os.path.basename(output_path)} ({elapsed:.1f}s)")

if __name__ == "__main__":
    target_file = sys.argv[1] if len(sys.argv) > 1 else os.path.join(PROJ_ROOT, "대본.txt")
    if os.path.exists(target_file):
        with open(target_file, "r", encoding="utf-8") as f:
            script_text = f.read().strip()
        if script_text:
            timestamp = datetime.datetime.now().strftime("%m%d_%H%M")
            base_filename = os.path.splitext(os.path.basename(target_file))[0]
            output_name = f"{base_filename}_Fish_1.5_{timestamp}.mp3"
            output_path = os.path.join(DOWNLOADS_DIR, output_name)
            
            generator = FishSpeechGenerator()
            generator.run(script_text, output_path)
        else: print("❌ 빈 대본")
    else: print("❌ 파일 없음")

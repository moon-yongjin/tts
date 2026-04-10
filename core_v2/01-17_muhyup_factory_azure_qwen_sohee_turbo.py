import os
import sys
import time
import re
import datetime
import tempfile
import numpy as np
import soundfile as sf
from pydub import AudioSegment
import azure.cognitiveservices.speech as speechsdk
import mlx.core as mx
from mlx_audio.tts import load 

# [1. 환경 및 경로 설정]
sys.stdout.reconfigure(encoding='utf-8')

ENGINE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJ_ROOT = os.path.dirname(ENGINE_DIR)
DOWNLOADS_DIR = os.path.join(os.path.expanduser("~"), "Downloads")

# Azure Speech 설정
SPEECH_KEY = "21HfTF65JeOoI5mqoW5NfPYZcmG114R7AFzrjbk5HLRE4fqIua7NJQQJ99CAACNns7RXJ3w3AAAYACOGMfRn"
SPEECH_REGION = "koreacentral"
AZURE_VOICE = "ko-KR-JiMinNeural" 

# Qwen-TTS MLX 설정
MODEL_ID = "mlx-community/Qwen3-TTS-12Hz-1.7B-CustomVoice-bf16"
QWEN_VOICE = "sohee"

# Qwen용 파라미터
QWEN_INSTRUCT = "당신은 서울 표준어를 사용하는 성우입니다. 정확하고 단호한 한국어 어조로 낭독하세요."
GEN_KWARGS = {
    "temperature": 0.0,
    "top_p": 1.0,
    "repetition_penalty": 1.5
}

AZURE_SPEED = 1.1
QWEN_SPEED = 1.0

def format_srt_time(ms):
    s, ms = divmod(ms, 1000)
    m, s = divmod(s, 60)
    h, m = divmod(m, 60)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

class QwenAzureTurboGenerator:
    def __init__(self):
        print(f"🚀 [TURBO] Qwen BF16 모델 로딩 중: {MODEL_ID}")
        self.qwen_model = load(MODEL_ID)
        print("✅ Qwen 모델 로딩 완료!")
        
        # Azure 설정
        self.speech_config = speechsdk.SpeechConfig(subscription=SPEECH_KEY, region=SPEECH_REGION)
        self.speech_config.set_speech_synthesis_output_format(speechsdk.SpeechSynthesisOutputFormat.Audio48Khz192KBitRateMonoMp3)

    def clean_text(self, text):
        text = re.sub(r'\[(BGM|묘사|지문|설명|배경|음악|CHAPTER|챕터|SFX):?.*?\]', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\(.*?\)', '', text)
        return text.strip()

    def parse_segments(self, text):
        parts = re.split(r'(")', text)
        segments = []
        is_inside_quote = False
        
        for part in parts:
            if part == '"':
                is_inside_quote = not is_inside_quote
                continue
            
            p_text = part.strip()
            if not p_text: continue
            
            seg_type = "dialogue" if is_inside_quote else "narration"
            
            if segments and segments[-1]["type"] == seg_type:
                segments[-1]["text"] += " " + p_text
            else:
                segments.append({"type": seg_type, "text": p_text})
                
        return segments

    def split_chunks(self, text, max_chars=60):
        raw_chunks = re.split(r'([.!?,\n]\s*)', text)
        chunks = []
        for i in range(0, len(raw_chunks), 2):
            part = raw_chunks[i]
            punc = raw_chunks[i+1] if i+1 < len(raw_chunks) else ""
            full = (part + punc).strip()
            if not full: continue
            
            # 글자가 없고 문장 부호만 있는 경우 스킵 (Azure 에러 방지)
            if not re.search(r'[가-힣a-zA-Z0-9]', full):
                continue

            if len(full) > max_chars:
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


    def generate_azure(self, text, output_path):
        ssml_text = f'''
        <speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="ko-KR">
            <voice name="{AZURE_VOICE}">
                <prosody rate="{(AZURE_SPEED-1)*100:+.2f}%">{text}</prosody>
            </voice>
        </speak>
        '''
        audio_config = speechsdk.audio.AudioOutputConfig(filename=output_path)
        synthesizer = speechsdk.SpeechSynthesizer(speech_config=self.speech_config, audio_config=audio_config)
        result = synthesizer.speak_ssml_async(ssml_text).get()
        
        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            return True
        else:
            print(f"   ❌ Azure 오류: {result.reason}")
            if result.reason == speechsdk.ResultReason.Canceled:
                cancellation_details = result.cancellation_details
                print(f"      사유: {cancellation_details.reason}")
                if cancellation_details.reason == speechsdk.CancellationReason.Error:
                    print(f"      에러 코드: {cancellation_details.error_code}")
                    print(f"      에러 상세: {cancellation_details.error_details}")
            return False

    def run(self, script_text, base_filename):
        timestamp = datetime.datetime.now().strftime("%m%d_%H%M")
        output_name = f"{base_filename}_Turbo_Hybrid_{timestamp}.mp3"
        output_path = os.path.join(DOWNLOADS_DIR, output_name)
        
        segments = self.parse_segments(self.clean_text(script_text))
        print(f"\n🚀 [TURBO BATCH] 하이브리드 생성 시작 (Azure + Qwen {QWEN_VOICE} Batch)")
        
        # 1. 전처리 및 대사 청크 수집
        all_qwen_chunks = []
        processed_segments = []
        
        for idx, seg in enumerate(segments):
            chunks = self.split_chunks(seg["text"])
            seg_info = {"type": seg["type"], "chunks": []}
            for chunk in chunks:
                if seg["type"] == "dialogue":
                    chunk_idx = len(all_qwen_chunks)
                    all_qwen_chunks.append(chunk)
                    seg_info["chunks"].append({"text": chunk, "qwen_idx": chunk_idx})
                else:
                    seg_info["chunks"].append({"text": chunk})
            processed_segments.append(seg_info)

        # 2. Qwen 대사 일괄 생성 (Batch Processing)
        qwen_wav_map = {}
        if all_qwen_chunks:
            print(f"📦 {len(all_qwen_chunks)}개 대사 청크 일괄 생성 중 (Batch Processing)...")
            results = self.qwen_model.generate(
                text=all_qwen_chunks, 
                voice=QWEN_VOICE, 
                language="Korean",
                instruct=QWEN_INSTRUCT, 
                **GEN_KWARGS
            )
            # MLX generator결과를 리스트로 수집
            for i, res in enumerate(results):
                qwen_wav_map[i] = res.audio

        # 3. Azure 생성 및 병합
        combined_audio = AudioSegment.empty()
        all_srt_entries = []
        current_time_ms = 0
        srt_idx = 1
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            for idx, seg in enumerate(processed_segments):
                is_diag = (seg["type"] == "dialogue")
                print(f"   [{idx+1}/{len(processed_segments)}] {seg['type'].upper()} 처리 중...")
                
                for chunk_info in seg["chunks"]:
                    chunk_text = chunk_info["text"]
                    tmp_audio = os.path.join(tmp_dir, f"seg_{idx}_{srt_idx}.mp3")
                    
                    try:
                        if is_diag:
                            # 이미 일괄 생성된 오디오 사용
                            wav_mx = qwen_wav_map.get(chunk_info["qwen_idx"])
                            if wav_mx is not None:
                                audio_np = np.array(wav_mx)
                                wav_tmp = tmp_audio.replace(".mp3", ".wav")
                                sf.write(wav_tmp, audio_np, 24000)
                                segment = AudioSegment.from_wav(wav_tmp)
                                if QWEN_SPEED != 1.0:
                                    segment = segment.speedup(playback_speed=QWEN_SPEED, chunk_size=150, crossfade=25)
                                os.unlink(wav_tmp)
                            else:
                                continue
                        else:
                            # Azure는 개별 API 호출 (이미 빠름)
                            if self.generate_azure(chunk_text, tmp_audio):
                                if os.path.exists(tmp_audio) and os.path.getsize(tmp_audio) > 0:
                                    segment = AudioSegment.from_file(tmp_audio)
                                else:
                                    print(f"   ⚠️ Azure 생성 파일이 비어있습니다: {chunk_text[:20]}...")
                                    continue
                            else:
                                continue
                    except Exception as e:
                        print(f"   ❌ 오디오 처리 오류 (스킵): {e}")
                        continue
                    
                    duration_ms = len(segment)
                    start_time = format_srt_time(current_time_ms)
                    end_time = format_srt_time(current_time_ms + duration_ms)
                    all_srt_entries.append(f"{srt_idx}\n{start_time} --> {end_time}\n{chunk_text}\n\n")
                    
                    combined_audio += segment
                    current_time_ms += duration_ms
                    srt_idx += 1
                
                pause_ms = 800 if is_diag else 600
                combined_audio += AudioSegment.silent(duration=pause_ms)
                current_time_ms += pause_ms

        # 4. 저장
        combined_audio.export(output_path, format="mp3", bitrate="192k")
        srt_path = output_path.replace(".mp3", ".srt")
        with open(srt_path, "w", encoding="utf-8-sig") as f:
            f.writelines(all_srt_entries)
            
        print(f"✅ [TURBO] 모든 작업 완료: {output_name}")
        print(f"✅ 자막 생성 완료: {os.path.basename(srt_path)}")

if __name__ == "__main__":
    target_file = sys.argv[1] if len(sys.argv) > 1 else os.path.join(PROJ_ROOT, "대본.txt")
    if os.path.exists(target_file):
        with open(target_file, "r", encoding="utf-8") as f: script_text = f.read().strip()
        generator = QwenAzureTurboGenerator()
        generator.run(script_text, os.path.splitext(os.path.basename(target_file))[0])
    else:
        print(f"❌ 파일 없음: {target_file}")

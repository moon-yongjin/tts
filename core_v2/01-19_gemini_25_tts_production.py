import os
import json
import io
import re
from google import genai
from google.genai import types
from pydub import AudioSegment

# 1. Config 및 경로 설정
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(BASE_DIR)
CONFIG_PATH = os.path.join(ROOT_DIR, "config.json")
DOWNLOADS_DIR = os.path.join(os.path.expanduser("~"), "Downloads")

with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    config = json.load(f)
    API_KEY = config.get("Gemini_API_KEY")

client = genai.Client(api_key=API_KEY, http_options={'api_version': 'v1alpha'})

# [설정] 제미나이 프리뷰 TTS 파라미터
MODEL_ID = "gemini-2.5-flash-preview-tts"
# 할머니 페르소나 적용
QWEN_INSTRUCT = "당신은 70대 할머니 성우입니다. 맑고 인자한 목소리로, 지난 세월의 지혜가 묻어나는 따뜻한 말투로 천천히 낭독하세요. 특히 문장마다 목소리 톤이 바뀌지 않도록 처음부터 끝까지 일관된 톤과 감정을 유지하는 것이 가장 중요합니다."

def clean_text(text):
    text = re.sub(r'\[(BGM|묘사|지문|설명|배경|음악|CHAPTER|챕터|SFX|효과음):?.*?\]', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\(.*?\)', '', text)
    return text.strip()

def split_chunks(text, max_len=200):
    """긴 대본을 더 잘게 쪼개기 (톤 튐 및 쇳소리 방지)"""
    # 마침표, 물음표, 느낌표 뒤에서 쪼개되, 콤마에서도 추가로 쪼개기 시도
    sentences = re.split(r'(?<=[.!?])\s+', text)
    chunks = []
    current_chunk = ""
    for s in sentences:
        if len(current_chunk) + len(s) < max_len:
            current_chunk += " " + s
        else:
            chunks.append(current_chunk.strip())
            current_chunk = s
    if current_chunk:
        chunks.append(current_chunk.strip())
    return chunks

def run_production():
    script_path = os.path.join(ROOT_DIR, "대본.txt")
    if not os.path.exists(script_path):
        print("❌ 대본.txt를 찾을 수 없습니다.")
        return

    with open(script_path, "r", encoding="utf-8") as f:
        full_text = f.read()

    cleaned_text = clean_text(full_text)
    chunks = split_chunks(cleaned_text)
    
    print(f"🚀 [Gemini 2.5 TTS Production] 총 {len(chunks)}개 청크 생성 시작")
    combined_audio = AudioSegment.empty()

    for i, chunk in enumerate(chunks):
        print(f"   🎙️ 진행 중: [{i+1}/{len(chunks)}] ({len(chunk)}자)")
        try:
            # 페르소나 지시문을 포함하여 요청
            prompt = f"{QWEN_INSTRUCT}\n\n[본문]\n{chunk}"
            
            response = client.models.generate_content(
                model=MODEL_ID,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_modalities=["AUDIO"]
                )
            )
            
            chunk_audio_data = bytearray()
            for part in response.candidates[0].content.parts:
                if part.inline_data:
                    chunk_audio_data.extend(part.inline_data.data)
            
            if chunk_audio_data:
                # Raw PCM (24kHz Mono 16bit) -> AudioSegment
                segment = AudioSegment.from_raw(
                    io.BytesIO(chunk_audio_data), 
                    sample_width=2, 
                    frame_rate=24000, 
                    channels=1
                )
                combined_audio += segment
            else:
                print(f"   ⚠️ 청크 {i+1}에서 오디오 데이터를 받지 못했습니다.")
        except Exception as e:
            print(f"   ❌ 청크 {i+1} 생성 실패: {e}")

    if len(combined_audio) > 0:
        # [추가] 후보정: 볼륨 평준화 및 노멀라이즈
        print("🔧 오디오 후보정 중 (Normalization)...")
        combined_audio = combined_audio.normalize(headroom=1.0)
        
        output_name = f"박순자할머니_제미나이25_고품질_{os.getpid() % 1000}.mp3"
        output_path = os.path.join(DOWNLOADS_DIR, output_name)
        combined_audio.export(output_path, format="mp3", bitrate="192k")
        print(f"\n✨ 생성 완료: {output_path}")
        print(f"⏱️ 총 길이: {len(combined_audio)/1000:.2f}초")
    else:
        print("\n❌ 최종 음성 생성에 실패했습니다.")

if __name__ == "__main__":
    run_production()

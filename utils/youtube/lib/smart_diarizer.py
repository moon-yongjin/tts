import os
import json
import subprocess
from pathlib import Path
from google import genai
from google.genai import types

def transcribe_with_whisper(audio_path):
    """mlx_whisper를 이용해 받아쓰기 수행 및 세그먼트 반환"""
    print("✍️ 위스퍼 받아쓰기 중 (mlx_whisper)...")
    try:
        import mlx_whisper
        result = mlx_whisper.transcribe(
            str(audio_path), 
            path_or_hf_repo="mlx-community/whisper-large-v3-turbo"
        )
        return result.get("segments", [])
    except Exception as e:
        print(f"❌ 위스퍼 실행 실패: {e}")
        return []

def diarize_with_gemini(api_key, segments):
    """Gemini를 이용해 문맥 기반 화자 구분 (Diarization)"""
    if not api_key:
        print("⚠️ Gemini Key가 없어 화자 구분을 생략합니다.")
        return segments
        
    client = genai.Client(api_key=api_key)
    
    # 50개 단위로 묶어서 처리
    chunk_size = 50
    diarized_results = []
    
    print(f"🧠 총 {len(segments)}개의 문장을 지능형 화자 분석 중...")
    
    for i in range(0, len(segments), chunk_size):
        chunk = segments[i:i + chunk_size]
        chunk_text = "\n".join([f"{s['id']}|{s['start']:.2f}|{s['text']}" for s in chunk])
        
        prompt = f"""
다음은 유튜브 토크쇼 자막입니다. 
각 문장의 앞뒤 문맥을 파악하여 누가 말했는지 화자(김창옥, 사연자, 관객 등)를 분류해 주세요.
사연의 주인공은 반드시 '사연자'로 표시하세요.

자막:
{chunk_text}

---
**출력 형식 (JSON 배열):**
[
  {{"id": "0", "speaker": "김창옥", "text": "..."}},
  ...
]
"""
        try:
            print(f"   [{i//chunk_size + 1}/{(len(segments)-1)//chunk_size + 1}] 청크 분석 중...")
            response = client.models.generate_content(
                model='gemini-2.0-flash',
                contents=prompt,
                config=types.GenerateContentConfig(response_mime_type="application/json")
            )
            raw_data = json.loads(response.text.strip())
            
            for j, item in enumerate(raw_data):
                if j < len(chunk):
                    full_item = chunk[j].copy()
                    full_item["speaker"] = item.get("speaker", "알수없음")
                    diarized_results.append(full_item)
                    
        except Exception as e:
            print(f"❌ Gemini 분석 오류: {e}")
            for s in chunk:
                s["speaker"] = "Error"
                diarized_results.append(s)

    return diarized_results

import os
import json
import subprocess
from pathlib import Path
from google import genai
from google.genai import types
from pydub import AudioSegment

class SadRemixEngine:
    def __init__(self, api_key):
        self.client = genai.Client(api_key=api_key)

    def select_core_drama_segments(self, segments, target_duration=60):
        """AI로 '슬픈 본론' 구간만 0.1초 단위 정밀 선별"""
        print("🧠 AI가 감정의 정점을 분석하여 '본론' 위주로 짜집기 계획을 세우는 중...")
        
        # 대본 데이터 요약 (토큰 절약 및 문맥 집중)
        transcript_data = "\n".join([
            f"[{s['start']:.2f}s - {s['end']:.2f}s] {s.get('speaker', '?')}: {s['text']}" 
            for s in segments
        ])
        
        prompt = f"""
다음은 유튜브 사연 영상의 화자 분리 대본입니다. 
시청자에게 깊은 울림을 주기 위해 **"서론(배경 설명, 인사)은 과감히 버리고, 주인공의 가장 고통스럽고 시각적으로 그려지는 고백(본론)"**만 60초 내외로 짜집기해 주세요.

**편집 원칙 (V5+ Visual & Sad Logic):**
1. **No Intro / No Reporter**: 다른 화자나 기자의 설명으로 시작하지 마세요. 바로 주인공의 목소리로 본론부터 시작하세요.
2. **Visual Hardship First**: 단순히 "슬프다", "힘들었다"는 감정 표현보다, **"학교 진학 상담을 직접 다녔다", "동생을 업고 뛰었다", "돈 벌기 위해 이런 일을 했다"** 처럼 영상으로 장면을 그려낼 수 있는 구체적인 고생 담을 최우선으로 선별하세요. 이것이 영상 제작의 핵심입니다.
3. **Protagonist Centric**: 사연의 주인공 목소리만 나오게 하세요. 
4. **Natural Transition**: 주제별로 가장 임팩트 있는 고백들을 연결하세요.

대본:
{transcript_data}

---
**출력 형식 (JSON 배열):**
반드시 다음 형식의 JSON 배열로만 응답하세요. 총 합계 길이는 55~65초 사이여야 합니다.
[
  {{"start": 시작초, "end": 종료초, "text": "선택한 대사"}}
]
"""
        try:
            response = self.client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt,
                config=types.GenerateContentConfig(response_mime_type="application/json")
            )
            return json.loads(response.text.strip())
        except Exception as e:
            print(f"❌ AI 분석 실패: {e}")
            return None

    def merge_audio_segments(self, video_source, edit_list, output_path):
        """선별된 구간들을 고품질 오디오로 병합"""
        print(f"✂️ 추출된 {len(edit_list)}개 감정 조각을 병합 중...")
        
        # 고품질 원본 오디오 추출
        temp_wav = output_path.parent / "temp_hq_extract.wav"
        subprocess.run([
            "ffmpeg", "-y", "-i", str(video_source),
            "-vn", "-acodec", "pcm_s16le", "-ar", "44100", "-ac", "2",
            str(temp_wav)
        ], capture_output=True)
        
        full_audio = AudioSegment.from_wav(str(temp_wav))
        combined = AudioSegment.empty()
        
        for i, item in enumerate(edit_list):
            start_ms = int(item["start"] * 1000)
            end_ms = int(item["end"] * 1000)
            chunk = full_audio[start_ms:end_ms]
            
            # 조각 간 부드러운 연결 (크로스페이드 100ms)
            if len(combined) > 0:
                combined = combined.append(chunk, crossfade=100)
            else:
                combined = chunk
            
            # 문장 간 아주 짧은 정적 (0.3초) 추가하여 여운 제공
            combined += AudioSegment.silent(duration=300)
            
        combined.export(str(output_path), format="wav")
        if temp_wav.exists(): os.remove(temp_wav)
        return True

def run_auto_remix(api_key, diarized_json, video_source, output_dir):
    """엔진 통합 실행 함수"""
    with open(diarized_json, "r", encoding="utf-8") as f:
        segments = json.load(f)
        
    engine = SadRemixEngine(api_key)
    edit_list = engine.select_core_drama_segments(segments)
    
    if not edit_list:
        return None
        
    # 결과 저장용 폴더 및 파일명
    output_dir.mkdir(parents=True, exist_ok=True)
    remix_wav = output_dir / "04_Auto_Sad_Remix_V5.wav"
    remix_txt = output_dir / "04_Auto_Sad_Remix_V5_Transcript.txt"
    
    if engine.merge_audio_segments(video_source, edit_list, remix_wav):
        with open(remix_txt, "w", encoding="utf-8") as f:
            f.write("=== [V5 AI Editor] 자동화된 '슬픈 본론' 리믹스 대본 ===\n\n")
            total_dur = 0
            for item in edit_list:
                f.write(f"[{item['start']:.2f}s] {item['text']}\n")
                total_dur += (item['end'] - item['start'])
            f.write(f"\n총 길이: {total_dur:.2f}초")
            
        return remix_wav, remix_txt
    return None

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
청크 기반 긴 음성 생성 테스트
20초 분량을 짧은 청크로 나눠서 생성 후 합치기
"""

from gradio_client import Client, handle_file
from huggingface_hub import login
import os
import re
import shutil
from pydub import AudioSegment

# HF 토큰으로 로그인
HF_TOKEN = "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"
login(token=HF_TOKEN)

# Space ID
SPACE_ID = "moonyj8080/Qwen3-TTS10"

# 샘플 목소리 및 정확한 대본 (이게 일치해야 품질이 올라갑니다)
VOICE_SAMPLE = "/Users/a12/projects/tts/voices/golden_voice_8.wav"
VOICE_REF_TEXT = "남자는 바닥에 엎드러지며 당황한 기색으로 입을 엽니다."

# 지시문 (KBS 앵커 페르소나 적용)
INSTRUCT = """당신은 서울 표준어를 사용하는 20년 경력의 한국인 성우입니다. 
중국어나 영어 억양을 절대 섞지 말고, KBS 뉴스 앵커처럼 정확하고 단호한 한국어 어조로만 낭독하세요. 
40대 중저음으로 비장하면서도 차분하게 읽으세요. 어떤 외국어도 섞지 마세요."""

# 20초 분량의 텍스트
LONG_TEXT = """
안녕하세요 여러분, 오늘은 인공지능 음성 합성 기술의 놀라운 발전에 대해 이야기해보겠습니다.
최근 몇 년 사이에 딥러닝 기술이 급속도로 발전하면서, 음성 복제 기술도 함께 진화했습니다.
이제는 단 몇 초의 샘플 음성만으로도 매우 자연스럽고 감정이 담긴 음성을 생성할 수 있게 되었습니다.

특히 트랜스포머 아키텍처와 대규모 언어 모델의 등장으로, 텍스트를 음성으로 변환하는 과정이 더욱 정교해졌습니다.
이러한 기술은 콘텐츠 제작, 오디오북 제작, 교육 자료 개발 등 다양한 분야에서 활용되고 있습니다.
또한 시각 장애인을 위한 접근성 향상에도 큰 도움을 주고 있습니다.

하지만 가장 중요한 것은 생성된 음성이 긴 문장과 다양한 맥락에서도 일관된 음색과 특성을 유지하는지 확인하는 것입니다.
이것이 바로 우리가 오늘 테스트하려는 핵심 내용입니다. 감사합니다.
""".strip()

# 청크 크기 (더 잘게 쪼개기)
CHUNK_SIZE = 50 

def split_text_into_chunks(text, chunk_size):
    """텍스트를 아주 잘게 청크로 분할"""
    # 마침표, 물음표, 느낌표 기준으로 분할
    sentences = re.split(r'(?<=[.!?])\s+', text.replace('\n', ' '))
    
    chunks = []
    current_chunk = ""
    
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
            
        # 문장 자체가 청크 사이즈보다 크면 글자수로 자름
        if len(sentence) > chunk_size:
            if current_chunk:
                chunks.append(current_chunk)
                current_chunk = ""
            
            # 문장을 chunk_size 단위로 쪼갬
            for i in range(0, len(sentence), chunk_size):
                chunks.append(sentence[i:i+chunk_size])
        else:
            if len(current_chunk) + len(sentence) + 1 <= chunk_size:
                current_chunk += " " + sentence if current_chunk else sentence
            else:
                chunks.append(current_chunk)
                current_chunk = sentence
    
    if current_chunk:
        chunks.append(current_chunk)
    
    return [c.strip() for c in chunks if c.strip()]

def generate_chunked_audio():
    """청크별로 음성 생성 후 합치기 (최적화 버전)"""
    
    import re
    print(f"{'='*80}")
    print(f"🎤 [개선 버전] 청크 기반 긴 음성 생성 테스트")
    print(f"👉 참조 텍스트 교정: \"{VOICE_REF_TEXT}\"")
    print(f"{'='*80}\n")
    
    chunks = split_text_into_chunks(LONG_TEXT, CHUNK_SIZE)
    print(f"✂️  청크 개수: {len(chunks)}개 (사이즈: {CHUNK_SIZE})\n")
    
    try:
        client = Client(SPACE_ID)
        print("✅ Space 연결 성공!\n")
    except Exception as e:
        print(f"❌ Space 연결 실패: {e}")
        return
    
    temp_dir = "/Users/a12/projects/tts/temp_chunks_v2"
    os.makedirs(temp_dir, exist_ok=True)
    
    audio_files = []
    
    for i, chunk in enumerate(chunks, 1):
        print(f"🎵 청크 {i}/{len(chunks)} 생성 중... ({len(chunk)}자)")
        
        try:
            result = client.predict(
                ref_audio=handle_file(VOICE_SAMPLE),
                ref_text=VOICE_REF_TEXT,  # 실제 샘플 대본으로 교체
                target_text=chunk,
                language="Korean",
                use_xvector_only=False,
                model_size="1.7B",
                # instruct=INSTRUCT, # API에서 지원하는지 여부에 따라 조절 가능
                api_name="/generate_voice_clone"
            )
            
            generated_audio, status = result
            
            audio_path = generated_audio['path'] if isinstance(generated_audio, dict) else generated_audio
            temp_file = os.path.join(temp_dir, f"chunk_{i:02d}.wav")
            shutil.copy(audio_path, temp_file)
            audio_files.append(temp_file)
            print(f"   ✅ 성공")
            
        except Exception as e:
            print(f"   ❌ 실패: {e}")
    
    if not audio_files:
        print("❌ 생성된 파일 없음")
        return
    
    combined = AudioSegment.empty()
    for f in audio_files:
        combined += AudioSegment.from_wav(f) + AudioSegment.silent(duration=300)
    
    output_file = "/Users/a12/projects/tts/test_results/golden_8_개선_합본.wav"
    combined.export(output_file, format="wav")
    
    print(f"\n🎬 완료! 저장 위치: {output_file}")
    os.system(f'open "{output_file}"')
    shutil.rmtree(temp_dir)

if __name__ == "__main__":
    generate_chunked_audio()

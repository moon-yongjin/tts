#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HF Space 기반 커스텀 목소리 TTS 생성기
01-3의 청크 분할 방식 + HF Space API 조합
"""

from gradio_client import Client, handle_file
from huggingface_hub import login
import os
import re
import sys
import shutil
from pydub import AudioSegment
import datetime

# HF 토큰으로 로그인
HF_TOKEN = "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"
login(token=HF_TOKEN)

# Space ID
SPACE_ID = "moonyj8080/Qwen3-TTS10"

# 경로 설정
PROJ_ROOT = os.path.dirname(os.path.abspath(__file__))
VOICE_LIB_DIR = os.path.join(PROJ_ROOT, "voices")
DOWNLOADS_DIR = os.path.join(os.path.expanduser("~"), "Downloads")

# 황금 목소리 참조 (HF Space 테스트에서 검증된 설정)
CUSTOM_VOICE_WAV = os.path.join(VOICE_LIB_DIR, "golden_voice_8.wav")
CUSTOM_VOICE_REF_TEXT = "남자는 바닥에 엎드러지며 당황한 기색으로 입을 엽니다."

def clean_text(text):
    """텍스트 정리"""
    text = re.sub(r'\[(BGM|묘사|지문|설명|배경|음악|CHAPTER|챕터|SFX):?.*?\]', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\(.*?\)', '', text)
    return text.strip()

def split_chunks(text, max_chars=45):
    """텍스트를 자연스러운 청크로 분할 (01-3 방식: 문장 부호 + 길이 기반)"""
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

def format_srt_time(seconds):
    """SRT 시간 포맷"""
    td = datetime.datetime.fromtimestamp(seconds, datetime.UTC)
    return td.strftime('%H:%M:%S,%f')[:-3]

def generate_with_hf_space(script_text, output_path):
    """HF Space API로 음성 생성"""
    
    print(f"{'='*80}")
    print(f"🎤 HF Space 커스텀 목소리 TTS 생성")
    print(f"📍 01-3 청크 분할 방식 + golden_voice_8")
    print(f"{'='*80}\n")
    
    # 텍스트 정리 및 청크 분할
    clean = clean_text(script_text)
    chunks = split_chunks(clean, max_chars=45)
    
    print(f"📝 전체 텍스트: {len(clean)}자")
    print(f"📦 청크 개수: {len(chunks)}개 (문장 단위, 최대 45자)\n")
    
    # Space 연결
    try:
        client = Client(SPACE_ID)
        print("✅ HF Space 연결 성공!\n")
    except Exception as e:
        print(f"❌ Space 연결 실패: {e}")
        return False
    
    # 임시 디렉토리
    temp_dir = os.path.join(PROJ_ROOT, "temp_hf_chunks")
    os.makedirs(temp_dir, exist_ok=True)
    
    audio_files = []
    srt_entries = []
    current_time_ms = 0
    
    # 각 청크별로 음성 생성
    for i, chunk in enumerate(chunks, 1):
        print(f"⚡ [HF {i}/{len(chunks)}] Generating: {chunk[:40]}...")
        
        try:
            result = client.predict(
                ref_audio=handle_file(CUSTOM_VOICE_WAV),
                ref_text=CUSTOM_VOICE_REF_TEXT,  # 정확한 참조 텍스트
                target_text=chunk,
                language="Korean",
                use_xvector_only=False,
                model_size="1.7B",
                api_name="/generate_voice_clone"
            )
            
            generated_audio, status = result
            audio_path = generated_audio['path'] if isinstance(generated_audio, dict) else generated_audio
            
            # 임시 파일로 복사
            temp_file = os.path.join(temp_dir, f"chunk_{i:03d}.wav")
            shutil.copy(audio_path, temp_file)
            audio_files.append(temp_file)
            
            # SRT 엔트리 생성
            segment = AudioSegment.from_wav(temp_file)
            duration_ms = len(segment)
            
            start_sec = current_time_ms / 1000.0
            end_sec = (current_time_ms + duration_ms) / 1000.0
            srt_entries.append(f"{i}\n{format_srt_time(start_sec)} --> {format_srt_time(end_sec)}\n{chunk}\n\n")
            
            current_time_ms += duration_ms
            
            # 문장 끝에 따라 쉼 추가
            if any(chunk.endswith(p) for p in ['.', '?', '!']):
                current_time_ms += 400
            else:
                current_time_ms += 200
            
            print(f"   ✅ 성공 ({status})")
            
        except Exception as e:
            print(f"   ❌ 실패: {e}")
    
    if not audio_files:
        print("\n❌ 생성된 오디오 파일이 없습니다.")
        shutil.rmtree(temp_dir)
        return False
    
    print(f"\n{'='*80}")
    print(f"🔗 청크 합치는 중...")
    print(f"{'='*80}\n")
    
    # 오디오 파일 합치기
    combined = AudioSegment.empty()
    
    for i, audio_file in enumerate(audio_files, 1):
        print(f"   청크 {i} 추가 중...")
        audio = AudioSegment.from_wav(audio_file)
        combined += audio
        
        # 쉼 추가
        if i < len(audio_files):
            chunk_text = chunks[i-1]
            pause_ms = 400 if any(chunk_text.endswith(p) for p in ['.', '?', '!']) else 200
            combined += AudioSegment.silent(duration=pause_ms)
    
    # 최종 파일 저장
    combined.export(output_path, format="mp3", bitrate="192k")
    
    # SRT 파일 저장
    srt_path = output_path.replace(".mp3", ".srt")
    with open(srt_path, "w", encoding="utf-8-sig") as f:
        f.writelines(srt_entries)
    
    duration = len(combined) / 1000.0
    file_size = os.path.getsize(output_path)
    
    print(f"\n{'='*80}")
    print(f"🎬 완료!")
    print(f"{'='*80}")
    print(f"⏱️  총 길이: {duration:.1f}초")
    print(f"📦 파일 크기: {file_size:,} bytes")
    print(f"💾 저장 위치: {output_path}")
    print(f"📝 자막 파일: {srt_path}")
    print(f"{'='*80}\n")
    
    # 임시 파일 정리
    shutil.rmtree(temp_dir)
    print("🧹 임시 파일 정리 완료")
    
    return True

if __name__ == "__main__":
    target_file = sys.argv[1] if len(sys.argv) > 1 else os.path.join(PROJ_ROOT, "대본.txt")
    
    if not os.path.exists(target_file):
        print(f"❌ 대본 파일을 찾을 수 없습니다: {target_file}")
        sys.exit(1)
    
    with open(target_file, "r", encoding="utf-8") as f:
        script_text = f.read().strip()
    
    if not script_text:
        print("❌ 빈 대본")
        sys.exit(1)
    
    timestamp = datetime.datetime.now().strftime("%m%d_%H%M")
    base_filename = os.path.splitext(os.path.basename(target_file))[0]
    output_name = f"{base_filename}_HF_G8_{timestamp}.mp3"
    output_path = os.path.join(DOWNLOADS_DIR, output_name)
    
    success = generate_with_hf_space(script_text, output_path)
    
    if success:
        print("✅ 모든 작업이 완료되었습니다.")
    else:
        print("❌ 작업 실패")
        sys.exit(1)

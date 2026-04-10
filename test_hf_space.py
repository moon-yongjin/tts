#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hugging Face Space TTS 테스트 스크립트
Space: moonyj8080/Qwen3-TTS10
"""

from gradio_client import Client
from huggingface_hub import login
import os

# HF 토큰으로 로그인 (Private Space 접근용)
HF_TOKEN = "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"
login(token=HF_TOKEN)

# Space ID 고정
NEW_SPACE_ID = "moonyj8080/Qwen3-TTS10"

# 로컬 샘플 목소리 파일 경로
SAMPLE_VOICES = [
    "/Users/a12/projects/tts/voices/golden_voice_2.wav",
    "/Users/a12/projects/tts/voices/golden_voice_8.wav"
]

# 테스트할 텍스트
TEST_TEXTS = [
    "안녕하세요, 이것은 테스트 음성입니다.",
    "유료 공장으로 제대로 출근했습니다!",
    "목소리 복제 테스트를 진행하고 있습니다."
]

def test_tts_space():
    """HF Space TTS 테스트 실행"""
    
    print(f"📡 유료 10호 공장({NEW_SPACE_ID})으로 접속 시도 중...")
    
    try:
        # 이미 login()으로 인증했으므로 바로 연결
        client = Client(NEW_SPACE_ID)
        print("✅ 공장 연결 성공! (인증 완료)")
        
    except Exception as e:
        print(f"❌ 접속 실패: {e}")
        print("💡 Space가 'Running' 상태인지 확인하세요.")
        return
    
    # API 정보 확인
    print("\n📋 Space API 정보:")
    try:
        api_info = client.view_api()
        print(api_info)
    except Exception as e:
        print(f"API 정보 조회 실패: {e}")
    
    # 각 샘플 목소리로 테스트
    for idx, voice_path in enumerate(SAMPLE_VOICES, 1):
        if not os.path.exists(voice_path):
            print(f"❌ 샘플 파일 없음: {voice_path}")
            continue
            
        print(f"\n{'='*60}")
        print(f"🎤 테스트 {idx}: {os.path.basename(voice_path)}")
        print(f"{'='*60}")
        
        # 첫 번째 텍스트로 테스트
        test_text = TEST_TEXTS[0]
        
        try:
            print(f"📝 텍스트: {test_text}")
            print(f"🎵 참조 음성: {voice_path}")
            print("⏳ TTS 생성 중...")
            
            # API 호출 - /generate_voice_clone 사용
            result = client.predict(
                ref_audio=voice_path,                      # 참조 오디오 파일
                ref_text="이것은 참조 음성 샘플입니다.",    # 참조 오디오의 텍스트
                target_text=test_text,                     # 생성할 텍스트
                language="Korean",                         # 언어 설정
                use_xvector_only=False,                    # x-vector만 사용할지 여부
                model_size="1.7B",                         # 모델 크기
                api_name="/generate_voice_clone"
            )
            
            # result는 (generated_audio, status) 튜플
            generated_audio, status = result
            
            print(f"✅ 상태: {status}")
            print(f"✅ 결과물 생성 완료: {generated_audio}")
            
            # 결과 파일 확인
            if isinstance(generated_audio, dict) and 'path' in generated_audio:
                audio_path = generated_audio['path']
                if os.path.exists(audio_path):
                    file_size = os.path.getsize(audio_path)
                    print(f"📦 파일 크기: {file_size:,} bytes")
                    print(f"📂 저장 위치: {audio_path}")
            elif isinstance(generated_audio, str) and os.path.exists(generated_audio):
                file_size = os.path.getsize(generated_audio)
                print(f"📦 파일 크기: {file_size:,} bytes")
                print(f"📂 저장 위치: {generated_audio}")
            
        except Exception as e:
            print(f"❌ TTS 생성 실패: {e}")
            print(f"💡 에러 상세: {type(e).__name__}")
    
    print(f"\n{'='*60}")
    print("🎬 테스트 완료!")
    print(f"{'='*60}")

if __name__ == "__main__":
    test_tts_space()

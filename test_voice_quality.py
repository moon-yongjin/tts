#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
음성 복제 품질 테스트 스크립트
목소리가 제대로 고정되는지 다양한 길이의 텍스트로 테스트
"""

from gradio_client import Client, handle_file
from huggingface_hub import login
import os
import shutil

# HF 토큰으로 로그인
HF_TOKEN = "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"
login(token=HF_TOKEN)

# Space ID
SPACE_ID = "moonyj8080/Qwen3-TTS10"

# 샘플 목소리 파일
SAMPLE_VOICES = [
    "/Users/a12/projects/tts/voices/golden_voice_2.wav",
    "/Users/a12/projects/tts/voices/golden_voice_8.wav"
]

# 다양한 길이의 테스트 텍스트
TEST_TEXTS = {
    "짧은 텍스트": "안녕하세요, 테스트입니다.",
    
    "중간 텍스트": "안녕하세요, 이것은 음성 복제 테스트입니다. 목소리가 제대로 유지되는지 확인하고 있습니다.",
    
    "긴 텍스트": """
    안녕하세요, 여러분. 오늘은 인공지능 음성 합성 기술에 대해 이야기해보려고 합니다.
    최근 딥러닝 기술의 발전으로 인해 음성 복제 기술이 놀라울 정도로 발전했습니다.
    이제는 단 몇 초의 샘플 음성만으로도 매우 자연스러운 음성을 생성할 수 있게 되었습니다.
    하지만 중요한 것은 목소리의 특성이 긴 문장에서도 일관되게 유지되는지 확인하는 것입니다.
    """.strip(),
    
    "매우 긴 텍스트": """
    안녕하세요, 여러분. 오늘은 인공지능 음성 합성 기술의 발전과 그 응용 분야에 대해 자세히 알아보겠습니다.
    
    먼저, 음성 합성 기술의 역사를 간단히 살펴보면, 초기에는 단순한 규칙 기반 시스템에서 시작했습니다.
    하지만 최근 몇 년 사이에 딥러닝, 특히 트랜스포머 아키텍처의 등장으로 혁신적인 발전을 이루었습니다.
    
    현재의 음성 복제 기술은 단 몇 초의 참조 음성만으로도 매우 자연스럽고 감정이 담긴 음성을 생성할 수 있습니다.
    이는 콘텐츠 제작, 오디오북 제작, 접근성 향상 등 다양한 분야에서 활용되고 있습니다.
    
    하지만 가장 중요한 것은 생성된 음성이 긴 문장과 다양한 맥락에서도 일관된 음색과 특성을 유지하는지 확인하는 것입니다.
    이것이 바로 우리가 오늘 테스트하려는 핵심 내용입니다.
    """.strip()
}

def test_voice_cloning():
    """음성 복제 품질 테스트"""
    
    print(f"{'='*80}")
    print(f"🎤 음성 복제 품질 테스트 시작")
    print(f"{'='*80}\n")
    
    # 결과 저장 디렉토리
    output_dir = "/Users/a12/projects/tts/test_results"
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        client = Client(SPACE_ID)
        print("✅ Space 연결 성공!\n")
    except Exception as e:
        print(f"❌ Space 연결 실패: {e}")
        return
    
    # 각 샘플 목소리로 테스트
    for voice_idx, voice_path in enumerate(SAMPLE_VOICES, 1):
        if not os.path.exists(voice_path):
            print(f"❌ 샘플 파일 없음: {voice_path}\n")
            continue
        
        voice_name = os.path.basename(voice_path).replace('.wav', '')
        
        print(f"\n{'='*80}")
        print(f"🎵 샘플 목소리 {voice_idx}: {voice_name}")
        print(f"   파일: {voice_path}")
        
        # 오디오 길이 확인
        import subprocess
        try:
            duration = subprocess.check_output([
                'ffprobe', '-v', 'error', '-show_entries', 
                'format=duration', '-of', 
                'default=noprint_wrappers=1:nokey=1', voice_path
            ]).decode().strip()
            print(f"   길이: {float(duration):.2f}초")
        except:
            pass
        
        print(f"{'='*80}\n")
        
        # 각 텍스트 길이로 테스트
        for test_name, test_text in TEST_TEXTS.items():
            print(f"  📝 테스트: {test_name} ({len(test_text)}자)")
            print(f"  ⏳ 생성 중...")
            
            try:
                result = client.predict(
                    ref_audio=handle_file(voice_path),  # 파일을 제대로 업로드
                    ref_text="이것은 참조 음성 샘플입니다.",
                    target_text=test_text,
                    language="Korean",
                    use_xvector_only=False,
                    model_size="1.7B",
                    api_name="/generate_voice_clone"
                )
                
                generated_audio, status = result
                
                # 결과 저장
                if isinstance(generated_audio, dict) and 'path' in generated_audio:
                    audio_path = generated_audio['path']
                elif isinstance(generated_audio, str):
                    audio_path = generated_audio
                else:
                    print(f"  ❌ 알 수 없는 결과 형식: {type(generated_audio)}")
                    continue
                
                # 파일 복사
                if os.path.exists(audio_path):
                    output_filename = f"{voice_name}_{test_name.replace(' ', '_')}.wav"
                    output_path = os.path.join(output_dir, output_filename)
                    shutil.copy(audio_path, output_path)
                    
                    file_size = os.path.getsize(output_path)
                    print(f"  ✅ 성공! 상태: {status}")
                    print(f"  📦 크기: {file_size:,} bytes")
                    print(f"  💾 저장: {output_path}")
                else:
                    print(f"  ⚠️  파일을 찾을 수 없음: {audio_path}")
                
            except Exception as e:
                print(f"  ❌ 실패: {e}")
            
            print()
    
    print(f"\n{'='*80}")
    print(f"🎬 테스트 완료!")
    print(f"📂 결과 저장 위치: {output_dir}")
    print(f"{'='*80}\n")
    print("💡 생성된 음성 파일들을 직접 들어보고 목소리가 일관되게 유지되는지 확인하세요!")

if __name__ == "__main__":
    test_voice_cloning()

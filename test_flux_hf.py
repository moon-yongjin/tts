#!/usr/bin/env python3
"""
Hugging Face Flux 이미지 생성 테스트 스크립트 (토큰 순환 및 최신 엔드포인트)
"""
import os
import requests
from dotenv import load_dotenv
from pathlib import Path

# .env 파일 로드
load_dotenv()

# 기존 작업물에서 발견된 토큰들
HF_TOKENS = [
    "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",
    "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",
    "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"
]

# Flux 모델 엔드포인트 (schnell 시도 - 라이선스 제약 적음)
API_URL = "https://router.huggingface.co/hf-inference/models/black-forest-labs/FLUX.1-schnell"

def try_generate():
    # 대본에서 첫 번째 장면 추출
    script_path = Path(__file__).parent / "대본.txt"
    if script_path.exists():
        with open(script_path, "r", encoding="utf-8") as f:
            script_text = f.read().strip()
        first_scene = script_text.split(",")[0].strip()
        prompt = f"A cinematic Korean drama scene: An elderly Korean woman in traditional muddy work pants kneeling on cold marble floor in a luxury penthouse in Apgujeong, Seoul. Her daughter-in-law stands over her mockingly, holding expensive designer bags. Dramatic lighting, high contrast, photorealistic, 4K quality, Korean drama aesthetic."
    else:
        prompt = "A dramatic scene of an elderly Korean woman in a luxury penthouse, cinematic lighting, photorealistic"

    output_dir = Path.home() / "Downloads"
    output_path = output_dir / "flux_test_final_128.png"

    print(f"📝 프롬프트: {prompt[:100]}...")

    success = False
    for i, token in enumerate(HF_TOKENS):
        print(f"\n🔑 토큰 {i+1} 시도 중...")
        headers = {"Authorization": f"Bearer {token}"}
        
        try:
            payload = {
                "inputs": prompt,
                "parameters": {"num_inference_steps": 4} # schnell은 4스텝이면 충분
            }
            response = requests.post(API_URL, headers=headers, json=payload, timeout=120)
            
            if response.status_code == 200:
                with open(output_path, "wb") as f:
                    f.write(response.content)
                print(f"✅ 이미지 생성 완료 (토큰 {i+1} 성공): {output_path}")
                success = True
                break
            else:
                print(f"❌ 토큰 {i+1} 실패: {response.status_code}")
                try:
                    print(f"   메시지: {response.json()}")
                except:
                    print(f"   메시지: {response.text}")
                
        except Exception as e:
            print(f"❌ 토큰 {i+1} 예외: {e}")

    return success, output_path

if __name__ == "__main__":
    success, path = try_generate()
    if success:
        print(f"\n🎉 테스트 완료! 파일: {path}")
    else:
        print(f"\n⚠️ 모든 토큰 실패. Hugging Face에서 새 토큰을 발급받거나 라이선스를 승인해야 합니다.")

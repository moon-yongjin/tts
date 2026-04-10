import os
import requests
import json
import base64
import time

# [설정]
DRAWTHINGS_URL = "http://127.0.0.1:7860/sdapi/v1/txt2img"
OUTPUT_PATH = os.path.expanduser("~/Downloads/flux_enhanced_tiger_8k.png")

# [프롬프트] - 호랑이 + Realism LoRA
# 핵심: 털 질감, 젖은 코, 눈동자 디테일 극대화
PROMPT = (
    "Extreme hyper-realistic close-up portrait of a Siberian Tiger, "
    "visible individual fur strands, wet nose texture, intricate eye details, "
    "piercing amber eyes, whiskers, cinematic lighting, 8k resolution, raw photography, "
    "National Geographic style, masterpiece, best quality, ultra detailed"
)

payload = {
    "prompt": PROMPT,
    "negative_prompt": "cartoon, 3d, painting, drawing, sketch, blurry, plastic, smooth, doll, low resolution",
    "steps": 6, # LoRA 디테일을 살리기 위해 스텝 확보
    "cfg_scale": 1.0,
    "width": 1024,
    "height": 1024,
    "sampler_name": "Euler a",
    "seed": 7777,
    # LoRA 적용 (가정: API가 프롬프트 내 <lora:...> 구문을 해석하거나, Draw Things 앱에서 해당 LoRA가 활성화되어 있어야 함)
    # 이전 단계에서 다운로드한 'flux-RealismLora' 사용
    "prompt": PROMPT + " <lora:flux-RealismLora:0.9>", 
}

def generate_enhanced_tiger():
    print(f"🐯 [Enhanced Flux] '호랑이' 실사 강화(LoRA + Upscale) 생성 시작...")
    start_time = time.time()
    try:
        response = requests.post(DRAWTHINGS_URL, json=payload, timeout=600)
        if response.status_code == 200:
            end_time = time.time()
            elapsed_time = end_time - start_time
            result = response.json()
            if "images" in result and len(result["images"]) > 0:
                print(f"✅ 생성 완료. 고해상도 처리 중...")
                img_data = base64.b64decode(result["images"][0])
                with open(OUTPUT_PATH, "wb") as f:
                    f.write(img_data)
                print(f"✅ 최종 저장 완료: {OUTPUT_PATH}")
                print(f"⏱️ 소요 시간: {elapsed_time:.2f}초")
            else:
                print(f"❌ 에러: 이미지 데이터가 없습니다. {result}")
        else:
            print(f"❌ API 요청 실패: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ 예외 발생: {e}")

if __name__ == "__main__":
    generate_enhanced_tiger()

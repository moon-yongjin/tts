#!/usr/bin/env python3
"""
Draw Things Flux 배치 생성 (최적화된 고정 프롬프트 10개)
"""
import os
import requests
import base64
import time

# ===== 설정 =====
SD_API_URL = "http://127.0.0.1:7860/sdapi/v1/txt2img"
DOWNLOAD_DIR = os.path.expanduser("~/Downloads/Flux_Batch_DrawThings")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# ===== 부정 프롬프트 (Flux 전용 강화) =====
NEGATIVE_PROMPT = """
cartoon, anime, 3d render, CGI, painting, drawing, sketch, illustration, 
plastic skin, doll-like, smooth skin, airbrushed, oversaturated colors,
blurry, out of focus, low resolution, pixelated, jpeg artifacts,
bad anatomy, deformed hands, extra fingers, missing fingers, fused fingers, mutated hands, 
poorly drawn hands, malformed hands, long fingers, twisted fingers, broken fingers,
bad eyes, crossed eyes, lazy eye, asymmetric eyes, different sized eyes, misaligned eyes,
weird eyes, unnatural eyes, glowing eyes, red eyes, empty eyes, soulless eyes,
floating limbs, missing limbs, extra limbs, disconnected limbs,
text, watermark, signature, logo, frame, border,
yellow skin, jaundice, unnatural skin tone, wax figure,
symmetrical face, perfect face, flawless skin, beauty filter
""".replace('\n', ' ').strip()

# ===== 최적화된 프롬프트 10개 (대본 기반) =====
PROMPTS = [
    # 1. 약을 받는 장면
    "Close-up shot, A 72-year-old Korean woman, short gray hair with visible white roots, deep wrinkles around eyes and mouth, detailed realistic eyes with visible iris texture and natural reflections, trembling hands with five fingers clearly visible holding a small white pill, realistic hand anatomy with visible veins and age spots on hands, sitting on a beige fabric sofa in a modern Korean apartment living room, natural afternoon sunlight from large window on the left, tears welling up in symmetrical eyes with clear pupils, furrowed brow showing distrust, wearing a traditional navy blue hanbok with subtle floral patterns, 8k RAW photo, Fujifilm XT4, cinematic lighting, photorealistic, film grain, natural skin texture with age spots",
    
    # 2. 혼미한 척 연기
    "Medium shot, A 72-year-old Korean woman with detailed unfocused eyes showing realistic iris and natural eye whites, sitting slumped in a modern living room chair, hands resting naturally on armrests with five fingers each clearly visible, mouth slightly open as if confused, wearing a light gray cardigan over white blouse, son and daughter-in-law standing behind her with excited expressions and detailed facial features, harsh overhead fluorescent lighting creating stark shadows, cluttered coffee table with documents and an ink stamp pad, 8k RAW photo, Fujifilm XT4, cinematic cold lighting, photorealistic, film grain, realistic skin texture",
    
    # 3. 경찰과 변호사 등장
    "Wide shot, Korean apartment living room interior, uniformed police officers entering through the front door, professional male lawyer in dark suit holding legal documents, shocked middle-aged Korean man in casual clothes with pale complexion, modern furniture with cream-colored walls, natural daylight mixed with indoor lighting, tense atmosphere, 8k RAW photo, Fujifilm XT4, cinematic lighting, photorealistic, film grain",
    
    # 4. 파산 서류 확인
    "Extreme close-up, Trembling male hands holding official Korean bankruptcy documents with red stamps, visible sweat droplets on fingertips, shallow depth of field blurring background, harsh direct lighting from above, paper texture clearly visible, 8k RAW photo, Fujifilm XT4, macro photography, photorealistic, film grain, natural imperfections",
    
    # 5. 며느리의 애원
    "Low angle shot, A Korean woman in her 40s kneeling on wooden floor, both hands with five fingers each clasped together in desperate prayer position showing realistic hand anatomy, mascara running down cheeks, detailed eyes with visible tears and realistic iris texture, wearing a beige knit sweater, modern apartment interior with white walls, natural window light creating dramatic side lighting, emotional distress visible in facial muscles and symmetrical eye expression, 8k RAW photo, Fujifilm XT4, cinematic lighting, photorealistic, film grain, hyper-realistic eyes with natural reflections",
    
    # 6. 녹음기 재생
    "Close-up shot, Elderly Korean woman's wrinkled hand with five fingers clearly visible and realistic hand anatomy holding a small digital voice recorder, pressing play button with detailed index finger showing natural skin texture and wrinkles, sitting at a wooden dining table, shocked family members with detailed realistic eyes visible in soft focus background, warm indoor lighting from ceiling lamp, 8k RAW photo, Fujifilm XT4, cinematic lighting, photorealistic, film grain, skin pores visible on hands",
    
    # 7. 막내딸의 분노
    "Medium shot, Young Korean woman in her 30s with angry expression and detailed realistic eyes showing emotion, right hand with five fingers clearly visible raised mid-slap motion with realistic hand anatomy, targeting middle-aged man's face with detailed facial features, modern living room setting, natural daylight from large windows, dynamic motion blur on hand, tears streaming down woman's face from symmetrical eyes, 8k RAW photo, Fujifilm XT4, high shutter speed, photorealistic, film grain, emotional intensity in eyes",
    
    # 8. 최후 통첵
    "Portrait shot, A 72-year-old Korean woman with stern cold expression and detailed realistic eyes with clear iris and natural eye whites making direct eye contact with camera, sitting upright in a high-back chair, arms crossed showing hands with five fingers each and realistic hand anatomy, wearing traditional hanbok, soft natural light from window creating Rembrandt lighting, modern apartment background slightly out of focus, 8k RAW photo, Fujifilm XT4, cinematic lighting, photorealistic, film grain, weathered face with character and symmetrical eyes",
    
    # 9. 막내딸과의 포옹
    "Medium shot, Two Korean women embracing with hands visible showing five fingers each and realistic hand anatomy, elderly mother (72) with gray hair and detailed realistic eyes showing tears being hugged by daughter (35) with long black hair and symmetrical eyes also crying, both with natural facial expressions and detailed eye reflections, standing in modern apartment living room, warm golden hour sunlight streaming through sheer curtains, emotional reunion, 8k RAW photo, Fujifilm XT4, soft cinematic lighting, photorealistic, film grain, natural skin texture",
    
    # 10. 새 아파트에서의 평화
    "Wide shot, A 72-year-old Korean woman sitting peacefully on a small balcony, holding a cup of tea, overlooking a modest Korean apartment complex view, potted plants on balcony railing, wearing comfortable casual clothes, soft morning sunlight, serene expression with slight smile, 8k RAW photo, Fujifilm XT4, natural lighting, photorealistic, film grain, peaceful atmosphere"
]

# ===== 이미지 생성 함수 =====
def generate_image(prompt_text, index):
    """Draw Things API로 이미지 생성"""
    print(f"\n🎨 [{index}/10] 생성 중...")
    print(f"   📝 프롬프트: {prompt_text[:80]}...")
    
    payload = {
        "prompt": prompt_text,
        "negative_prompt": NEGATIVE_PROMPT,
        "steps": 15,
        "width": 832,
        "height": 1216,
        "cfg_scale": 3.5,
        "sampler_name": "Euler a",
        "seed": -1
    }
    
    try:
        start_time = time.time()
        response = requests.post(SD_API_URL, json=payload, timeout=300)
        
        if response.status_code == 200:
            r = response.json()
            if "images" in r and len(r["images"]) > 0:
                timestamp = time.strftime("%H%M%S")
                filename = f"Flux_{index:02d}_{timestamp}.png"
                filepath = os.path.join(DOWNLOAD_DIR, filename)
                
                img_data = base64.b64decode(r["images"][0])
                with open(filepath, "wb") as f:
                    f.write(img_data)
                
                elapsed = time.time() - start_time
                print(f"   ✅ 완료: {filename} ({elapsed:.1f}초)")
                return True
            else:
                print("   ❌ 이미지 데이터 없음")
                return False
        else:
            print(f"   ❌ API 에러: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ 오류: {e}")
        return False

# ===== 메인 실행 =====
def main():
    print("\n" + "="*60)
    print("  🚀 Flux Batch Generator (Draw Things)")
    print("="*60)
    print(f"  📂 출력 폴더: {DOWNLOAD_DIR}")
    print(f"  🎯 목표: 10장 생성 (대본 기반 최적화 프롬프트)")
    print("="*60 + "\n")
    
    success_count = 0
    
    for i, prompt in enumerate(PROMPTS, 1):
        print(f"\n{'─'*60}")
        if generate_image(prompt, i):
            success_count += 1
        
        if i < 10:
            time.sleep(2)
    
    print("\n" + "="*60)
    print(f"  ✅ 완료: {success_count}/10 성공")
    print(f"  📂 결과 확인: {DOWNLOAD_DIR}")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()

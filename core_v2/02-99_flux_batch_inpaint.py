#!/usr/bin/env python3
"""
Draw Things Flux 배치 생성 + 얼굴 인페인팅 (순차 처리 버전)
와이드 샷 및 전신 구도 강제 최적화
"""
import os
import requests
import base64
import time
import cv2
import numpy as np
from PIL import Image
import io

# ===== 설정 =====
SD_API_URL = "http://127.0.0.1:7860/sdapi/v1/txt2img"
IMG2IMG_API_URL = "http://127.0.0.1:7860/sdapi/v1/img2img"
DOWNLOAD_DIR = os.path.expanduser("~/Downloads/Flux_Batch_DrawThings")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# ===== 부정 프롬프트 (상반신/클로즈업 강력 금지) =====
NEGATIVE_PROMPT = """
cartoon, anime, 3d render, CGI, painting, drawing, sketch, illustration, 
close-up, extreme close-up, headshot, face focus, zoomed in, macro,
upper body, waist up, bust up, medium shot, portrait focus,
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

# ===== 최적화된 프롬프트 10개 (와이드 샷 및 전신 구도 명시) =====
# 프롬프트 앞에 "Wide cinematic shot, full body composition"을 명시하여 구도를 강제함
PROMPTS = [
    # 1. 약을 받는 장면
    "Wide cinematic shot, full body composition, cinematic interior of a modern Korean apartment living room, a 72-year-old Korean woman sitting on a sofa, a middle-aged man standing in front of her offering a small pill, focus on the atmospheric living room environment with natural afternoon sunlight, realistic furniture, 8k RAW photo, Fujifilm XT4, photorealistic",
    
    # 2. 혼미한 척 연기
    "Wide angle environmental view, full body shot of a 72-year-old Korean woman slumped in a living room chair, son and daughter-in-law standing in the background whispering, focus on the messy coffee table with legal documents, harsh overhead lighting creating tense atmosphere, 8k RAW photo, Fujifilm XT4, photorealistic, cinematic depth",
    
    # 3. 경찰과 변호사 등장
    "Extreme wide shot, cinematic view of the apartment entrance and living room, uniformed police officers walking in, a lawyer in a dark suit standing near the sofa, entire group visible within the room context, group dynamic, natural daylight, 8k RAW photo, Fujifilm XT4, dramatic cinematic composition, photorealistic",
    
    # 4. 파산 서류 확인
    "Wide environmental shot, a middle-aged Korean man standing next to a dining table looking at documents, the entire dining area visible, dimly lit room from one side, person's figure showing despair from a distance, emphasis on the scattered legal papers on the large table, 8k RAW photo, Fujifilm XT4, photorealistic",
    
    # 5. 며느리의 애원
    "Wide cinematic perspective, a woman kneeling on the floor of a large empty living room, looking towards someone off-camera, focus on the vastness of the space and her small figure on the floor, long shadows from window light, situational emotional distress, 8k RAW photo, Fujifilm XT4, wide cinematic shot, photorealistic",
    
    # 6. 녹음기 재생
    "Wide angle dining room scene, elderly mother sitting at the head of a long wooden table, a small recorder in the center, entire family standing around her in shock, spatial layout of the dining hall, warm indoor lighting, 8k RAW photo, Fujifilm XT4, storytelling composition, photorealistic",
    
    # 7. 막내딸의 분노
    "Wide shot of a modern living room, young woman standing and pointing at a man on the sofa, heated argument visible in the full-room context, scattered cushions and open balcony window, high shutterspeed, 8k RAW photo, Fujifilm XT4, cinematic lighting, photorealistic, wide cinematic lens",
    
    # 8. 최후 통첩
    "Wide environmental portrait, elderly Korean woman standing tall in a spacious apartment, her family members standing far in the background near a window, authoritative presence in the room context, traditional hanbok, 8k RAW photo, Fujifilm XT4, realistic environment, photorealistic",
    
    # 9. 막내딸과의 포옹
    "Wide cinematic shot, full figure view of two women embracing in the middle of a sunlit living room at golden hour, atmospheric scene with windows and floor context, sheer curtains, soft cinematic lighting, emotional situation, 8k RAW photo, Fujifilm XT4, photorealistic",
    
    # 10. 새 아파트에서의 평화
    "Extreme wide shot from inside the living room looking towards a balcony, a 72-year-old woman sitting peacefully, skyline visible through the window, focus on the interior plants and the transition from indoor to outdoor space, morning sunlight, 8k RAW photo, Fujifilm XT4, natural lighting, photorealistic"
]

# ===== 얼굴 감지 함수 =====
def detect_faces(image_array):
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    gray = cv2.cvtColor(image_array, cv2.COLOR_RGB2GRAY)
    # 넓은 샷에서도 얼굴을 잡을 수 있게 최소 크기 축소 (40 -> 30)
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
    return faces

# ===== 얼굴 인페인팅 함수 =====
def inpaint_face(image_array, face_coords, original_prompt):
    x, y, w, h = face_coords
    margin = int(w * 0.3)
    x1 = max(0, x - margin)
    y1 = max(0, y - margin)
    x2 = min(image_array.shape[1], x + w + margin)
    y2 = min(image_array.shape[0], y + h + margin)
    
    face_crop = image_array[y1:y2, x1:x2]
    if face_crop.shape[0] < 20 or face_crop.shape[1] < 20:
        return image_array

    face_pil = Image.fromarray(face_crop)
    buffered = io.BytesIO()
    face_pil.save(buffered, format="PNG")
    face_b64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
    
    payload = {
        "init_images": [face_b64],
        "prompt": f"{original_prompt}, focus on clear facial detail, realistic eyes, natural skin texture",
        "negative_prompt": NEGATIVE_PROMPT,
        "steps": 15,
        "denoising_strength": 0.45,
        "width": 512,
        "height": 512,
        "cfg_scale": 4.0,
        "sampler_name": "Euler a"
    }
    
    try:
        response = requests.post(IMG2IMG_API_URL, json=payload, timeout=120)
        if response.status_code == 200:
            r = response.json()
            if "images" in r and len(r["images"]) > 0:
                refined_face_data = base64.b64decode(r["images"][0])
                refined_face = Image.open(io.BytesIO(refined_face_data))
                refined_face_resized = refined_face.resize((x2-x1, y2-y1), Image.LANCZOS)
                result_array = image_array.copy()
                result_array[y1:y2, x1:x2] = np.array(refined_face_resized)
                return result_array
    except Exception as e:
        print(f"      ⚠️ 얼굴 보정 실패: {e}")
    return image_array

# ===== 메인 생성 함수 =====
def generate_one(prompt_text, index):
    print(f"\n🎨 [{index}/10] 생성 시작 (구도: Wide/Full Body)...")
    start_time = time.time()
    
    # 기본 이미지 생성
    payload = {
        "prompt": prompt_text,
        "negative_prompt": NEGATIVE_PROMPT,
        "steps": 20,
        "width": 768,
        "height": 1024,
        "cfg_scale": 3.5,
        "sampler_name": "Euler a",
        "seed": -1
    }
    
    try:
        response = requests.post(SD_API_URL, json=payload, timeout=300)
        if response.status_code != 200:
            print(f"   ❌ API 에러: {response.status_code}")
            return False
        
        r = response.json()
        img_data = base64.b64decode(r["images"][0])
        img = Image.open(io.BytesIO(img_data))
        img_array = np.array(img)
        print(f"   ✅ 기본 생성 완료 ({time.time() - start_time:.1f}초)")
        
        # 얼굴 보정
        faces = detect_faces(img_array)
        if len(faces) > 0:
            print(f"   👤 얼굴 {len(faces)}개 감지됨, 보정 중...")
            for face in faces:
                img_array = inpaint_face(img_array, face, prompt_text)
            print(f"   ✨ 보정 완료")
        else:
            print(f"   ℹ️ 얼굴 미감지 (상황 묘사 중심)")
        
        # 저장
        final_img = Image.fromarray(img_array)
        timestamp = time.strftime("%H%M%S")
        filename = f"Flux_Wide_{index:02d}_{timestamp}_refined.png"
        filepath = os.path.join(DOWNLOAD_DIR, filename)
        final_img.save(filepath)
        print(f"   💾 저장 완료: {filename} ({time.time() - start_time:.1f}초)")
        return True
    except Exception as e:
        print(f"   ❌ 오류: {e}")
        return False

def main():
    print("\n" + "="*60)
    print("  🚀 Flux Batch Wide Generator (순차 처리 + 전신 구도 고정)")
    print("="*60)
    
    start_all = time.time()
    for i, prompt in enumerate(PROMPTS, 1):
        generate_one(prompt, i)
        time.sleep(1)
        
    print("\n" + "="*60)
    print(f"  ✅ 모든 생성 완료 (총 {time.time() - start_all:.1f}초)")
    print(f"  📂 폴더: {DOWNLOAD_DIR}")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()

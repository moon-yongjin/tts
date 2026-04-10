import os
import sys
import requests
import base64
import time
import cv2
import json
import numpy as np
from PIL import Image
import io

# [설정]
SD_API_URL = "http://127.0.0.1:7860/sdapi/v1/txt2img"
IMG2IMG_API_URL = "http://127.0.0.1:7860/sdapi/v1/img2img"
OLLAMA_API_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3.1:latest" # 사용 가능한 모델: llama3.1, qwen2.5-coder, deepseek-r1 등
DOWNLOAD_DIR = os.path.expanduser("~/Downloads/Flux_Manual_Test")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# [스타일] Flux Realism
STYLE_PROMPT = "Photorealistic, 8k RAW photo, Fujifilm XT4, Cinematic Lighting, Skin texture detail, Weathered face, Hyper-realistic eyes, Subtle cinematic grain, film grain, high ISO, natural imperfections, skin pores, raw photo, <lora:flux-RealismLora:0.8>"

# [부정 프롬프트]
NEGATIVE_PROMPT = """
cartoon, anime, 3d render, CGI, painting, drawing, sketch, illustration, 
close-up, extreme close-up, headshot, face focus, zoomed in, macro,
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

def refine_prompt_with_ollama(user_input):
    print(f"🧠 [Ollama] 로컬 AI 모델({OLLAMA_MODEL})로 분석 중...")
    
    system_prompt = f"""
    You are an expert AI prompt engineer for Flux.1 image generator.
    Task: Translate the user input to English (if Korean) and expand it into a detailed, high-quality photographic prompt.
    Rules:
    1. Focus on REALISM, textures (skin pores, fabric), lighting (cinematic, natural), and atmosphere.
    2. Describe the scene from a medium or wide shot perspective unless specified otherwise.
    3. Output the English refined prompt ONLY. No introductory text.
    
    User Input: "{user_input}"
    Refined English Prompt:
    """
    
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": system_prompt,
        "stream": False,
        "options": {
            "temperature": 0.7,
            "num_predict": 150
        }
    }
    
    try:
        response = requests.post(OLLAMA_API_URL, json=payload, timeout=60)
        if response.status_code == 200:
            data = response.json()
            refined = data.get("response", "").strip()
            # 따옴표 등이 포함될 수 있으므로 정제
            refined = refined.replace('"', '').replace("'", "").strip()
            return refined
    except Exception as e:
        print(f"⚠️ Ollama 프롬프트 최적화 실패: {e}")
    return user_input

def detect_faces(image_array):
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    gray = cv2.cvtColor(image_array, cv2.COLOR_RGB2GRAY)
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(40, 40))
    return faces

def inpaint_face(image_array, face_coords, original_prompt):
    x, y, w, h = face_coords
    margin = int(w * 0.25)
    x1 = max(0, x - margin)
    y1 = max(0, y - margin)
    x2 = min(image_array.shape[1], x + w + margin)
    y2 = min(image_array.shape[0], y + h + margin)
    
    face_crop = image_array[y1:y2, x1:x2]
    face_pil = Image.fromarray(face_crop)
    
    buffered = io.BytesIO()
    face_pil.save(buffered, format="PNG")
    face_b64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
    
    payload = {
        "init_images": [face_b64],
        "prompt": f"{original_prompt}, focus on facial detail, realistic eyes, natural skin texture",
        "negative_prompt": NEGATIVE_PROMPT,
        "steps": 15,
        "denoising_strength": 0.4,
        "width": 512,
        "height": 512,
        "cfg_scale": 3.5,
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
    except: pass
    return image_array

def generate(user_input):
    refined_prompt = refine_prompt_with_ollama(user_input)
    print(f"✨ [AI Refined]: {refined_prompt}")
    
    full_prompt = f"{STYLE_PROMPT}, {refined_prompt}"
    
    payload = {
        "prompt": full_prompt,
        "negative_prompt": NEGATIVE_PROMPT,
        "steps": 20,
        "width": 768,
        "height": 1024,
        "cfg_scale": 3.5,
        "sampler_name": "Euler a",
        "seed": -1
    }

    try:
        print(f"🚀 [Flux] 이미지 생성 중 (20 steps)...")
        start_time = time.time()
        response = requests.post(SD_API_URL, json=payload, timeout=300)
        
        if response.status_code == 200:
            r = response.json()
            if "images" in r and len(r["images"]) > 0:
                img_data = base64.b64decode(r["images"][0])
                img = Image.open(io.BytesIO(img_data))
                img_array = np.array(img)
                
                faces = detect_faces(img_array)
                if len(faces) > 0:
                    print(f"   👤 얼굴 {len(faces)}개 감지됨, 보정 시작...")
                    for face in faces:
                        img_array = inpaint_face(img_array, face, refined_prompt)
                
                final_img = Image.fromarray(img_array)
                timestamp = time.strftime("%H%M%S")
                safe_prompt = "".join([c if c.isalnum() else "_" for c in user_input])[:20]
                filename = f"Flux_Ollama_{timestamp}_{safe_prompt}.png"
                filepath = os.path.join(DOWNLOAD_DIR, filename)
                
                final_img.save(filepath)
                print(f"✅ 생성 완료: {filename}")
                print(f"⏱️ 총 소요 시간: {time.time() - start_time:.2f}초")
            else:
                print("❌ 이미지 데이터 없음")
        else:
            print(f"❌ API 에러: {response.status_code}")
    except Exception as e:
        print(f"❌ 오류 발생: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        generate(sys.argv[1])

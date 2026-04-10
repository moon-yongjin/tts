import requests
import json
import base64
import os
import time
from datetime import datetime

# 1. 설정
DRAWTHINGS_URL = "http://127.0.0.1:7860/sdapi/v1/txt2img"
OUTPUT_BASE_DIR = os.path.expanduser("~/Downloads")
TIMESTAMP = datetime.now().strftime("%m%d_%H%M")
SAVE_DIR = os.path.join(OUTPUT_BASE_DIR, f"Yeonhwa_Dynamic_30_{TIMESTAMP}")
os.makedirs(SAVE_DIR, exist_ok=True)

# 2. 공통 설정 (고정: Steps 6, CFG 1.0)
COMMON_NEGATIVE = "easynegative, human_low_quality, bad_anatomy, distorted_face, blurry, lowres, text, watermark, signature, modern_clothing, western_features, 3d, render, illustration, simple background"
COMMON_PARAMS = {
    "sampler_name": "Euler A AYS",
    "steps": 6,
    "cfg_scale": 1.0,
    "width": 720,
    "height": 1280,
    "negative_prompt": COMMON_NEGATIVE,
    "model": "z_image_turbo_1.0_q8p.ckpt",
    "shift": 3.0,
    "sharpness": 6
}

# 3. 캐릭터 프로필 (Consistency)
IDO_YOUNG = "A 20-year-old Korean nobleman, fine purple silk hanbok, topknot (SANGTU), arrogant and cruel expression."
YEONHWA_YOUNG = "A beautiful 18-year-old Korean woman, humble white cotton hanbok, long dark hair tied lowly."
IDO_BEGGAR = "A miserable 30-year-old Korean beggar man, dirty thin face, messy matted hair, wearing filthy rags."
YEONHWA_RICH = "An extraordinarily beautiful 28-year-old Korean merchant woman, elegant red silk hanbok, golden hairpin (BINYEO), dignified cold aura."

# 4. 30개 청크별 맞춤형 프롬프트 (대사에 충실, 배경 및 오브젝트 강조)
SCENES = [
    # 01-09: 과거 (갈등과 추방)
    {"name": "Chunk_01", "prompt": f"Close-up of a sharp butcher's knife being sharpened on a wet stone, sparks flying, {IDO_YOUNG}'s shouting face blurred in background, intense historical drama."},
    {"name": "Chunk_02", "prompt": f"Low angle shot of the grand decorated wooden gate of a wealthy Korean nobleman's house (Hanok), {IDO_YOUNG} standing arrogantly on the stone steps, looking down."},
    {"name": "Chunk_03", "prompt": f"Traditional Korean wedding scene setting, a table full of colorful rice cakes and fruits, {YEONHWA_YOUNG} in red bridal hanbok (Hwarot) looking sad and pale, dim candlelight."},
    {"name": "Chunk_04", "prompt": f"A lonely room in a Hanok, {YEONHWA_YOUNG} sitting alone in the shadows, her shoes (Kkotsin) left solitary outside on the wooden porch, moonlight."},
    {"name": "Chunk_05", "prompt": f"A set traditional Korean table (Soban) with various side dishes and a bottle of rice wine, a hand of {IDO_YOUNG} slamming the table in anger, wine spilling."},
    {"name": "Chunk_06", "prompt": f"(Impact shot), {IDO_YOUNG} is mid-air, his foot and silk boot making direct hard contact with {YEONHWA_YOUNG}'s chest, {YEONHWA_YOUNG} is being knocked backward in pain, dynamic movement, scattered brass bowls and food fragments flying, dramatic shadows, intense historical drama."},
    {"name": "Chunk_07", "prompt": f"{IDO_YOUNG} shouting and pointing toward the dark open gate, {YEONHWA_YOUNG} on the floor gasping for air, glowing lanterns in the background, nighttime."},
    {"name": "Chunk_08", "prompt": f"(Wide shot), {YEONHWA_YOUNG} walking alone into the dark night and rain, holding a small cloth bundle (Botjim), coughing into her hand, cold wind blowing."},
    {"name": "Chunk_09", "prompt": f"Symbolic shot: A small golden light or butterfly flying away from the grand Hanok into the dark forest, the house becoming dim and cold."},
    
    # 10-18: 10년 후 (몰락과 빈곤)
    {"name": "Chunk_10", "prompt": f"Text '10 Years Later' feeling: A withered tree losing its leaves against a gray sky, shifting seasons, passage of time."},
    {"name": "Chunk_11", "prompt": f"Cinematic landscape of a ruined village, scorched earth, smoke rising from abandoned traditional houses, desolate and gray atmosphere."},
    {"name": "Chunk_12", "prompt": f"(Dramatic focus) Government soldiers in red uniforms putting seals on the grand wooden doors of {IDO_YOUNG}'s house, family members crying in the background."},
    {"name": "Chunk_13", "prompt": f"Empty interiors of a grand Hanok, dust flying in the sunlight beams, valuable antiques and silks being dragged away by soldiers."},
    {"name": "Chunk_14", "prompt": f"A dark and smoky gambling den (Tujeon), messy piles of traditional paper cards, {IDO_YOUNG} with bloodshot eyes holding a bottle of cheap liquor in a corner."},
    {"name": "Chunk_15", "prompt": f"{IDO_BEGGAR}'s thin shadow cast on the high wall of a luxurious mansion, he is shivering from hunger, winter's first snow falling."},
    {"name": "Chunk_16", "prompt": f"(Contrast shot), {IDO_BEGGAR} sitting in the mud, as a magnificent and colorful palanquin (Gama) with gold embroidery passes by, high detail."},
    {"name": "Chunk_17", "prompt": f"{IDO_BEGGAR} prostrating his head into the muddy ground in front of the palanquin, dirty fingers clawing at the dirt, desperation."},
    {"name": "Chunk_18", "prompt": f"(Close-up), Dirty, trembling hands of {IDO_BEGGAR} reaching toward a pair of expensive silk shoes of a guard, begging for a single coin, shallow depth of field."},
    
    # 19-30: 조우와 최후 (인과응보)
    {"name": "Chunk_19", "prompt": f"Close-up of a hand with jade rings slowly pulling back a heavy purple silk curtain from a palanquin window, golden embroidery shining."},
    {"name": "Chunk_20", "prompt": f"POV from inside the palanquin: Looking down at the miserable {IDO_BEGGAR} in the mud, the world looks bright and rich from the inside."},
    {"name": "Chunk_21", "prompt": f"(Reveal shot), The elegant and dignified face of {YEONHWA_RICH} appearing from behind the curtain, looking down with a cold and piercing gaze."},
    {"name": "Chunk_22", "prompt": f"(Success montage), A bustling warehouse full of silk rolls and jars, busy workmen loading wagons, {YEONHWA_RICH}'s logo or flag waving in the wind."},
    {"name": "Chunk_23", "prompt": f"{IDO_BEGGAR}'s face frozen in pure shock, eyes wide, seeing {YEONHWA_RICH}, the memory of the past flashing in his eyes."},
    {"name": "Chunk_24", "prompt": f"Close-up of {YEONHWA_RICH}'s mouth speaking with a cold smile, her chin held high, luxurious traditional jewelry (Binyeo) in her hair."},
    {"name": "Chunk_25", "prompt": f"(Wide cinematic), {IDO_BEGGAR} sobbing and banging his head on the ground, {YEONHWA_RICH}'s palanquin surrounded by dozens of wealthy guards."},
    {"name": "Chunk_26", "prompt": f"Close-up of {IDO_BEGGAR}'s tears falling into the dry dust, his shaking shoulders, total regret."},
    {"name": "Chunk_27", "prompt": f"The silk curtain of the palanquin being closed firmly by {YEONHWA_RICH}, her cold silhouette visible through the fabric, dusk light."},
    {"name": "Chunk_28", "prompt": f"A guard's hand throwing a piece of dark, rotten meat into the mud near {IDO_BEGGAR}'s face, dogs barking in the distant background."},
    {"name": "Chunk_29", "prompt": f"(Wide shot), {YEONHWA_RICH}'s palanquin moving away into the foggy distance, leaving the miserable {IDO_BEGGAR} alone in the dirt, sunset."},
    {"name": "Chunk_30", "prompt": f"Symbolic ending: A single withered rose or a broken butcher's knife in the snow, the moon rising over the ruins of the grand house, poetic ending."}
]

def generate_image(scene, index):
    print(f"🎨 [{index+1}/30] 생성 중: {scene['name']}")
    payload = COMMON_PARAMS.copy()
    payload["prompt"] = scene["prompt"] + ", (masterpiece, high quality, 8k, realistic skin texture, historical setting, high contrast, cinematic lighting)"
    payload["seed"] = 2024 + index
    
    try:
        response = requests.post(DRAWTHINGS_URL, json=payload, timeout=300)
        if response.status_code == 200:
            result = response.json()
            image_data = base64.b64decode(result['images'][0])
            file_path = os.path.join(SAVE_DIR, f"{scene['name']}.png")
            with open(file_path, "wb") as f:
                f.write(image_data)
            return True
        else:
            print(f"  ❌ API 오류: {response.status_code}")
    except Exception as e:
        print(f"  ❌ 에러: {e}")
    return False

def main():
    print(f"🚀 연화 이야기 [역동적 30장] 생성 프로세스 시작")
    print(f"📍 저장경로: {SAVE_DIR}")
    
    for i, scene in enumerate(SCENES):
        generate_image(scene, i)
        # time.sleep(0.5)
        
    print(f"\n🎉 완료! 총 30개의 이미지가 생성되었습니다.")
    print(f"📍 폴더 확인: {SAVE_DIR}")

if __name__ == "__main__":
    main()

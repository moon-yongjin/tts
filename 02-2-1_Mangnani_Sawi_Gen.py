import requests
import json
import base64
import os
import time
from datetime import datetime

# 1. 설정
API_URL = "http://127.0.0.1:7860/sdapi/v1/txt2img"
OUTPUT_BASE_DIR = os.path.expanduser("~/Downloads")
TIMESTAMP = datetime.now().strftime("%m%d_%H%M")
SAVE_DIR = os.path.join(OUTPUT_BASE_DIR, f"Mangnani_Sawi_Story_{TIMESTAMP}")
os.makedirs(SAVE_DIR, exist_ok=True)

# 2. 공통 프롬프트 설정 (시네마틱, 고퀄리티)
COMMON_NEGATIVE = "easynegative, human_low_quality, bad_anatomy, distorted_face, blurry, lowres, text, watermark, signature, hat, gat, modern_clothing"
COMMON_PARAMS = {
    "sampler_name": "Euler A AYS",
    "steps": 6,
    "cfg_scale": 1.0,
    "width": 720,
    "height": 1280,
    "negative_prompt": COMMON_NEGATIVE,
    "seed": 2024,
    "model": "z_image_turbo_1.0_q8p.ckpt",
    "shift": 3.0,
    "sharpness": 6
}

# 3. 캐릭터 고정 프로필
SAWI_PROFILE = "A handsome but disheveled 25-year-old Korean man (SAWI), messy topknot (SANGTU), wearing a light gray traditional Korean hanbok, drunk and flushed face, expressive eyes."
JANGMO_PROFILE = "An extraordinarily beautiful and elegant 38-year-old Korean noblewoman (JANGMO), sharp and sophisticated facial features, long dark hair tied neatly, wearing a translucent white sokjeoksam (traditional inner hanbok), intense and angry eyes."

# 4. 장면 리스트
SCENES = [
    {
        "name": "01_Drunk_Sawi",
        "prompt": f"(Cinematic shot, depth of field), {SAWI_PROFILE} staggering through a misty traditional Korean house (Hanok) hallway in the deep night, pitch black background, dim candlelight, mystery atmosphere, 35mm lens."
    },
    {
        "name": "02_Entering_Room",
        "prompt": f"(Suspenseful angle, medium shot), {SAWI_PROFILE} carefully opening a wooden sliding door (Changho-ji) in the middle of the night, peering into a dark room with anticipation, faint light from inside, absolute darkness outside."
    },
    {
        "name": "02b_Entering_Blanket_Dark",
        "prompt": f"(Silhouetted shot, absolute darkness), a man's dark silhouette slowly crawling into a traditional Korean silk blanket where a person is sleeping, deep night, pitch black room, faces are barely visible, tension, mysterious shadows."
    },
    {
        "name": "03_Under_Blanket",
        "prompt": f"(Close-up shot), a man's hand reaching under a colorful traditional Korean silk blanket in a pitch-black room, candlelight shadows, tactile texture, soft skin, secret and intimate atmosphere."
    },
    {
        "name": "09_Sawi_Whispering_Under_Blanket",
        "prompt": f"(Close-up shot), {SAWI_PROFILE} lying under a silk blanket in a dark room, whispering with a sly smile, candlelight reflecting in his eyes, intimate and mischievous expression, deep night."
    },
    {
        "name": "10_Jangmo_Shocked_Under_Blanket",
        "prompt": f"(Close-up shot), {JANGMO_PROFILE} lying under a silk blanket in the dark, eyes wide open with extreme shock and terror, hand grasping the blanket, candlelight shadows, stunningly beautiful but horrified, deep night."
    },
    {
        "name": "04_Candle_Light_Up",
        "prompt": f"(Dramatic lighting, high contrast), {JANGMO_PROFILE} lighting a candle in the deep night, her stunningly beautiful face illuminated by flicking orange fire light, pitch black background, eyes burning with fierce anger, looking at SAWI with shock."
    },
    {
        "name": "05_Shocked_Sawi",
        "prompt": f"(Close-up shot, exaggerated expression), {SAWI_PROFILE}'s face turning pale with terror in a dark room under candlelight, Realizing the fatal mistake, high tension, cinematic horror lighting."
    },
    {
        "name": "06_Shameless_Excuse",
        "prompt": f"(Medium shot), {SAWI_PROFILE} patting {JANGMO_PROFILE}'s thigh under the blanket with a forced calm expression, deep night room, dim orange candlelight, {JANGMO_PROFILE} looking utterly bewildered and disgusted."
    },
    {
        "name": "07_Angry_Jangmo",
        "prompt": f"(Low angle shot, empowering), {JANGMO_PROFILE} standing up in the dark, reaching for a wooden stick (Mongdungi), candlelight illumination, her beautiful face distorted with rage, SAWI trembling in front of her."
    },
    {
        "name": "11_Jangmo_Attacking",
        "prompt": f"(Action shot, dynamic motion), {JANGMO_PROFILE} swinging a wooden stick (Mongdungi) with intense rage, her beautiful but fierce face, flying dust and shadows in candlelight, deep night, cinematic action."
    },
    {
        "name": "12_Sawi_Running_Away",
        "prompt": f"(Medium shot, wide-eyed terror), {SAWI_PROFILE} scrambling to get away, looking back with pure panic, falling over traditional furniture, frantic movement in the dark Hanok room, candlelight flicker."
    },
    {
        "name": "08_Escape",
        "prompt": f"(Action shot, wide angle), {SAWI_PROFILE} jumping over a stone wall (Damjang) of a Hanok under the moonlight and deep night sky, pitch black background, funny and desperate flee, 24mm lens."
    }
]

def generate_image(scene, index):
    print(f"\n🎨 장면 [{index+1}/{len(SCENES)}] 생성 중: {scene['name']}")
    
    payload = COMMON_PARAMS.copy()
    payload["prompt"] = scene["prompt"] + ", masterpiece, high quality, 8k, realistic skin texture, detailed hanbok"
    
    try:
        response = requests.post(API_URL, json=payload, timeout=300)
        if response.status_code == 200:
            result = response.json()
            image_data = base64.b64decode(result['images'][0])
            
            file_path = os.path.join(SAVE_DIR, f"{scene['name']}.png")
            with open(file_path, "wb") as f:
                f.write(image_data)
            print(f"  ✅ 저장 완료: {file_path}")
            return file_path
        else:
            print(f"  ❌ API 오류 ({response.status_code}): {response.text}")
    except Exception as e:
        print(f"  ❌ 에러 발생 ({scene['name']}): {e}")
    return None

def main():
    print(f"🚀 '망나니 사위' 이미지 생성 프로세스 시작 (저장경로: {SAVE_DIR})")
    
    generated_files = []
    for i, scene in enumerate(SCENES):
        path = generate_image(scene, i)
        if path:
            generated_files.append(path)
        time.sleep(1) # 부하 방지
    
    print(f"\n🎉 완료! 총 {len(generated_files)}개의 이미지가 생성되었습니다.")
    print(f"📍 생성된 폴더를 확인하세요: {SAVE_DIR}")

if __name__ == "__main__":
    main()

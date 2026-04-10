import requests
import json
import time
import os

# --- [설정 영역] ---
# 지수(며느리): 슬프지만 우아하고 아름다운 젊은 여성
# 김 회장(시아버지): 70대 초반, 탐욕스럽고 권위적인 눈빛의 재벌가 노인
CFG_SCALE = 1.0  # 터보 모델 최적화 속도
STEPS = 4
SEED = -1
OUTPUT_DIR = "/Users/a12/Downloads/Jisu_Drama_36"
os.makedirs(OUTPUT_DIR, exist_ok=True)

COMMON_PROMPT = "8k resolution, cinematic lighting, masterwork, detailed textures, 1980s retro cinematic film style, highly detailed skin,"

# 36개의 핵심 시퀀스 프롬프트 구성
prompts = [
    # 1-6: 장례식장 및 소유욕
    f"{COMMON_PROMPT} A grand funeral hall in a luxury mansion, Kim Chairman (greedy old man in early 70s, sharp eyes) looking at Jisu's neck.",
    f"{COMMON_PROMPT} Jisu (beautiful young woman, classy white funeral dress, pale neck, sorrowful eyes), tears rolling down.",
    f"{COMMON_PROMPT} Close up on Kim Chairman's greedy and lustful smirk while looking at Jisu.",
    f"{COMMON_PROMPT} Kim Chairman handing over a stack of debt papers to trembling Jisu.",
    f"{COMMON_PROMPT} Kim Chairman whispering into Jisu's ear like a snake, cold atmosphere.",
    f"{COMMON_PROMPT} Jisu looking at her father's debt documents, feeling hopeless.",
    
    # 7-12: 오피스텔 감금 및 럭셔리 감옥
    f"{COMMON_PROMPT} Jisu trapped in an ultra-luxurious penthouse apartment, looking out the floor-to-ceiling window.",
    f"{COMMON_PROMPT} Luxury jewelry and designer bags piled up on a table, a symbol of a golden cage.",
    f"{COMMON_PROMPT} Close up on a hidden camera lens blinking in the corner of a luxury room.",
    f"{COMMON_PROMPT} Jisu sitting on a bed, feeling suffocated, luxury symbols everywhere.",
    f"{COMMON_PROMPT} Kim Chairman entering the room late at night, drunk and aggressive.",
    f"{COMMON_PROMPT} Kim Chairman shouting and waving a debt document at crying Jisu.",
    
    # 13-18: 수행비서의 등장 및 비밀 거래
    f"{COMMON_PROMPT} A loyal secretary (middle-aged man, stoic) secretly recording Kim Chairman's verbal abuse.",
    f"{COMMON_PROMPT} The secretary secretly handing a small USB/recording device to Jisu in a dark corridor.",
    f"{COMMON_PROMPT} Jisu listening to the recording on a laptop, eyes widening in shock.",
    f"{COMMON_PROMPT} Close up on Jisu's face, her sadness turning into a fierce determination for revenge.",
    f"{COMMON_PROMPT} Jisu looking at herself in a mirror, getting ready for a party, wearing a hidden recorder.",
    f"{COMMON_PROMPT} A wide shot of the grand anniversary party of the group, luxury chandeliers.",
    
    # 19-24: 파티장 폭로전 (클라이맥스)
    f"{COMMON_PROMPT} Jisu standing on a grand stage at the party, holding a microphone.",
    f"{COMMON_PROMPT} A giant screen at the party suddenly showing Kim Chairman's disgusting face and audio waves.",
    f"{COMMON_PROMPT} The guests at the party looking shocked and whispering as the audio plays.",
    f"{COMMON_PROMPT} Kim Chairman on the VIP seat, face turning pale and trembling with rage.",
    f"{COMMON_PROMPT} Jisu screaming 'I am not this beast's toy!' into the microphone, full of dignity.",
    f"{COMMON_PROMPT} Chaos in the party hall, press flashing cameras at the exposed chairman.",
    
    # 25-30: 체포 및 몰락
    f"{COMMON_PROMPT} Police officers entering the party hall, surrounding Kim Chairman.",
    f"{COMMON_PROMPT} Close up on shiny silver handcuffs being snapped onto Kim Chairman's wrists.",
    f"{COMMON_PROMPT} Kim Chairman being dragged away by police, his expensive tuxedo wrinkled.",
    f"{COMMON_PROMPT} Reporters rushing towards the falling chairman, chaos.",
    f"{COMMON_PROMPT} Jisu watching the chairman being dragged away, a faint look of relief on her face.",
    f"{COMMON_PROMPT} The grand group logo falling or flickering, symbolizing the fall of the empire.",
    
    # 31-36: 2부 예고 (비밀 금고 및 떡밥)
    f"{COMMON_PROMPT} A large, heavy metal secret safe door slowly opening in a dark room.",
    f"{COMMON_PROMPT} Inside the safe, a mysterious glowing object wrapped in silk.",
    f"{COMMON_PROMPT} Jisu looking at her necklace, which has a hidden compartment or engraving.",
    f"{COMMON_PROMPT} Kim Chairman in a dark prison cell, looking defeated and miserable.",
    f"{COMMON_PROMPT} A dramatic shot of a mysterious ledger found in the safe, full of secrets.",
    f"{COMMON_PROMPT} Ending shot: Jisu walking towards the light, away from the mansion, with 2部 (Part 2) text overlay."
]

def generate_images():
    for i, prompt in enumerate(prompts):
        filename = f"Jisu_Drama_{i+1:02d}.png"
        save_path = os.path.join(OUTPUT_DIR, filename)
        
        payload = {
            "prompt": prompt,
            "strength": 1.0,
            "guidance_scale": CFG_SCALE,
            "steps": STEPS,  # num_inference_steps에서 steps로 수정
            "seed": SEED,
            "width": 512,
            "height": 768
        }
        
        print(f"🎬 [{i+1}/36] Rendering: {filename}")
        try:
            response = requests.post("http://127.0.0.1:7860/sdapi/v1/txt2img", json=payload)
            if response.status_code == 200:
                data = response.json()
                # API 응답에서 이미지를 추출하여 저장
                if "images" in data and len(data["images"]) > 0:
                    import base64
                    with open(save_path, "wb") as f:
                        f.write(base64.b64decode(data["images"][0]))
                    print(f"✅ Saved: {filename}")
                else:
                    print(f"⚠️ Success but no image data in response: {filename}")
                time.sleep(1) 
            else:
                print(f"❌ Failed ({response.status_code}): {response.text}")
        except Exception as e:
            print(f"⚠️ Error connectiong to Draw Things: {e}")

if __name__ == "__main__":
    print("🚀 [Jisu Drama] 36-Frame Cinematic Storyboard Generation Started.")
    generate_images()
    print("🔥 All 36 frames are queued for rendering.")

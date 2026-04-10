import requests
import json
import os
import time

# [설정] 형님 지시 규격 칼준수
WIDTH = 576
HEIGHT = 1024
STEPS = 5
SAMPLER = "Euler A AYS"
MODEL = "z_image_turbo_1.0_q8p.ckpt"
DRAW_THINGS_URL = "http://127.0.0.1:7860"
OUTPUT_DIR = os.path.join(os.path.expanduser("~"), "Downloads", "Jaejin_Story_30")

if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

import base64

NEGATIVE = "heavy makeup, dark eyeliner, dark lips, text, watermark, banner, low quality, blurry, distorted, anime, cartoon, illustration, drawing, extra fingers, messy hands, distorted face, nsfw, naked, bad proportions, bad anatomy, doll face, plastic surgery, airbrushed, 3d, cg, cropped frame"

# ... (scenes 리스트는 동일하므로 중략 가능하나 전체 교체 시 포함)
scenes = [
    # [소개] 잘나가는 이재진 변호사
    "Cinematic shot, Lee Jae-jin, successful Korean lawyer in his late 30s, sharp suit, luxurious law firm office background, confident expression, high-end interior, photorealistic",
    "Close up, Lee Jae-jin lawyer, cold and ambitious eyes, adjusting silk tie, expensive watch visible, cinematic lighting",
    "Lee Jae-jin walking through a glass-walled corridor of a skyscraper, blurred city view, powerful aura",
    
    # [과거] 가난한 고시생 시절과 아내 수진
    "Flashback, 10 years ago, small messy one-room apartment, young Jae-jin studying hard under a dim desk lamp, exhausted look",
    "Young wife Su-jin, mid-20s, kind and humble face, wearing a simple apron, serving food in a busy small restaurant, sweat on forehead, tired but smiling",
    "Su-jin working late at night in a convenience store, fluorescent lighting, stacking boxes, rough and reddened hands visible",
    "Su-jin packing a humble lunch box with a small note, looking at sleeping Jae-jin with love",
    
    # [약속] 수진의 거친 손을 잡는 재진
    "Close up, Jae-jin's clean hand holding Su-jin's rough, red, and cracked hand, emotional lighting, promise",
    "Young Jae-jin crying slightly, holding Su-jin's hands, worn-out wallpaper background, deep vow",
    
    # [성공과 새로운 여자] 은서와의 만남
    "10 years later, Jae-jin in a luxury lounge, meeting Eun-seo, a wealthy and glamorous heiress, elegant dress, expensive jewelry",
    "Eun-seo smiling charmingly at Jae-jin, high-end champagne on the table, elite atmosphere",
    "Jae-jin and Eun-seo walking together at a red carpet event, flashing camera lights, pretending to be a perfect couple",
    
    # [거짓말] "미혼입니다"
    "Jae-jin bowing to a powerful Chairman, expensive hanok background, looking respectful but deceitful",
    "Jae-jin's face showing a subtle evil smirk while saying a lie, dark shadow, cinematic tension",
    
    # [결혼식] 나타난 수진과 배신
    "Grand luxury hotel wedding hall, flowers everywhere, Jae-jin and Eun-seo in tuxedo and wedding dress",
    "Su-jin standing at the entrance of the wedding hall, wearing outdated cheap clothes, pale face, trembling with shock",
    "Su-jin trying to reach Jae-jin, security guards blocking and dragging her out, people whispering, chaotic scene",
    "Jae-jin looking at Su-jin with cold, disgusted eyes, shouting 'Get that crazy stalker out!', cruel expression",
    "Su-jin crying on the cold floor outside the hotel, lonely and heartbroken, wedding hall lights in the far background",
    
    # [복수의 시작] 조력자와의 만남
    "Su-jin sitting in a dark cafe, meeting an elegant but cold middle-aged woman (Eun-seo's mother), meaningful eye contact",
    "Eun-seo's mother handing over a thick brown envelope (secret ledger), revenge planning",
    "Su-jin's eyes changing from sadness to fierce determination, sharp look, cinematic close-up",
    
    # [몰락] 압수수색과 체포
    "Prosecution team raiding a luxury penthouse, boxes of evidence, chaos",
    "Jae-jin in a tailored suit, now messy and panicked, being held by prosecutors, flashing lights",
    "Close up, Jae-jin in an orange prisoner uniform, sitting in a dim interrogation room, despairing face",
    "Jae-jin behind bars, holding the prison bars, regretful but miserable look",
    
    # [비참한 끝] 거리를 헤매는 재진
    "Jae-jin, now homeless and messy, wandering the cold streets at night, crying out 'Don't go!', pathetic look",
    "Jae-jin sitting on a park bench, holding a ragged old bag, empty eyes, falling autumn leaves",
    
    # [티저] 비밀 장부의 진실
    "Close up, a page of the secret ledger, a shocking name written on it (blurred), mysterious lighting",
    "Su-jin standing on a bridge, looking at the city lights, holding a hidden necklace, strong and independent look"
]

def generate_image(prompt, index):
    filename = f"Jaejin_{index:02d}.png"
    filepath = os.path.join(OUTPUT_DIR, filename)
    
    print(f"🚀 [{index+1}/{len(scenes)}] 생성 중: {filename}")
    
    # [핵심] 형님 필살 규격 576x1024, 5스텝
    payload = {
        "prompt": f"{prompt}, natural makeup, bare face look, soft cinematic, ultra-detailed textures, realistic lighting, 8k professional photography, film grain, 1980s retro aesthetics, raw texture",
        "negative_prompt": NEGATIVE,
        "steps": STEPS,
        "width": WIDTH,
        "height": HEIGHT,
        "seed": -1,
        "model": MODEL,
        "guidance_scale": 1.0,
        "sampler": SAMPLER,
        "shift": 3.0,
        "sharpness": 6
    }
    
    try:
        response = requests.post(f"{DRAW_THINGS_URL}/sdapi/v1/txt2img", json=payload, timeout=600)
        if response.status_code == 200:
            data = response.json()
            if "images" in data:
                with open(filepath, "wb") as f:
                    f.write(base64.b64decode(data["images"][0]))
                print(f"✅ 저장 완료: {filepath}")
        else:
            print(f"❌ 생성 실패 ({response.status_code}): {response.text}")
    except Exception as e:
        print(f"⚠️ 에러 발생: {str(e)}")

if __name__ == "__main__":
    print(f"🎨 드로띵 렌더링 시작: {WIDTH}x{HEIGHT}, {STEPS}단계")
    for i, scene in enumerate(scenes):
        generate_image(scene, i + 1)
        time.sleep(1) # 서버 과부하 방지
    print("\n🎉 모든 이미지 생성이 완료되었습니다!")


import requests
import json
import os
import time
import base64

# [설정] 형님 지시 규격 칼준수
WIDTH = 576
HEIGHT = 1024
STEPS = 5
SAMPLER = "Euler A AYS"
MODEL = "z_image_turbo_1.0_q8p.ckpt"
DRAW_THINGS_URL = "http://127.0.0.1:7860"
OUTPUT_DIR = os.path.join(os.path.expanduser("~"), "Downloads", "Jaejin_Story_36_Modern")

if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

NEGATIVE = "fog, hazy, mist, low contrast, washed out, dull, grey, gray, monochrome, heavy makeup, dark eyeliner, dark lips, text, watermark, banner, low quality, blurry, distorted, anime, cartoon, illustration, drawing, extra fingers, messy hands, distorted face, nsfw, naked, bad proportions, bad anatomy, doll face, plastic surgery, airbrushed, 3d, cg, cropped frame"

# [총 36장 구성]
scenes = [
    # 1-3: 성공한 변호사 이재진
    "Cinematic shot, Lee Jae-jin, successful Korean lawyer in his late 30s, sharp suit, luxurious law firm office background, confident expression, high-end interior, photorealistic",
    "Close up, Lee Jae-jin lawyer, cold and ambitious eyes, adjusting silk tie, expensive watch visible, cinematic lighting",
    "Lee Jae-jin walking through a glass-walled corridor of a skyscraper, blurred city view, powerful aura",
    
    # 4-7: 힘들던 젊은 시절 (뒷바라지하는 수진)
    "Modern cinematic memory, Lee Jae-jin in his 20s, small but clean studio apartment, studying hard under a bright LED desk lamp, determined look",
    "Young wife Su-jin, mid-20s, kind and humble face, wearing a modern clean apron, serving food in a busy trendy small restaurant, bright lighting",
    "Su-jin working late at night in a modern convenience store, bright LED lighting, stacking boxes, hands showing hard work",
    "Su-jin packing a clean modern lunch box with a small note, looking at sleeping Jae-jin with love, warm home lighting",
    
    # 8-10: 헌신적인 약속
    "Close up, Jae-jin's clean hand holding Su-jin's hands, emotional bright lighting, promise of a better future",
    "Young Jae-jin crying slightly, holding Su-jin's hands, modern apartment background, deep vow",
    "A subtle close up of a simple but elegant wedding ring Jae-jin bought for Su-jin, shiny and clear, placed on a clean wooden desk", # 추가 1
    
    # 11-14: 배신의 시작 (은서와의 만남)
    "10 years later, Jae-jin in a luxury lounge, meeting Eun-seo, a wealthy and glamorous heiress, elegant dress, expensive jewelry",
    "Eun-seo smiling charmingly at Jae-jin, high-end champagne on the table, elite atmosphere",
    "Jae-jin and Eun-seo walking together at a red carpet event, flashing camera lights, pretending to be a perfect couple",
    "Jae-jin looking at his reflection in a luxury mirror, adjusting his expensive tuxedo, eyes filled with cold ambition", # 추가 2
    
    # 15-17: 거짓말과 회장님
    "Jae-jin bowing to a powerful Chairman, expensive hanok background, looking respectful but deceitful",
    "Jae-jin's face showing a subtle evil smirk while saying a lie in a dark room, cinematic tension",
    "Close up of business contract being signed by Jae-jin, focus on his expensive fountain pen and cold hands", # 추가 3
    
    # 18-23: 충격의 결혼식과 배신
    "Grand luxury hotel wedding hall, flowers everywhere, Jae-jin and Eun-seo in tuxedo and wedding dress",
    "Su-jin standing at the entrance of the wedding hall, wearing outdated cheap clothes, pale face, trembling with shock",
    "Su-jin trying to reach Jae-jin, security guards blocking and dragging her out, people whispering, chaotic scene",
    "Jae-jin looking at Su-jin with cold, disgusted eyes, shouting 'Get that crazy stalker out!', cruel expression",
    "Su-jin crying on the cold floor outside the hotel, lonely and heartbroken, wedding hall lights in the far background",
    "The expensive wedding cake being cut by Jae-jin and Eun-seo inside, while Su-jin's tears fall on the pavement outside", # 추가 4
    
    # 24-26: 복수의 서막
    "Su-jin sitting in a dark cafe, meeting an elegant but cold middle-aged woman (Eun-seo's mother), meaningful eye contact",
    "Eun-seo's mother handing over a thick brown envelope (secret ledger), revenge planning",
    "Su-jin's eyes changing from sadness to fierce determination, sharp look, cinematic close-up",
    
    # 27-31: 몰락과 체포
    "Prosecution team raiding a luxury penthouse, boxes of evidence being carried out, chaotic lighting",
    "Jae-jin in a tailored suit, now messy and panicked, being held by prosecutors, flashing blue and red lights",
    "Close up, Jae-jin in an orange prisoner uniform, sitting in a dim interrogation room, despairing face",
    "Jae-jin behind bars, holding the prison bars with trembling hands, regretful but miserable look",
    "Jae-jin in the prison yard, looking up at the gray sky through barbed wire, a single tear of regret on his cheek", # 추가 5
    
    # 32-34: 비참한 광경
    "Jae-jin, now homeless and messy, wandering the cold streets at night, crying out 'Don't go!', pathetic look",
    "Jae-jin sitting on a park bench, holding a ragged old bag, empty eyes, falling autumn leaves around him",
    "Jae-jin looking at a discarded newspaper featuring his own downfall headline, wind blowing trash around him at night", # 추가 6
    
    # 35-36: 진실과 새로운 시작
    "Close up, a page of the secret ledger, a shocking name written on it, mysterious dramatic lighting",
    "A dramatic silhouette of Su-jin walking toward a new bright future, the city skyline glowing behind her, independent and strong"
]

def generate_image(prompt, index):
    filename = f"Jaejin_{index:02d}.png"
    filepath = os.path.join(OUTPUT_DIR, filename)
    
    print(f"🚀 [{index}/{len(scenes)}] 생성 중: {filename}")
    
    payload = {
        "prompt": f"{prompt}, high-end vibrant cinematic, extremely sharp details, vivid colors, high contrast, clear background, 8k resolution, masterpiece, professional studio lighting, highly detailed face",
        "negative_prompt": NEGATIVE,
        "steps": STEPS,
        "width": WIDTH,
        "height": HEIGHT,
        "seed": -1,
        "model": MODEL,
        "guidance_scale": 1.0,
        "sampler": SAMPLER,
        "shift": 3.0,
        "sharpness": 6,
        "seed_mode": "Scale Alike"
    }
    
    try:
        response = requests.post(f"{DRAW_THINGS_URL}/sdapi/v1/txt2img", json=payload, timeout=600)
        if response.status_code == 200:
            data = response.json()
            if "images" in data:
                with open(filepath, "wb") as f:
                    f.write(base64.b64decode(data["images"][0]))
                print(f"✅ 저장 완료: {filepath}")
                return True
        else:
            print(f"❌ 생성 실패 ({response.status_code}): {response.text}")
    except Exception as e:
        print(f"⚠️ 에러 발생: {str(e)}")
    return False

if __name__ == "__main__":
    print(f"🎨 드로띵 렌더링 시작 (총 {len(scenes)}장): {WIDTH}x{HEIGHT}, {STEPS}단계")
    start = time.time()
    success = 0
    for i, scene in enumerate(scenes):
        if generate_image(scene, i + 1):
            success += 1
        time.sleep(0.5)
    
    end = time.time()
    print(f"\n🎉 모든 작업 완료! ({success}/{len(scenes)} 성공, 소요시간: {end-start:.1f}s)")
    print(f"📍 저장 위치: {OUTPUT_DIR}")
    os.system(f"open {OUTPUT_DIR}")

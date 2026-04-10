import json
import requests
import time
import os
import base64

# [설정]
DRAW_THINGS_URL = "http://127.0.0.1:7860" 
TIMESTAMP = time.strftime('%m%d_%H%M')
DOWNLOADS_DIR = f"/Users/a12/Downloads/Frames_ParkMJ_Storyboard_{TIMESTAMP}"

if not os.path.exists(DOWNLOADS_DIR):
    os.makedirs(DOWNLOADS_DIR)

def check_and_start_draw_things():
    check_app = os.popen('pgrep -x "Draw Things"').read().strip()
    if not check_app:
        os.system('open -a "Draw Things"')
        time.sleep(10)
    try:
        requests.get(f"{DRAW_THINGS_URL}/sdapi/v1/options", timeout=2)
        return True
    except:
        return False

def generate_frame(frame_num, pose_desc, filename_prefix):
    filename = f"{frame_num:02d}_{filename_prefix}.png"
    
    style_prompt = "cinematic 35mm film aesthetic, raw texture, realistic lighting, dramatic shadows, 1980s-90s retro Korean atmosphere, high detail, photorealistic"

    payload = {
        "prompt": f"{pose_desc}, {style_prompt}",
        "negative_prompt": "doll face, plastic surgery, glamorous fit body, voluptuous, airbrushed, 3d, cg, naked, split frame, multiple panels, text, watermarks, low quality, blurry",
        "steps": 6,
        "width": 720,
        "height": 1280,
        "seed": -1,
        "model": "z_image_turbo_1.0_q8p.ckpt",
        "guidance_scale": 1.0,
        "sampler": "Euler A AYS",
        "shift": 3.0,
        "sharpness": 6,
        "seed_mode": "Scale Alike"
    }

    try:
        response = requests.post(f"{DRAW_THINGS_URL}/sdapi/v1/txt2img", json=payload, timeout=600)
        if response.status_code == 200:
            data = response.json()
            if "images" in data:
                filepath = os.path.join(DOWNLOADS_DIR, filename)
                with open(filepath, "wb") as f:
                    f.write(base64.b64decode(data["images"][0]))
                print(f"  ✅ [{frame_num:02d}/48] {filename_prefix} 저장 완료!")
                return True
        print(f"  ❌ [{frame_num:02d}/48] 실패: {response.status_code}")
    except Exception as e:
        print(f"  ❌ 드로띵 연결 오류: {e}")
    return False

if __name__ == "__main__":
    check_and_start_draw_things()

    # 등장인물 기본 속성 설정
    mj = "A 49-year-old Korean woman, Park Myung-ja. Initially a tired housewife with a gentle but weary face and faded clothes. Later, she has a neat short bob and sharp, professional office wear."
    ks = "A 50s Korean man, Lee Kang-su, construction company manager. Slicked-back black hair, expensive 1980s-90s style suit, arrogant and cold expression."

    FRAMES = [
        # Phase 1: Domestic Life & Trust
        (f"A realistic photo of {mj} ironing a crisp white dress shirt on a wooden board, steam rising in soft morning light", "01_Ironing_Morning"),
        (f"Close up of {mj}'s hands carefully pressing the collar of a dark grey suit jacket, meticulous attitude", "02_Suit_Pressing"),
        (f"{mj} standing in a small 1990s Korean kitchen, steam rising from a stone pot, preparing traditional breakfast", "03_Kitchen_Breakfast"),
        (f"{ks} sitting at dining table, reading newspaper and ignoring {mj}, looking arrogant in expensive pajamas", "04_Indifferent_Husband"),
        (f"{mj} handing a leather briefcase to {ks} at the front door, {ks} looking away impatiently", "05_Front_Door_Departure"),
        (f"A static photo of an old Korean bankbook on a dark wooden dresser, slightly dusty, symbolizing forgotten trust", "06_Joint_Bankbook"),
        (f"{mj} looking at a framed family photo on the wall, nostalgic look in eyes, soft warm interior lighting", "07_Family_Photo"),
        (f"{mj} watching {ks} walk towards a black 1990s sedan from the porch, cold mist in the morning air", "08_Husband_Leaving"),

        # Phase 2: The Shocking Discovery
        (f"{mj} standing at a 1990s bank counter, holding a son's college tuition bill, looking anxious", "09_Bank_Counter"),
        (f"Close up of a bank teller's face behind glass, looking at computer screen with a concerned frown", "10_Serious_Teller"),
        (f"An ATM screen showing red '잔액부족' Korean message, harsh digital glow on {mj}'s shocked face", "11_Insufficient_Balance"),
        (f"A portrait of {mj} in the bank lobby, frozen in shock, background people blurred into bokeh", "12_MJ_Shocked"),
        (f"A dot-matrix bank printer rapidly printing out pages of transaction history, mechanical noise", "13_Printing_History"),
        (f"{mj} sitting on a plastic bank bench, staring blankly at a thick stack of papers in lap", "14_Bank_Bench"),
        (f"Close up of bank statement showing recurring 1.5 million won transfers, red pen circling numbers", "15_Statement_CloseUp"),
        (f"{mj} walking home alone on a busy city street, holding her bag tightly, looking small and devastated", "16_Walk_In_Rain"),

        # Phase 3: Silent Investigation
        (f"{mj} sitting alone at a dimly lit dining table, a single bowl of rice, shadows deepening in house", "17_Solitary_Dinner"),
        (f"{mj}'s hand reaching into inner pocket of {ks}'s suit jacket hanging on a chair, moonlight through window", "18_Pocket_Search"),
        (f"Close up of receipt for an expensive French restaurant found in the pocket, dated late evening", "19_Restaurant_Receipt"),
        (f"{mj} taking a photo of a jewelry shop receipt using a compact 90s camera, focused and silent", "20_Secret_Photo"),
        (f"{mj} searching dashboard of a sedan at night, finding a perfume-scented card from a florist", "21_Car_Dashboard"),
        (f"{mj} hiding a bundle of receipts in a secret compartment of a traditional wooden jewelry box", "22_Evidence_Box"),
        (f"{mj} watching {ks} from dark kitchen as he laughs while talking on a phone in silhouette", "23_Secret_Phone_Call"),
        (f"Close up of {mj}'s face in the dark, her eyes sharp and freezing with resolve", "24_Cold_Determination"),

        # Phase 4: Skills & Preparation
        (f"{mj} sitting in front of a bulky beige CRT monitor in a dark room, blue light on her determined face", "25_Computer_Glow"),
        (f"Computer screen showing YouTube interface with video 'Excel for Bookkeeping' in Korean", "26_Excel_Tutorial"),
        (f"{mj}'s fingers firmly pressing keys on a mechanical keyboard, a stack of receipts nearby", "27_Typing_Practice"),
        (f"Close up of Excel grid on monitor, organized rows of dates and '54,000,000 won' total", "28_Excel_Spreadsheet"),
        (f"{mj} looking between a receipt and the screen, face concentrated, glasses reflecting the grid", "29_Data_Entry"),
        (f"A graph on the screen showing the monthly drain of savings, revealing the scale of {ks}'s betrayal", "30_Calculated_Greed"),
        (f"A printer outputting a neatly organized binder of evidence, {mj}'s hand catching the warm paper", "31_Binder_Printing"),
        (f"{mj} looking at mirror, cutting her hair into a neat short bob, looking refreshed and strong", "32_New_Self_Mirror"),

        # Phase 5: Confrontation & Trial
        (f"{ks} sitting on sofa, throwing tie aside, saying 'Let's end this' with arrogant and tired look", "33_Divorce_Demand"),
        (f"{mj} standing in front of {ks}, looking down with expression of calm indifference, arms crossed", "34_MJ_Ready"),
        (f"{ks}'s expensive lawyer looking smug opening a thin folder in a mediation room", "35_Opposing_Lawyer"),
        (f"{mj} sitting alone across from them, placing her thick professionally bound binder on the table", "36_MJ_Presentation"),
        (f"A low angle shot of a judge in robes, looking through {mj}'s organized evidence with surprise", "37_Courtroom_Judge"),
        (f"{mj} pointing at a photo of a receipt in her binder, {ks} looks on with growing horror", "38_Evidence_Reveal"),
        (f"Close up of {ks}'s face turning pale and sweaty as his lawyer looks at him with frustration", "39_Husband_Collapse"),
        (f"A dramatic shot of a wooden gavel slamming down on the judge's bench, final victory", "40_Gavel_Slam"),

        # Phase 6: New Beginning
        (f"{mj} walking out of a grand courthouse building, bright afternoon sun on her confident smile", "41_Victory_Sunlight"),
        (f"Wide shot of a bright empty apartment living room with {mj} standing in center, looking at new beginning", "42_New_Home_Sun"),
        (f"{mj} standing at a shelf in stationery store, reaching for a premium leather ledger book", "43_Stationery_Store"),
        (f"Close up of {mj} writing 'Today is the first day' in her new ledger with a fountain pen", "44_First_Entry"),
        (f"{mj} standing in front of a glass door with 'Bookkeeper Wanted' sign, looking professional", "45_Hiring_Sign"),
        (f"{mj} sitting for a job interview, smiling warmly and confidently at an older tax accountant", "46_Interview_Smile"),
        (f"{mj} sitting at a new desk in a quiet office, typing on computer, face filled with peace", "47_New_Desk"),
        (f"{mj} standing on a rooftop at sunset, looking out at the city skyline, silhouette of freedom", "48_End_Horizon")
    ]

    print(f"🎬 '48개 풀 프레임 연속 스토리보드 (박명자 편)' 생성을 시작하겠습니다.")
    
    for i, (pose_desc, prefix) in enumerate(FRAMES):
        generate_frame(i + 1, pose_desc, prefix)
        time.sleep(1)

    print(f"\n✨ [생성 완료] 48개 연속 프레임 렌더링 끝!")
    print(f"📍 저장 위치: {DOWNLOADS_DIR}")
    os.system(f"open {DOWNLOADS_DIR}")

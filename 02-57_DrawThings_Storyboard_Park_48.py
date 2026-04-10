import json
import requests
import time
import os
import base64

# [설정]
DRAW_THINGS_URL = "http://127.0.0.1:7860" 
TIMESTAMP = time.strftime('%m%d_%H%M')
DOWNLOADS_DIR = f"/Users/a12/Downloads/Frames_Park_Storyboard_{TIMESTAMP}"

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
    
    style_prompt = "cinematic raw photography captures, photorealistic lighting setups, detailed surrounding atmosphere, 1980s retro aesthetics, raw texture"

    payload = {
        "prompt": f"{pose_desc}, {style_prompt}",
        "negative_prompt": "doll face, plastic surgery, glamorous fit body, voluptuous, airbrushed, 3d, cg, naked, split frame, multiple panels, text, watermarks",
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
    jaedal = "A realistic photo of a 50s Korean man, heavy build, oily slicked-back hair, greedy and arrogant facial expression, wearing an expensive 1980s retro suit with a shiny silk tie"
    inspector = "A realistic photo of a sharp 40s Korean man, clean-cut short hair, wearing a 1980s trench coat, keen and intimidating gaze"
    villager = "An old 60s Korean farmer with dry wrinkled skin wearing faded traditional work-clothes, looking exhausted and angry"

    FRAMES = [
        # 1-8: 기승전결 (기) - 부패의 시작과 권력형 탐욕
        (f"A cinematic high angle view of 1980s remote Korean mountain village, dry and cracked soil terrain", "01_Village_Overview"),
        (f"A portrait of {jaedal} secretly giving a bulk brown envelope of money to a man inside dark smoking lounge", "02_Bribe_Secret"),
        (f"{jaedal} standing sizing up a 1980s wooden desk office room inside government building office", "03_Office_Arrive"),
        (f"{jaedal} leaning back inside heavy office sofa holding cigarette with arrogant greedy look, rich interiors", "04_Posh_Greed"),
        (f"{jaedal} seated comfortably in high-backed leather chair, side lighting on greed shadow", "05_Arrogant_Pose"),
        (f"Close up of two men doing handshake dealing over a sealed folder mockup inside meeting room", "06_Deal_Folder"),
        (f"A photo of expensive 1980s office frame setting laden with accessories, antique gold desk weight props", "07_Posh_Accessories"),
        (f"{jaedal} smiling standing and inspecting himself inside a mirror frame adjusting silk tie proudly", "08_Mirror_Inspect"),

        # 9-16: 기승전결 (승) - 수탈과 군민의 고통
        (f"A photo of 60s Korean farmers standing on dried cracked rice paddy fields looking desperate top light", "09_Drought_Distress"),
        (f"{jaedal} shouting pointing finger demanding to employees inside 1980s layout meeting workspace", "10_Harsh_Demands"),
        (f"A close up photo of brown payment notices containing red circular stamp printed paper is glued rigidly on wooden doors", "11_Tax_Sticker"),
        (f"An older {villager} weeping sitting at home humble table holding grey head in dark indoor light", "12_Elderly_Distress"),
        (f"An electric wire hanging loose from a simple pole beside traditional village cottage dusk sun backlight", "13_Electricity_Cut"),
        (f"{villager} kneeling holding hands up begging before {jaedal} office desk chair, ignoring cold expression", "14_Begging_Farmer"),
        (f"A top view of static ledger finance booklet containing numerical values getting stamped rapidly with red seal inks", "15_Ledger_Stamping"),
        (f"{jaedal} laughing together with assistants raising glass drinks inside indoor workspace party vibes", "16_Greedy_Drinking"),

        # 17-24: 기승전결 (승➡전) - 함정 및 미끼
        (f"A 1980s night street row loading passing black sedan cars containing round headlights glowing", "17_Night_Sedans"),
        (f"A static photo of {inspector} entering inside a vintage dark mahogany clouded smoking hotel lounge setting", "18_Inspector_Entry"),
        (f"{inspector} sitting facing across {jaedal} inside dimmed cloudy layout smoking room booth", "19_Inspector_Meeting"),
        (f"{inspector} whispering to {jaedal} containing a gold bar mockup presentation sitting across dining table", "20_Whisper_Deal"),
        (f"A portrait of {inspector} staring with sharp intimidating cold gaze indoors cloudy lighting setups", "21_Inspector_Gaze"),
        (f"{jaedal} clapping hands excited clapping inside clouded smoking room seating greedy grin face", "22_Jaedal_Excited"),
        (f"Close up on {jaedal} signing agricultural funds paper with gold pen framing inside mahogany table", "23_Secret_Signing"),
        (f"{jaedal} counting bundle packages inside black open briefcase loading money papers focused attitude", "24_Counting_Money"),

        # 25-32: 기승전결 (전) - 반전 전야와 출두
        (f"Close up of document Clearance stamp is pushed rapid on printed file documents desk spotlight setup", "25_Clearance_Seal"),
        (f"{jaedal} counting calculating values calculator adding math rapidly tensed desk office space focus", "26_Speed_Account"),
        (f"{inspector} silent standing shadow framing side position inside door frame staring Jaedal desk corner view", "27_Watching_Jaedal"),
        (f"An exterior overview structure photo of 1980s Korean government headquarters building sunrise dawn sky", "28_HQ_Building"),
        (f"A top down approach of 3 black sedan cars parking harsh inside government headquarters gravel yard paving", "29_Arriving_Sedans"),
        (f"An indoor car set up of {inspector} grabbing metallic silver handcuffs out of leather pockets up close", "30_Clicking_Handcuffs"),
        (f"{jaedal} looking bright admiring himself adjusting silk necktie in framed mirror setup smiling proud", "31_Tie_Fixing"),
        (f"A static reflection of {jaedal} smiling happily proud thinking inside framed mirror spotlight", "32_Mirror_Reflection"),

        # 33-40: 기승전결 (전➡결) - 체포와 몰락
        (f"An indoor door frame burst open as armed 1980s police officers rushing inside desk office workplace setup", "33_Door_Burst"),
        (f"{jaedal} holding document with total shocked facial features standing besides mahogany desk freezing look", "34_Shocked_Jaedal"),
        (f"{inspector} revealing presenting shiny metal police badge emblem to {jaedal} head set up focused look", "35_Revealing_Badge"),
        (f"{inspector} holding highly detailed metallic silver handcuffs pointing forwards down towards desk spotlight", "36_Holding_Handcuffs"),
        (f"Close up on locking metallic handcuffs onto wrists of bundle suit jacket up close dramatic lighting", "37_Handcuff_Clicking"),
        (f"{jaedal} falling to knees screaming face inside desk office carpet flooring weeping screaming despair", "38_Jaedal_Falling"),
        (f"A static photo of office workers following with shock gasping postures isolated holding head defocus setting", "39_Workers_Shock"),
        (f"{jaedal} being dragged down long corridor flooring crying posture handcuffs attached on floor lighting", "40_Dragged_Out"),

        # 41-48: 기승전결 (결) - 여운과 교훈 피날레
        (f"An open dark steel vault safe frame leaving shelves empty with zero goods inside static vault room", "41_Empty_Safe"),
        (f"A single golden mock cube representation left behind alone placed mahogany desk top corner layout", "42_Fake_Gold"),
        (f"A photo of empty office chair left behind backlight office window desk layout loneliness ambient air", "43_Empty_Chair"),
        (f"A group of 60s Korean {villager}s gathered corridor outside smiling proudly laughing together side lighting", "44_Villagers_Laughing"),
        (f"Silhouette approach of {villager}s overlooking sunset mountain village horizon sky high dynamic setting", "45_Horizon_Silhouette"),
        (f"A cinematic high depth photo of parched earth soil receiving raindrops up close macro focus depth", "46_Raindrops_Falling"),
        (f"An older {villager} making calm respectful nod locking into viewers smiling proud far away background", "47_Villager_Nod"),
        (f"Silhouette approach of sunlight peaks behind village forest trees cinematic ending dramatic framing sunset", "48_Happy_Ending")
    ]

    print("🎬 '48개 풀 프레임 연속 스토리보드 (박재달 부군수편)' 생성을 시작하겠습니다.")
    
    for i, (pose_desc, prefix) in enumerate(FRAMES):
        generate_frame(i + 1, pose_desc, prefix)
        time.sleep(1)

    print(f"\n✨ [생성 완료] 48개 연속 프레임 렌더링 끝!")
    print(f"📍 저장 위치: {DOWNLOADS_DIR}")
    os.system(f"open {DOWNLOADS_DIR}")

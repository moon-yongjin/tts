import json
import requests
import time
import os
import base64

# [설정]
DRAW_THINGS_URL = "http://127.0.0.1:7860" 
TIMESTAMP = time.strftime('%m%d_%H%M')
DOWNLOADS_DIR = f"/Users/a12/Downloads/Frames_48_Storyboard_{TIMESTAMP}"

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
    
    style_prompt = "cinematic raw photography captures, photorealistic lighting setups, detailed surrounding atmosphere, raw texture"

    payload = {
        "prompt": f"{pose_desc}, {style_prompt}",
        "negative_prompt": "doll face, plastic surgery, glamorous fit body, voluptuous, airbrushed, mature, old aged, 3d, cg, naked, split frame, multiple panels, text, watermarks",
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

    # 은숙 캐릭터 기본 속성 
    eunsook = "A realistic photo of a late 40s Korean woman with smooth skin and short bob haircut, wearing modest casual clothes"

    # [48개 스토리 프레임 분할 - 시네마틱 환경 및 다중 인원 연출 완전 탑재]
    FRAMES = [
        # 1-8: 헌신과 고단한 일상
        (f"A portrait of {eunsook} with tired respectful face, clean standing inside home domestic hallway", "01_Eunsook_Intro"),
        (f"{eunsook} preparing medicine pills at 5 AM inside home dark kitchen, backlight shining through steam from boiling kettle", "02_Morning_Pills"),
        (f"{eunsook} packing a stainless steel lunchbox inside home kitchen domestic setting, early morning sun scattering", "03_Lunchbox_Packing"),
        (f"{eunsook} ironing children's school uniform on boards, smooth iron with steam rises, household chores props", "04_Ironing_Uniform"),
        (f"{eunsook} collapsing slightly on a wooden stool standing alone inside kitchen corner, exhausted air", "05_Exhausted_Vibe"),
        (f"{eunsook} carefully aiding a 70s Korean grandmother resting on a bed, caregiving scene, warm nightstand lamp light", "06_Caring_Dementia"),
        (f"{eunsook} cooking large amount of festive foods inside kitchen laden with dishes plates, lonely posture", "07_Holiday_Cooking"),
        (f"A portrait of {eunsook} looking silently obedient and composed inside domestic surroundings, quiet atmosphere", "08_Devotion_Silence"),

        # 9-16: 이혼과 배신
        (f"A 50s Korean man loosening necktie with cold expression inside hallway standing near door", "09_Husband_Coming"),
        (f"A 50s Korean man looking straight with cold facial features inside dimly lit dining room posture speaking", "10_Demanding_Divorce"),
        (f"{eunsook} shocked face Holding a teacup sitting at table, holding dramatic side shadow lighting", "11_Shocked_Divorce"),
        (f"{eunsook} weeping softly covering eyes in dark domestic living room lighting, dramatic despair air", "12_Despair_Moment"),
        (f"A static photo of another 50s Korean woman high makeup curled hair standing holding hands with {eunsook} sitting inside a sofa", "13_Friend_Visiting"),
        (f"A static photo of two women inside a law firm office meeting room sitting facing an office worker table props", "14_Lawyers_Office"),
        (f"{eunsook} holding pen inside legal meeting room signage quietly signing paper contract contract forms", "15_Signing_Deals"),
        (f"{eunsook} examining final terms reading folder inside law room, shocked and weeping air", "16_Terms_Realization"),

        # 17-24: 8평 원룸과 가계부
        (f"A 50s Korean man and a makeup curled hair 50s woman standing together smiling together inside hallway secretly", "17_Betrayal_Secret"),
        (f"{eunsook} sobbing heavily alone on dusty floor corner inside room, windows backlight passing through air particles", "18_Sobbing_Despair"),
        (f"A indoor photo of a small 26 square meter humble quiet domestic studio room loaded with some package boxes", "19_Moving_Studio"),
        (f"{eunsook} sitting isolating inside humble quiet studio room looking lonely on windows backlight desk", "20_Isolated_Eunsook"),
        (f"{eunsook} touching older budget domestic finance ledger calculation booklet on a wooden desk table with index", "21_Ledger_Found"),
        (f"{eunsook} wearing reading glasses analyzing meticulous math numbers sheets calculation papers ledger focused attitude", "22_Detailed_Numbers"),
        (f"{eunsook} touching her face inside studio on desk, touching hands on table thinking inside humble desk space", "23_Thinking_Purpose"),
        (f"An older 70s neighbor grandmother knocking a small doorway with accurate rough wooden frame threshold smiling", "24_Granny_Knocking"),

        # 25-32: 반찬가게 오픈
        (f"An older 70s neighbor grandmother giving received plate of kimchi up close standing inside apartment corridor", "25_Kimchi_Request"),
        (f"{eunsook} surprised face standing on doorstep seeing neighbor warm grandmother holding a dish item", "26_Hopeful_Waking"),
        (f"A high quality aesthetic background template layout related to food market alley with smooth blurred crowd defocus", "27_Placeholder_Template"),
        (f"A photo of a 33 square meter small traditional market booth shop stall frame with rough weathered steel gates", "28_Market_Booth"),
        (f"{eunsook} setting small transparent transparent plastic packs loaded with side dishes inside market stall", "29_Making_SideDishes"),
        (f"A photo of marketplace crowd pedestrians gathered around a neat booth full of food looking interested defocus", "30_Pedestrians_Gathering"),
        (f"{eunsook} smiling cheerfully inside market stall crowded full of customer shoppers defocus side light", "31_Market_Popular"),
        (f"{eunsook} hanging a clean elegant wooden banner written Haneunsook Banchan signage above traditional store frame", "32_Banner_Hanging"),

        # 33-40: 아들의 방문과 현우
        (f"A fit young 28 year old Korean man standing inside markets entry with red crying eyes looking for someone", "33_Son_Visiting"),
        (f"A young 28 year old Korean man crying hand on face apologetic bowing bending waist sitting inside small shop", "34_Son_Crying_Bowing"),
        (f"{eunsook} patting holding hands with a young 28 year old man crying face, emotional support in shop floor", "35_Son_Consoling"),
        (f"A quiet 50s man in neat knitted sweater carrying a heavy transparent kimchi container inside market shop", "36_Hyunwoo_Caring"),
        (f"A quiet 50s man with reading glasses assist carrying heavy loads down a rough damp asphalt paved food alleyway", "37_Hyunwoo_Walking"),
        (f"A quiet 50s man and {eunsook} reviewing finance calculation ledger together on a small wooden counter spotlight", "38_Ledger_Question"),
        (f"A quiet 50s man with warmhearted expression holding glasses speaking inside marketplace shopfront stall ambient", "39_Questioning_Numbers"),
        (f"{eunsook} touched tears forming on corners weeping quietly forming inside marketplace shop corner desk layout", "40_Touched_Tears"),

        # 41-48: 복수와 해피엔딩
        (f"{eunsook} focused sitting analysis corporate financial sheets calculating numbers inside desk spotlight accurately", "41_Revenge_Analysis"),
        (f"A close up photo of transparent plastic credit cards receipts laid on a mahogany office desk frame", "42_Credit_Evidence"),
        (f"{eunsook} packing corporate tax reporting transparent envelopes standing beside a small desk intelligent design", "43_Evidence_Prep"),
        (f"A 50s Korean man looking down with exhausted collapsed posture sitting inside rough tensed office spaces", "44_Husband_Ruin"),
        (f"A makeup 50s Korean woman packing bags with urgent expression leaving inside hallway room door open", "45_Friend_Escape"),
        (f"{eunsook} touched feelings indoors cozy bookstore cafe across a kind 50s man with warm beverages gold sun scatter", "46_Warm_Conversation"),
        (f"A realistic photo of {eunsook} smiling bright holding hands with kind 50s man down damp paved market alley sunset", "47_Couple_Walking"),
        (f"{eunsook} standing proudly behind marketplace banner stall frame smiling brightly realistic life begins framing", "48_Happy_Ending")
    ]

    print("🎬 '48개 풀 프레임 연속 스토리보드' 생성을 시작하겠습니다.")
    
    for i, (pose_desc, prefix) in enumerate(FRAMES):
        generate_frame(i + 1, pose_desc, prefix)
        time.sleep(1)

    print(f"\n✨ [생성 완료] 48개 연속 프레임 렌더링 끝!")
    print(f"📍 저장 위치: {DOWNLOADS_DIR}")
    os.system(f"open {DOWNLOADS_DIR}")

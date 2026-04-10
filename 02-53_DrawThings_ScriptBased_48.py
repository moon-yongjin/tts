import json
import requests
import time
import os
import base64

# [설정]
DRAW_THINGS_URL = "http://127.0.0.1:7860" 
TIMESTAMP = time.strftime('%m%d_%H%M')
DOWNLOADS_DIR = f"/Users/a12/Downloads/ScriptBased_48_{TIMESTAMP}"

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

def generate_scene_storyboard(scene_num, variant_id, pose_desc, filename_prefix):
    filename = f"{filename_prefix}_Scene{scene_num:02d}_Var{variant_id}.png"
    
    # [동안보정 보존] 40대 후반 깨끗한 피부 + 과도한 피트니스나 글래머 세팅 배제한 평범한 형태
    base_prompt = "A high-quality realistic photo of a normal ordinary late 40s Korean woman looking youthful for age, sleek smooth skin with modest graceful face, standard clean short bob haircut, normal body proportion, wearing neat modest clean casual daily clothes"
    
    style_prompt = "candid raw photography captures, cinematic lighting setups, photorealistic style, ordinary daily life ambience"

    payload = {
        "prompt": f"{base_prompt}, {pose_desc}, {style_prompt}",
        "negative_prompt": "doll face, plastic surgery, glamorous fit body, voluptuous bust, airbrushed, mature, old aged, grandma, 3d, cg, naked, blur",
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
    
    # 각도 및 표현 배리에이션 미세 조정
    if variant_id == 2:
        payload["prompt"] += ", sitting posture angle view"
    elif variant_id == 3:
        payload["prompt"] += ", candid head shoulder angle view"

    try:
        response = requests.post(f"{DRAW_THINGS_URL}/sdapi/v1/txt2img", json=payload, timeout=600)
        if response.status_code == 200:
            data = response.json()
            if "images" in data:
                filepath = os.path.join(DOWNLOADS_DIR, filename)
                with open(filepath, "wb") as f:
                    f.write(base64.b64decode(data["images"][0]))
                print(f"  ✅ [{scene_num:02d}-{variant_id}] {filename_prefix} 저장 완료!")
                return True
        print(f"  ❌ [{scene_num:02d}-{variant_id}] 실패: {response.status_code}")
    except Exception as e:
        print(f"  ❌ 드로띵 연결 오류: {e}")
    return False

if __name__ == "__main__":
    check_and_start_draw_things()

    # 단축 대본 기반 16개 주요 씬 (장면당 3장 생성 ➡ 총 48장)
    SCENES = [
        ("wearing a humble kitchen apron, preparing medicine pills and packing a packed lunch at 5 AM inside home kitchen, tired face", "01_Mornings_Hardwork"),
        ("carefully aiding an elderly grandmother sitting on bed in bedroom, assisting posture, warm but exhausted look", "02_Caring_Grandmother"),
        ("sitting at a dining table, looking at a cold expression man in 50s, shocked face holding a teacup, divorce request", "03_With_Cold_Husband"),
        ("sitting at office desk, holding a pen inside legal office meeting room, signing divorce papers quietly", "04_Signing_Papers"),
        ("weeping single woman indoors sitting in a corner, realization of betrayal and shock", "05_Shock_Truth"),
        ("sitting inside a small 26-square-meter humble studio room, isolated, lonely gaze sitting on desk", "06_Isolated_Studio"),
        ("sitting and meticulously examining a domestic finance calculation ledger booklet, focused look with reading glasses", "07_Ledger_Accounting"),
        ("standing in a humble apartment doorway, looking very surprised with Brightened eyes seeing an old neighbor grandmother giving kimchi plate", "08_Granny_Visiting"),
        ("hanging a clean neat wooden banner written Haneunsook Banchan shopfront above a traditional food market stall", "09_Store_Opening"),
        ("standing proudly in top of market booth corner loaded with various packed side dishes, looking very happy with gentle smile", "10_Success_Moment"),
        ("crying and patting holding hands with a young man in his late 20s crying face, emotional support", "11_Son_Apology"),
        ("standing next to a quiet middle-aged man in neat sweater carrying a heavy plate inside marketplace bookstore, warm air", "12_Bookstore_Helper"),
        ("standing listening warmhearted gaze, looking touched inside a warm library cafe holding simple mug", "13_Touched_Feelings"),
        ("focused sitting analysis accurate financial ledgers, corporate secret papers, intelligent desk lighting", "14_Evidence_Revenge"),
        ("standing elegantly in professional business room tall posing with folder, looking victorious while counting something", "15_Victorious_Ruin"),
        ("smiling very brightly happy expression, holding hands with kind-hearted spectacles man, quiet bookstore street afternoon sunset", "16_Happy_Ending")
    ]

    print("🎬 '단축 대본 기반 16개 씬 x 3장 배리에이션 = 총 48장' 연쇄 생성을 시작합니다.")
    
    count = 1
    for i, (pose_desc, prefix) in enumerate(SCENES):
        for var_id in range(1, 4):  # 1, 2, 3회 배리에이션 
            generate_scene_storyboard(i + 1, var_id, pose_desc, prefix)
            time.sleep(1)
            count += 1

    print(f"\n✨ [생성 완료] 총 48장 극본 맞춤형 렌더링 끝!")
    print(f"📍 저장 위치: {DOWNLOADS_DIR}")
    os.system(f"open {DOWNLOADS_DIR}")

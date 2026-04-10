import json
import requests
import time
import os
import base64

# [설정]
DRAW_THINGS_URL = "http://127.0.0.1:7860" 
TIMESTAMP = time.strftime('%m%d_%H%M')
DOWNLOADS_DIR = f"/Users/a12/Downloads/ScriptBased_Multi_{TIMESTAMP}"

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
    
    # [다중 인물 지원을 위해 base_prompt를 더 유연하게 조정]
    # 이전의 단독 인물 고정 태그를 빼고, pose_desc 내부에 은숙+타배우 묘사를 주도권 부여
    
    style_prompt = "candid raw photography captures, cinematic lighting setups, photorealistic style, ordinary daily life ambience"

    payload = {
        "prompt": f"{pose_desc}, {style_prompt}",
        "negative_prompt": "doll face, plastic surgery, glamorous fit body, voluptuous, airbrushed, mature, old aged, 3d, cg, naked, blur, split frame, multiple panels",
        "steps": 6,
        "width": 576,  # 720 * 0.8 = 576
        "height": 1024, # 1280 * 0.8 = 1024
        "seed": -1,
        "model": "z_image_turbo_1.0_q8p.ckpt",
        "guidance_scale": 1.0,
        "sampler": "Euler A AYS",
        "shift": 3.0,
        "sharpness": 6,
        "seed_mode": "Scale Alike"
    }
    
    # 배리에이션 거리감 조절
    if variant_id == 2:
        payload["prompt"] += ", sitting angle view"
    elif variant_id == 3:
        payload["prompt"] += ", close shot angle view"

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

    # 단축 대본 기반 16개 주요 씬 (다중 배우 연출 반영)
    SCENES = [
        # 1. 헌신 (주방 단독)
        ("A realistic photo of a late 40s Korean woman with smooth skin and short bob haircut, wearing a humble kitchen apron, preparing medicine pills at 5 AM inside home kitchen, tired face", "01_Mornings_Hardwork"),
        
        # 2. 시어머니 수발 (2인)
        ("A realistic full body photo of a late 40s Korean woman with short bob haircut carefully aiding a 70s Korean grandmother who is resting on a bed in bedroom, caregiving scene", "02_Caring_Grandmother"),
        
        # 3. 이혼 통보 (2인)
        ("A realistic photo of a late 40s Korean woman shocked face weeping, sitting across a dining table from a 50s Korean man who has a cold expression, divorce request conversation", "03_With_Cold_Husband"),
        
        # 4. 도장 찍음 (법률 오피스 배경)
        ("A late 40s Korean woman sitting inside legal office meeting room and holding a pen, signs a white sheet of paper quietly with sad face", "04_Signing_Papers"),
        
        # 5. 배신의 진실 (단독 절망)
        ("A photo of a late 40s Korean woman weeping alone indoors sitting on floor corner, overwhelmed with shock of betrayal", "05_Shock_Truth"),
        
        # 6. 골방 (단독 고독)
        ("A photo of a late 40s Korean woman sitting inside a small domestic studio room, isolated, lonely gaze sitting near desk", "06_Isolated_Studio"),
        
        # 7. 가계부 (단독 집중)
        ("A late 40s Korean woman with sleek skin sitting on chair mat, meticulously examining calculation ledger booklet, holding eyeglasses", "07_Ledger_Accounting"),
        
        # 8. 할머니 방문 (2인)
        ("A photo of a late 40s Korean woman standing in a doorway surprised face, holding received plate of kimchi from a kind-hearted 70s Korean grandmother with smiling attitude", "08_Granny_Visiting"),
        
        # 9. 간판 (단독 희망)
        ("A late 40s Korean woman hanging a clean neat wooden banner written Haneunsook Banchan at marketplace food stall storefront facade", "09_Store_Opening"),
        
        # 10. 소문 (2인 혹은 시장 풍경)
        ("A late 40s Korean woman standing proudly behind dynamic market booth full of various packed side dish plates, smiling happy face giving products to customer", "10_Success_Moment"),
        
        # 11. 아들 사죄 (2인)
        ("A realistic photo of a late 40s Korean woman holding hands with a young 28-year-old Korean man who is crying and bowing in apology, indoor backdrops", "11_Son_Apology"),
        
        # 12. 현우의 도움 (2인)
        ("A quiet 50s Korean man with neat clothes assisting a late 40s Korean woman inside a traditional bookstore facade marketplace, carrying heavy containers together", "12_Bookstore_Helper"),
        
        # 13. 위로 (2인)
        ("A late 40s Korean woman touched feeling indoor cafe together with a kind-hearted 50s Korean man with reading glasses across table, warm drinks", "13_Touched_Feelings"),
        
        # 14. 복수 장부 (단독 분석)
        ("A late 40s Korean woman focused sitting analysis corporate financial sheets, calculating accounting numbers on elegant desk spotlight", "14_Evidence_Revenge"),
        
        # 15. 승리 (회사 단독)
        ("A late 40s Korean woman standing in bright workspace holding a reports folder, looking victorious but calm posture", "15_Victorious_Ruin"),
        
        # 16. 해피엔딩 (2인)
        ("A realistic photo of a late 40s Korean woman smiling bright, holding hands with a kind 50s Korean man wearing reading spectacles, walking down bookstore alleyway in sunset golden hour", "16_Happy_Ending")
    ]

    print("🎬 '다중 배우(상황 연출) 반영 + 사이즈 20% 축소(576x1024) 48장' 생성을 시작하겠습니다.")
    
    count = 1
    for i, (pose_desc, prefix) in enumerate(SCENES):
        for var_id in range(1, 4):  # 1, 2, 3회 배리에이션 
            generate_scene_storyboard(i + 1, var_id, pose_desc, prefix)
            time.sleep(1)
            count += 1

    print(f"\n✨ [생성 완료] 다중 조연 매칭 48장 렌더링 끝!")
    print(f"📍 저장 위치: {DOWNLOADS_DIR}")
    os.system(f"open {DOWNLOADS_DIR}")

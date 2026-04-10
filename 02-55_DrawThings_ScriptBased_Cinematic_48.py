import json
import requests
import time
import os
import base64

# [설정]
DRAW_THINGS_URL = "http://127.0.0.1:7860" 
TIMESTAMP = time.strftime('%m%d_%H%M')
DOWNLOADS_DIR = f"/Users/a12/Downloads/ScriptBased_Cinematic_{TIMESTAMP}"

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
    
    style_prompt = "cinematic raw photography captures, 8k resolution, authentic lighting setups, realistic textures, detailed surrounding atmosphere"

    payload = {
        "prompt": f"{pose_desc}, {style_prompt}",
        "negative_prompt": "doll face, plastic surgery, glamorous fit body, voluptuous, airbrushed, mature, old aged, 3d, cg, naked, blur, split frame, multiple panels, low quality",
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
    
    # 배리에이션 거리감 조절
    if variant_id == 2:
        payload["prompt"] += ", sitting angle view"
    elif variant_id == 3:
        payload["prompt"] += ", close up head angle shot"

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

    # 등장 인물 캐스팅 기본형 (극본 톤 유지)
    eunsook = "A realistic photo of a late 40s Korean woman with smooth skin and short bob haircut, wearing modest casual clothes"

    # [환경 묘사 집요하게 추가] 빛과 공기, 질감, 생동감 가중치 배가
    SCENES = [
        # 1. 헌신
        (f"{eunsook} wearing a humble kitchen apron on a wet tile-sink floor, preparing medicine pills at 5 AM inside home dark kitchen, backlight shining through steam from boiling kettle, dust particles floating in light shaft, ambient silence", "01_Mornings_Hardwork"),
        
        # 2. 시어머니 수발
        (f"{eunsook} with graceful look carefully aiding a 70s Korean grandmother resting on a bed, caregiving scene, warm side-light from a nightstand lamp scattering in thick air, soft fabric mattress textures, silence", "02_Caring_Grandmother"),
        
        # 3. 이혼 통보
        (f"{eunsook} weeping sitting across a rough textured wooden dining table from a 50s Korean man, heavy dramatic side lighting creating shadows, dust cone overhead, half-empty coffee mug reflective highlights, cold tensed air", "03_With_Cold_Husband"),
        
        # 4. 도장 찍음
        (f"{eunsook} sitting inside a sterile legal office meeting room and holding a pen, overhead blueish cinematic fluorescence casting cold light on polished wooden table reflections, neat folder papers piled, quiet air", "04_Signing_Papers"),
        
        # 5. 배신의 진실
        (f"{eunsook} weeping alone on a dusty floor corner indoors, weak window backlight passing through dense air particles, peeling rough wallpaper texture, overwhelmed lonely air", "05_Shock_Truth"),
        
        # 6. 골방
        (f"{eunsook} sitting inside a small domestic studio room, dusty air filled, fading orange sunset light leaking through cracked venetian blinds, old desk props, solitary absolute silence", "06_Isolated_Studio"),
        
        # 7. 가계부
        (f"{eunsook} sitting examining a calculation ledger booklet with reading glasses, warm incandescent desk lamp scattering light shaft in humid air, stacked papers and accurate props on table, focused mood", "07_Ledger_Accounting"),
        
        # 8. 할머니 방문
        (f"{eunsook} standing in a rough weathered wooden doorway threshold showing surprised face, receiving plate of kimchi with steam rising from it by a kind 70s neighbor grandmother, soft scattered afternoon outdoor rim lighting", "08_Granny_Visiting"),
        
        # 9. 간판
        (f"{eunsook} hanging a clean neat wooden banner written Haneunsook Banchan high up, morning sunlight scattering through dusty air of traditional marketplace alleyway, rough signage textures, lively background crowd defocus", "09_Store_Opening"),
        
        # 10. 소문 (대박)
        (f"{eunsook} standing proudly behind marketplace booth corner loaded with diverse green and red side dish plates giving glossy wet lighting reflections, energetic sidelight bouncing, packed cheerful customer crowds defocus", "10_Success_Moment"),
        
        # 11. 아들 사죄
        (f"{eunsook} weeping holding hands with a young 28-year-old crying face man, dramatic sunset orange light breaking through living room glass window reflecting on dusty floor floorboards, heavy emotional air", "11_Son_Apology"),
        
        # 12. 현우의 도움
        (f"A quiet 50s Korean man carrying a heavy transparent tub walking with {eunsook} down a rough damp asphalt paved traditional market alleyway, cinematic backlight scattering in dusty market air ambient bustle", "12_Bookstore_Helper"),
        
        # 13. 위로
        (f"{eunsook} touching glasses indoor cozy bookstore cafe together with a kind 50s man wearing reading glasses across warm mahogany table, steam rising from coffee mugs, golden sunset lighting scattering, peaceful vibes", "13_Touched_Feelings"),
        
        # 14. 복수 장부
        (f"{eunsook} focused sitting analyzing banking financial sheets and corporate papers, metal vintage calculator prop reflecting white spotlight highlights on desk, dense silent night", "14_Evidence_Revenge"),
        
        # 15. 승리
        (f"{eunsook} standing in high-ceiling modern office layout holding a reported files stack, sleek polished tile floor reflecting sides window daylight, office props stillness posture", "15_Victorious_Ruin"),
        
        # 16. 해피엔딩
        (f"{eunsook} smiling very brightly, holding hands with a kind 50s Korean man wearing spectacles walking down a wet rough paved bookstore alleyway, cinematic golden hour lens flare scattering warmth, out of focus crowd lively air", "16_Happy_Ending")
    ]

    print("🎬 '빛/공기/질감 환경 묘사 고도화 + 사이즈 축소 48장' 연쇄 생성을 시작합니다.")
    
    count = 1
    for i, (pose_desc, prefix) in enumerate(SCENES):
        for var_id in range(1, 4): 
            generate_scene_storyboard(i + 1, var_id, pose_desc, prefix)
            time.sleep(1)
            count += 1

    print(f"\n✨ [생성 완료] 시네마틱 환경 48장 렌더링 끝!")
    print(f"📍 저장 위치: {DOWNLOADS_DIR}")
    os.system(f"open {DOWNLOADS_DIR}")

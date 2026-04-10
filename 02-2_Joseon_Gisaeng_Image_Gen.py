import json
import requests
import time
import os
import base64

# [설정]
DRAW_THINGS_URL = "http://127.0.0.1:7860" 
TIMESTAMP = time.strftime('%m%d_%H%M')
DOWNLOADS_DIR = f"/Users/a12/Downloads/Joseon_Gisaeng_Story_{TIMESTAMP}"

if not os.path.exists(DOWNLOADS_DIR):
    os.makedirs(DOWNLOADS_DIR)

def check_and_start_draw_things():
    """드로띵 앱 상태 확인"""
    print("⏳ [자동화] 드로띵 앱 및 API 서버 상태 확인 중...")
    
    check_app = os.popen('pgrep -x "Draw Things"').read().strip()
    if not check_app:
        print("🚀 드로띵 앱이 꺼져 있어 자동으로 실행합니다...")
        os.system('open -a "Draw Things"')
        time.sleep(10)

    for i in range(5):
        try:
            requests.get(f"{DRAW_THINGS_URL}/sdapi/v1/options", timeout=2)
            print("✅ 드로띵 API 서버가 활성화되어 있습니다.")
            return True
        except:
            print(f"⏳ API 서버 대기 중... ({i+1}/5)")
            time.sleep(5)
    return False

def generate_scene(scene_num, prompt_text):
    filename = f"Gisaeng_Scene_{scene_num:02d}.png"
    
    # 공통 고품질 프롬프트 접미사
    # [샘플러 설정 최종 교정: Euler A AYS (사용자 선호 설정)]
    payload = {
        "prompt": f"{prompt_text}, masterpiece, high-end cinematic, joseon dynasty period, traditional korean atmosphere, ultra-detailed textures, realistic lighting, 8k professional photography, high contrast, warm lamp light and moonlight",
        "negative_prompt": "text, watermark, banner, low quality, blurry, distorted, anime, cartoon, illustration, drawing, extra fingers, messy hands, distorted face, nsfw, naked, bad proportions, bad anatomy, modern objects, western features",
        "steps": 6,
        "width": 720,
        "height": 1280,
        "seed": 2024,
        "model": "z_image_turbo_1.0_q8p.ckpt",
        "guidance_scale": 1.0,
        "sampler": "Euler A AYS",
        "shift": 3.0,
        "sharpness": 6,
        "seed_mode": "Scale Alike"
    }
    
    print(f"🚀 [Draw Things] Scene {scene_num} 전송 중 (Sampler: Euler A AYS)...")
    try:
        response = requests.post(f"{DRAW_THINGS_URL}/sdapi/v1/txt2img", json=payload, timeout=600)
        if response.status_code == 200:
            data = response.json()
            if "images" in data:
                filepath = os.path.join(DOWNLOADS_DIR, filename)
                with open(filepath, "wb") as f:
                    f.write(base64.b64decode(data["images"][0]))
                print(f"  ✅ Scene {scene_num} 저장 완료! -> {filepath}")
                return True
        print(f"  ❌ Scene {scene_num} 실패: {response.status_code}")
    except Exception as e:
        print(f"  ❌ 드로띵 연결 오류: {e}")
    return False

if __name__ == "__main__":
    if not check_and_start_draw_things():
        print("💡 API 서버를 자동으로 켜지 못했습니다. 앱에서 [HTTP API Server -> Start]를 직접 확인해주세요.")

    # [캐릭터 및 배경 정의 - 현실성 극대화 (AI 느낌 제거)]
    # 박 서방: 현실적인 조선 중년 남성, 땀방울, 피부 질감 강조
    PARK = "A realistic obese Korean man in his 50s, natural aged skin with fine wrinkles and pores, NO HAT, traditional topknot (SANGTU), wearing light off-white indoor cotton hanbok, expressive sweaty face, Joseon Dynasty, 80mm lens portrait"
    # 매화: 인형 같은 얼굴 탈피, 현실적인 동양인 미인, 무꺼풀/속쌍꺼풀, 자연스러운 피부
    MAE_HWA = "A beautiful young Korean woman in her 20s, natural Korean facial features, monolid eyes, realistic skin texture with subtle pores, natural long black hair, wearing a thin traditional silk indoor hanbok, natural soft curves, elegant but realistic look, RAW photo style, Fujifilm-like cinematography"
    # 배경: 현실적인 광원과 그림자
    GIBANG = "inside a traditional Korean luxury bedroom, authentic wooden textures, warm flickering candlelight, deep shadows, cinematic atmosphere, no digital artifacts"

    # [장면별 프롬프트 - 현실적 연출 및 화각]
    PROMPTS = [
        f"Wide angle shot (24mm lens) of {PARK} sitting on the floor in {GIBANG}, shouting angrily, spit flying, face turning red with anger, realistic low angle, highly detailed skin texture.", # 1
        f"Full body shot (35mm lens) of {MAE_HWA} lying flat and still on the wooden floor in {GIBANG}, staring at the ceiling with a vacant indifferent look, realistic anatomy, natural lighting.", # 2
        f"Dynamic medium shot (24mm lens, low angle): {PARK} leaning over scolding {MAE_HWA} who is lying on the floor, visible tension in his neck, {GIBANG}, high contrast.", # 3
        f"Close up portrait (80mm lens) of {MAE_HWA}'s face, lying on the floor, a subtle and clever smile, natural Korean monolid eyes, detailed eyelashes, authentic skin glow, {GIBANG} bokeh.", # 4
        f"Medium shot (35mm lens) of {PARK} laughing heartily, belly shaking realistically, pulling out a heavy silk money pouch from his waist, {GIBANG}.", # 5
        f"Action shot (24mm lens): the silk money pouch falling onto {MAE_HWA}'s chest as she lies on the floor, blurred background of {PARK}, cinematic motion blur, {GIBANG}.", # 6
        f"Low angle medium shot (35mm lens) of {MAE_HWA} holding the money pouch close to her chest, a triumphant yet natural smile, cinematic lighting, 8k RAW photography, {GIBANG}." # 7
    ]

    print(f"🎬 매화 캐릭터의 현실성을 강화한(AI 느낌 제거) 이미지를 최종 재생성합니다. (Euler A AYS)")
    success_count = 0
    for i, p in enumerate(PROMPTS):
        if generate_scene(i+1, p):
            success_count += 1
    
    print(f"\n✨ [제작 완료] {success_count}/{len(PROMPTS)}장 생성 성공!")
    print(f"📍 저장 위치: {DOWNLOADS_DIR}")
    os.system(f"open {DOWNLOADS_DIR}")

import json
import urllib.request
import time
import os
import shutil
from pathlib import Path

# [설정]
COMFYUI_URL = "http://127.0.0.1:8188"
INPUT_DIR = "/Users/a12/Downloads/Local_ZImage_Scenes" # Z-이미지 생성 결과물 폴더
COMFY_INPUT_DIR = "/Users/a12/projects/tts/ComfyUI/input" # ComfyUI 입력 폴더
OUTPUT_DIR = "/Users/a12/projects/tts/ComfyUI/output"
DOWNLOADS_DIR = "/Users/a12/Downloads/Local_I2V_Clips"

os.makedirs(DOWNLOADS_DIR, exist_ok=True)

def queue_prompt(prompt):
    p = {"prompt": prompt}
    data = json.dumps(p).encode('utf-8')
    req = urllib.request.Request(f"{COMFYUI_URL}/prompt", data=data)
    return json.loads(urllib.request.urlopen(req).read())

def get_history(prompt_id):
    try:
        with urllib.request.urlopen(f"{COMFYUI_URL}/history/{prompt_id}") as response:
            return json.loads(response.read())
    except:
        return {}

# LTX-Video I2V 워크플로우 템플릿 (generate_video.py 기준 가공)
def get_i2v_workflow(image_name, scene_prompt):
    return {
        "1": { "class_type": "UnetLoaderGGUF", "inputs": { "ckpt_name": "ltx-video-2b-v0.9-Q4_K_M.gguf" } },
        "2": { "class_type": "CLIPLoader", "inputs": { "clip_name": "t5xxl_fp8_e4m3fn.safetensors", "type": "ltxv", "device": "default" } },
        "3": { "class_type": "VAELoader", "inputs": { "vae_name": "LTX-Video-VAE-BF16.safetensors" } },
        "4": { "class_type": "LoadImage", "inputs": { "image": image_name, "upload": "image" } },
        "5": { "class_type": "CLIPTextEncode", "inputs": { "text": scene_prompt, "clip": ["2", 0] } },
        "6": { "class_type": "CLIPTextEncode", "inputs": { "text": "low quality, blurry, static, distorted, bad anatomy", "clip": ["2", 0] } },
        "7": { "class_type": "LTXVImgToVideo", "inputs": { "positive": ["5", 0], "negative": ["6", 0], "vae": ["3", 0], "image": ["4", 0], "width": 768, "height": 512, "length": 33, "batch_size": 1, "strength": 1.0 } },
        "8": { "class_type": "LTXVConditioning", "inputs": { "positive": ["7", 0], "negative": ["7", 1], "frame_rate": 24 } },
        "9": { "class_type": "LTXVScheduler", "inputs": { "steps": 25, "cfg": 2.05, "stochasticity": 0.95, "offload_model": True, "latent": ["7", 2] } },
        "10": { "class_type": "KSamplerSelect", "inputs": { "sampler_name": "euler" } },
        "11": { "class_type": "SamplerCustom", "inputs": { "add_noise": True, "noise_seed": int(time.time()), "steps": 3, "cfg": 1, "model": ["1", 0], "positive": ["8", 0], "negative": ["8", 1], "sampler": ["10", 0], "sigmas": ["9", 0], "latent_image": ["7", 2] } },
        "12": { "class_type": "VAEDecode", "inputs": { "samples": ["11", 0], "vae": ["3", 0] } },
        "13": { "class_type": "CreateVideo", "inputs": { "frame_rate": 24, "images": ["12", 0] } },
        "14": { "class_type": "SaveVideo", "inputs": { "video": ["13", 0], "filename_prefix": f"I2V_{image_name.split('.')[0]}" } }
    }

def run_i2v_batch():
    # 1. 대상 이미지 목록 확보
    images = sorted([f for f in os.listdir(INPUT_DIR) if f.endswith(".png")])
    if not images:
        print(f"❌ '{INPUT_DIR}' 폴더에 이미지가 없습니다.")
        return

    print(f"🚀 총 {len(images)}장의 이미지를 AI 영상(I2V)으로 변환합니다.")
    
    prompt_ids = []
    for i, img_name in enumerate(images):
        scene_num = i + 1
        
        # 이미지를 ComfyUI input 폴더로 복사
        src_path = os.path.join(INPUT_DIR, img_name)
        dst_path = os.path.join(COMFY_INPUT_DIR, img_name)
        shutil.copy(src_path, dst_path)
        
        # 프롬프트 구성 (기본 시네마틱 프롬프트 사용)
        scene_prompt = "A beautiful cinematic video, high quality, realistic movement, watercolor style continuity."
        
        wf = get_i2v_workflow(img_name, scene_prompt)
        
        print(f"📤 [장면 {scene_num:02d}] I2V 큐 등록 중... ({img_name})")
        try:
            res = queue_prompt(wf)
            prompt_ids.append((scene_num, res['prompt_id']))
            time.sleep(1) # 부하 분산
        except Exception as e:
            print(f"❌ 장면 {scene_num} 큐 등록 실패: {e}")

    print(f"\n✅ {len(prompt_ids)}개 장면이 모두 I2V 큐에 등록되었습니다!")
    print(f"📸 AI가 각 사진을 살아 움직이는 영상으로 변환하는 중입니다 (약 10~20분 소요).")

    # 백그라운드에서 파일 수거 대기
    pending = prompt_ids.copy()
    while pending:
        for item in pending[:]:
            s_num, p_id = item
            history = get_history(p_id)
            if p_id in history:
                print(f"✨ [장면 {s_num:02d}] 영상 생성 완료! 수거 중...")
                # LTX-Video는 SaveVideo 노드를 사용하므로 outputs 구조 확인 필요
                # 보통 '14'번 노드가 SaveVideo
                if '14' in history[p_id]['outputs']:
                    videos = history[p_id]['outputs']['14']['videos']
                    for vid in videos:
                        file_name = vid['filename']
                        src = os.path.join(OUTPUT_DIR, file_name)
                        dst = os.path.join(DOWNLOADS_DIR, file_name)
                        if os.path.exists(src):
                            shutil.move(src, dst)
                            print(f"🚚 영상 이동 완료: {file_name}")
                pending.remove(item)
        time.sleep(10)

    print(f"\n🎉 모든 {len(images)}개 장면의 AI 영상 변환 및 수거가 완료되었습니다!")
    print(f"📂 저장 위치: {DOWNLOADS_DIR}")

if __name__ == "__main__":
    run_i2v_batch()

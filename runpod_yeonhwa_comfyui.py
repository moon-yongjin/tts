import requests
import json
import os
import time
from datetime import datetime

# --- 설정 ---
COMFYUI_BASE = "https://ko3dsyw10g4any-8188.proxy.runpod.net"
OUTPUT_DIR = os.path.expanduser("~/Downloads")
TIMESTAMP = datetime.now().strftime("%m%d_%H%M")
SAVE_DIR = os.path.join(OUTPUT_DIR, f"Yeonhwa_RunPod_{TIMESTAMP}")
os.makedirs(SAVE_DIR, exist_ok=True)

# --- 연화이야기 장면 리스트 ---
IDO_PROFILE = "A handsome but arrogant 20-year-old Korean nobleman (IDO), fine silk hanbok, topknot (SANGTU), sharp and cold facial features"
YEONHWA_PROFILE = "A beautiful but humble 18-year-old Korean woman (YEONHWA), simple traditional commoner's hanbok, long dark hair tied lowly, sad but resilient eyes"
YEONHWA_SUCCESS_PROFILE = "An extraordinarily beautiful and wealthy 28-year-old Korean merchant woman (YEONHWA), elegant and expensive silk hanbok, sophisticated makeup, cold and dignified aura"
IDO_BEGGAR_PROFILE = "A miserable 30-year-old Korean beggar man (IDO), dirty and thin face, matted hair, wearing torn and filthy rags, desperate eyes"

SCENES = [
    {"name": "01_Arrogant_Ido", "prompt": f"(Cinematic shot, low angle), {IDO_PROFILE} shouting with a sneer at {YEONHWA_PROFILE} who has her head bowed, grand traditional Korean house (Hanok), dramatic sunlight, masterpiece, 8k"},
    {"name": "02_The_Kick", "prompt": f"(Dynamic action shot), {IDO_PROFILE} drunk, kicking {YEONHWA_PROFILE}, spilled traditional side dishes on wooden floor, dim candlelight, night, masterpiece, 8k"},
    {"name": "03_Expulsion", "prompt": f"(Melancholy wide shot), {YEONHWA_PROFILE} walking away from grand wooden Hanok gate in rain, small cloth bundle, coughing with trace of blood, miserable night, masterpiece, 8k"},
    {"name": "04_Beggar_Ido", "prompt": f"(Close-up), {IDO_BEGGAR_PROFILE} begging on a dusty street of old Seoul (Hanseong), dirty hands reaching out, 10 years later, masterpiece, 8k"},
    {"name": "05_Palanquin_Encounter", "prompt": f"(Low angle shot), {IDO_BEGGAR_PROFILE} prostrating in front of luxurious traditional Korean palanquin (Gama), wealthy guards in silk uniforms, traditional Korean market, masterpiece, 8k"},
    {"name": "06_Yeonhwa_Revelation", "prompt": f"(Dramatic close-up), {YEONHWA_SUCCESS_PROFILE} looking down from inside palanquin through silk curtain, noble and cold expression, candlelight in her sharp eyes, masterpiece, 8k"},
    {"name": "07_Judgment", "prompt": f"(Cinematic shot), {YEONHWA_SUCCESS_PROFILE} closing palanquin curtain, servants throwing raw meat at {IDO_BEGGAR_PROFILE} crying in dirt, sunset lighting, masterpiece, 8k"},
]

NEGATIVE = "low quality, blurry, distorted, watermark, modern clothing, western features, bad anatomy"


def build_workflow(positive_prompt, negative_prompt="", seed=None):
    """ComfyUI API용 워크플로우 JSON 생성 (GGUF ZImage Turbo 기반)"""
    if seed is None:
        seed = int(time.time()) % 100000
    return {
        "prompt": {
            "1": {
                "class_type": "UnetLoaderGGUF",
                "inputs": {"unet_name": "z_image_turbo-Q5_K_M.gguf"}
            },
            "2": {
                "class_type": "CLIPLoader",
                "inputs": {"clip_name": "qwen_3_4b_fp8_mixed.safetensors", "type": "lumina2"}
            },
            "3": {
                "class_type": "VAELoader",
                "inputs": {"vae_name": "ae.safetensors"}
            },
            "4": {
                "class_type": "EmptyLatentImage",
                "inputs": {"width": 720, "height": 1280, "batch_size": 1}
            },
            "5": {
                "class_type": "CLIPTextEncode",
                "inputs": {"text": positive_prompt, "clip": ["2", 0]}
            },
            "6": {
                "class_type": "CLIPTextEncode",
                "inputs": {"text": negative_prompt, "clip": ["2", 0]}
            },
            "7": {
                "class_type": "KSampler",
                "inputs": {
                    "seed": seed,
                    "steps": 6,
                    "cfg": 1.5,
                    "sampler_name": "euler",
                    "scheduler": "simple",
                    "denoise": 1.0,
                    "model": ["1", 0],
                    "positive": ["5", 0],
                    "negative": ["6", 0],
                    "latent_image": ["4", 0]
                }
            },
            "8": {
                "class_type": "VAEDecode",
                "inputs": {"samples": ["7", 0], "vae": ["3", 0]}
            },
            "9": {
                "class_type": "SaveImage",
                "inputs": {"images": ["8", 0], "filename_prefix": "Yeonhwa"}
            }
        }
    }


def submit_prompt(workflow):
    """ComfyUI에 프롬프트 전송, prompt_id 반환"""
    url = f"{COMFYUI_BASE}/prompt"
    response = requests.post(url, json=workflow, timeout=10)
    if response.status_code == 200:
        return response.json().get("prompt_id")
    else:
        print(f"  ❌ 프롬프트 전송 실패: {response.status_code} - {response.text[:200]}")
        return None


def wait_for_result(prompt_id, timeout=120):
    """생성 완료 대기"""
    url = f"{COMFYUI_BASE}/history/{prompt_id}"
    for _ in range(timeout):
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            if prompt_id in data:
                return data[prompt_id]
        time.sleep(1)
    return None


def download_image(filename, save_path):
    """ComfyUI 서버에서 이미지 다운로드"""
    url = f"{COMFYUI_BASE}/view?filename={filename}&type=output"
    resp = requests.get(url, timeout=30)
    if resp.status_code == 200:
        with open(save_path, "wb") as f:
            f.write(resp.content)
        return True
    return False


def main():
    print("=" * 50)
    print("🚀 RunPod ComfyUI 이미지 생성 시작")
    print(f"🔗 서버: {COMFYUI_BASE}")
    print(f"📍 저장 폴더: {SAVE_DIR}")
    print("=" * 50)

    # 연결 테스트
    try:
        test = requests.get(f"{COMFYUI_BASE}/system_stats", timeout=5)
        print(f"✅ RunPod 연결 성공! (상태: {test.status_code})\n")
    except Exception as e:
        print(f"❌ RunPod 연결 실패: {e}")
        return

    for i, scene in enumerate(SCENES):
        print(f"\n🎨 [{i+1}/{len(SCENES)}] {scene['name']} 생성 중...")
        
        workflow = build_workflow(scene["prompt"], NEGATIVE, seed=2024+i)
        
        prompt_id = submit_prompt(workflow)
        if not prompt_id:
            print("  ⚠️ 건너뜀")
            continue
        
        print(f"  📡 전송 완료 (ID: {prompt_id[:8]}...), 생성 대기 중...")
        result = wait_for_result(prompt_id, timeout=120)
        
        if result and "outputs" in result:
            outputs = result["outputs"]
            saved = False
            for node_id, node_output in outputs.items():
                if "images" in node_output:
                    for img_info in node_output["images"]:
                        filename = img_info["filename"]
                        save_path = os.path.join(SAVE_DIR, f"{scene['name']}.png")
                        if download_image(filename, save_path):
                            print(f"  ✅ 저장 완료: {save_path}")
                            saved = True
            if not saved:
                print(f"  ⚠️ 이미지 다운로드 실패")
        else:
            print(f"  ⚠️ 생성 결과 없음 (타임아웃 또는 오류)")

    print(f"\n🎉 모든 장면 처리 완료! -> {SAVE_DIR}")


if __name__ == "__main__":
    main()

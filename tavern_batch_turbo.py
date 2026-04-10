#!/usr/bin/env python3
"""
🚀 터보 배치 영상 생성기 (Turbo Batch Video Generator)
Step 0: Whisk 이미지 → PNG 변환 → RunPod 업로드
Step 1: tavern_woman_scenes.json의 20개 장면을 RunPod ComfyUI에 고속 큐잉
Step 2: 4-step Turbo 설정으로 최대 속도 생성
Step 3: 생성 완료 즉시 자동 다운로드
"""
import json
import requests
import time
import os
import glob
import shutil
import subprocess

# === 설정 ===
RUNPOD_URL   = "https://qq063dyrqix4ht-8188.proxy.runpod.net"
TOKEN        = "$2b$12$J.2cd4LqTbmqwo6u2ao5wefyJNidzZeaAGPwx2o/NzFmwDut7cPly"
SCENES_FILE  = "/Users/a12/projects/tts/tavern_woman_scenes.json"
OUTPUT_DIR   = os.path.expanduser("~/Downloads/TavernWoman_Videos")
DOWNLOADS    = os.path.expanduser("~/Downloads")
SSH_KEY      = "/Users/a12/projects/tts/id_ed25519_runpod"
SSH_HOST     = "root@213.173.102.168"
SSH_PORT     = "12139"
REMOTE_INPUT = "/workspace/ComfyUI/input"

os.makedirs(OUTPUT_DIR, exist_ok=True)

# ─────────────────────────────────────────────
# STEP 0: 이미지 수집 → PNG 변환 → 서버 업로드
# ─────────────────────────────────────────────

def find_whisk_images() -> list:
    """Downloads 폴더에서 Whisk 이미지를 날짜순으로 수집"""
    patterns = ["Whisk_*.jpeg", "Whisk_*.jpg", "Whisk_*.png", "whisk_*.jpeg", "whisk_*.jpg"]
    files = []
    for pat in patterns:
        files += glob.glob(os.path.join(DOWNLOADS, pat))
    files = sorted(files, key=os.path.getmtime)
    return files

def convert_to_png(src_path: str, dest_path: str) -> bool:
    """sips(macOS 내장)으로 JPEG → PNG 변환"""
    result = subprocess.run(
        ["sips", "-s", "format", "png", src_path, "--out", dest_path],
        capture_output=True
    )
    return result.returncode == 0

def upload_image(local_path: str, remote_name: str) -> bool:
    """이미지를 RunPod 서버의 ComfyUI input 디렉토리에 업로드"""
    remote_target = f"{SSH_HOST}:{REMOTE_INPUT}/{remote_name}"
    result = subprocess.run([
        "scp", "-i", SSH_KEY,
        "-o", "StrictHostKeyChecking=no",
        "-P", SSH_PORT,
        local_path,
        remote_target
    ], capture_output=True)
    return result.returncode == 0

def prepare_images(scenes: list) -> dict:
    """
    Whisk 이미지를 장면 순서에 맞게 PNG로 변환하고 서버에 업로드.
    반환값: {scene_num: remote_filename}
    """
    print("\n" + "="*50)
    print("📸 STEP 0: 이미지 준비 및 서버 업로드")
    print("="*50)

    whisk_files = find_whisk_images()
    if not whisk_files:
        print("⚠️  Whisk 이미지를 찾을 수 없습니다!")
        print("   ~/Downloads/Whisk_*.jpeg 를 확인해 주세요.")
        print("   → 기본 이미지('1.png')로 모든 장면을 생성합니다.")
        return {s["scene"]: "1.png" for s in scenes}

    print(f"📁 발견된 Whisk 이미지: {len(whisk_files)}개")
    for i, f in enumerate(whisk_files):
        print(f"   {i+1}. {os.path.basename(f)}")

    scene_image_map = {}
    tmp_dir = "/tmp/tavern_png_convert"
    os.makedirs(tmp_dir, exist_ok=True)

    for i, scene in enumerate(scenes):
        num = scene["scene"]
        # 이미지가 장면보다 적으면 마지막 이미지 재사용
        src = whisk_files[min(i, len(whisk_files) - 1)]
        remote_name = f"tavern_{num:02d}.png"
        tmp_png = os.path.join(tmp_dir, remote_name)

        print(f"\n🔄 Scene {num:02d}: {os.path.basename(src)}")

        # PNG 변환
        if src.lower().endswith(".png"):
            shutil.copy(src, tmp_png)
            print(f"   ✅ PNG 복사 완료")
        else:
            ok = convert_to_png(src, tmp_png)
            if ok:
                print(f"   ✅ PNG 변환 완료")
            else:
                print(f"   ❌ 변환 실패, 원본 사용")
                shutil.copy(src, tmp_png)

        # 서버 업로드
        ok = upload_image(tmp_png, remote_name)
        if ok:
            print(f"   ☁️  업로드 완료: {REMOTE_INPUT}/{remote_name}")
            scene_image_map[num] = remote_name
        else:
            print(f"   ❌ 업로드 실패, 기본 이미지 사용")
            scene_image_map[num] = "1.png"

    print("\n✅ 이미지 준비 완료!\n")
    shutil.rmtree(tmp_dir, ignore_errors=True)
    return scene_image_map

# ─────────────────────────────────────────────
# STEP 1-2: 워크플로우 빌드 및 생성
# ─────────────────────────────────────────────

def build_workflow(positive_text: str, image_name: str, seed: int) -> dict:
    """4-step Turbo 워크플로우 생성 (서버 히스토리 기반 정답 설정)"""
    return {
        "1": {
            "inputs": {"ckpt_name": "ltx-2-19b-dev-fp8.safetensors"},
            "class_type": "CheckpointLoaderSimple"
        },
        "2": {
            "inputs": {
                "text_encoder": "gemma_3_12B_it_fp4_mixed.safetensors",
                "ckpt_name": "ltx-2-19b-dev-fp8.safetensors",
                "device": "default"
            },
            "class_type": "LTXAVTextEncoderLoader"
        },
        "20": {
            "inputs": {
                "lora_name": "ltx-2-19b-distilled-lora-384.safetensors",
                "strength_model": 1.0,
                "strength_clip": 1.0,
                "model": ["1", 0],
                "clip": ["2", 0]
            },
            "class_type": "LoraLoader"
        },
        "3": {
            "inputs": {"text": positive_text, "clip": ["2", 0]},
            "class_type": "CLIPTextEncode"
        },
        "4": {
            "inputs": {
                "text": "blurry, low quality, static, watermark, text.",
                "clip": ["2", 0]
            },
            "class_type": "CLIPTextEncode"
        },
        "10": {
            "inputs": {"image": image_name, "upload": "image"},
            "class_type": "LoadImage"
        },
        "5": {
            "inputs": {"frame_rate": 25, "positive": ["3", 0], "negative": ["4", 0]},
            "class_type": "LTXVConditioning"
        },
        "6": {
            "inputs": {"width": 768, "height": 512, "length": 49, "batch_size": 1},
            "class_type": "EmptyLTXVLatentVideo"
        },
        # ⚡ 핵심: 4-step turbo 전용 시그마
        "73": {
            "inputs": {"sigmas": "0.909375, 0.725, 0.421875, 0.0"},
            "class_type": "ManualSigmas"
        },
        "9": {"inputs": {"sampler_name": "euler"}, "class_type": "KSamplerSelect"},
        "15": {"inputs": {"noise_seed": seed}, "class_type": "RandomNoise"},
        "12": {
            "inputs": {
                "cfg": 1.0,
                "model": ["20", 0],
                "positive": ["5", 0],
                "negative": ["5", 1]
            },
            "class_type": "CFGGuider"
        },
        "11": {
            "inputs": {
                "noise": ["15", 0],
                "guider": ["12", 0],
                "sampler": ["9", 0],
                "sigmas": ["73", 0],
                "latent_image": ["6", 0]
            },
            "class_type": "SamplerCustomAdvanced"
        },
        "13": {
            "inputs": {"samples": ["11", 0], "vae": ["1", 2]},
            "class_type": "VAEDecode"
        },
        "14": {
            "inputs": {
                "frame_rate": 24,
                "loop_count": 0,
                "filename_prefix": f"tavern_scene",
                "format": "video/h264-mp4",
                "pix_fmt": "yuv420p",
                "crf": 19,
                "save_output": True,
                "pingpong": False,
                "images": ["13", 0]
            },
            "class_type": "VHS_VideoCombine"
        }
    }

def queue_prompt(workflow: dict) -> str | None:
    try:
        r = requests.post(
            f"{RUNPOD_URL}/prompt",
            json={"prompt": workflow},
            params={"token": TOKEN},
            timeout=15
        )
        if r.status_code == 200:
            return r.json().get("prompt_id")
        else:
            print(f"  ❌ 큐 실패 ({r.status_code}): {r.text[:200]}")
            return None
    except Exception as e:
        print(f"  ❌ 요청 오류: {e}")
        return None

def wait_for_completion(prompt_id: str, timeout_sec: int = 300) -> bool:
    start = time.time()
    dots = 0
    while time.time() - start < timeout_sec:
        try:
            r = requests.get(
                f"{RUNPOD_URL}/history/{prompt_id}",
                params={"token": TOKEN},
                timeout=10
            )
            if r.status_code == 200:
                data = r.json()
                if prompt_id in data:
                    status = data[prompt_id].get("status", {})
                    if status.get("completed"):
                        return True
                    err = [m for m in status.get("messages", []) if m[0] == "execution_error"]
                    if err:
                        print(f"\n  ❌ 오류: {err[-1]}")
                        return False
        except Exception:
            pass
        dots = (dots + 1) % 4
        print(f"\r  ⏳ 생성 중{'.' * dots}   ", end="", flush=True)
        time.sleep(3)
    print()
    return False

def download_outputs(prompt_id: str, scene_num: int) -> list:
    downloaded = []
    try:
        r = requests.get(
            f"{RUNPOD_URL}/history/{prompt_id}",
            params={"token": TOKEN},
            timeout=10
        )
        if r.status_code != 200:
            return downloaded
        history = r.json().get(prompt_id, {})
        for node_id, node_out in history.get("outputs", {}).items():
            for item in node_out.get("gifs", []) + node_out.get("videos", []):
                fname = item.get("filename")
                subfolder = item.get("subfolder", "")
                if fname:
                    remote = f"{REMOTE_INPUT.replace('input','output')}/{subfolder}/{fname}".replace("//", "/")
                    local = os.path.join(OUTPUT_DIR, f"scene_{scene_num:02d}_{fname}")
                    ret = subprocess.run([
                        "scp", "-i", SSH_KEY,
                        "-o", "StrictHostKeyChecking=no",
                        "-P", SSH_PORT,
                        f"{SSH_HOST}:{remote}",
                        local
                    ], capture_output=True)
                    if ret.returncode == 0:
                        print(f"\n  ⬇️  저장: {os.path.basename(local)}")
                        downloaded.append(local)
    except Exception as e:
        print(f"\n  ❌ 다운로드 오류: {e}")
    return downloaded

# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────
def main():
    with open(SCENES_FILE, "r", encoding="utf-8") as f:
        scenes = json.load(f)

    print("="*50)
    print("🍶 주막 주모 터보 배치 생성기")
    print(f"   장면 수: {len(scenes)}개 | 저장위치: {OUTPUT_DIR}")
    print("="*50)

    # STEP 0: 이미지 준비
    scene_image_map = prepare_images(scenes)

    # STEP 1~3: 생성 + 다운로드
    print("="*50)
    print("🎬 STEP 1-3: 영상 생성 시작")
    print("="*50)

    all_downloads = []
    for scene in scenes:
        num = scene["scene"]
        img  = scene_image_map.get(num, "1.png")
        text = scene["visual_prompt"]

        print(f"\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print(f"🎬 Scene {num:02d} | 이미지: {img}")
        print(f"   {scene['description']}")

        wf  = build_workflow(text, img, seed=num * 137)
        pid = queue_prompt(wf)
        if not pid:
            print(f"  ⚠️  큐 실패, 다음 장면으로")
            continue

        print(f"  ✅ 큐 ID: {pid}")
        success = wait_for_completion(pid)
        if success:
            files = download_outputs(pid, num)
            all_downloads.extend(files)
        else:
            print(f"  ⚠️  Scene {num} 생성 실패")

        time.sleep(2)

    print(f"\n{'='*50}")
    print(f"🎉 완료! 총 {len(all_downloads)}/{len(scenes)}개 장면 다운로드됨")
    print(f"📁 {OUTPUT_DIR}")
    print("="*50)

if __name__ == "__main__":
    main()

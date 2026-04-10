import json
import urllib.request
import urllib.parse
import uuid
import time
import argparse
import os
import re
import threading
import websocket
import subprocess

# ---------------------------------------------------------
# [CONFIG] RunPod ComfyUI 접속 정보
# ---------------------------------------------------------
SERVER_ADDRESS = "127.0.0.1:8181"
CLIENT_ID = str(uuid.uuid4())

# 런팟 SSH 정보 (자동 다운로드용)
RP_IP = "213.173.109.153"
RP_PORT = "13006"
RP_KEY = "/Users/a12/projects/tts/id_ed25519_runpod"

def queue_prompt(prompt):
    p = {"prompt": prompt, "client_id": CLIENT_ID}
    data = json.dumps(p).encode('utf-8')
    req = urllib.request.Request(f"http://{SERVER_ADDRESS}/prompt", data=data)
    with urllib.request.urlopen(req) as response:
        return json.loads(response.read())

def get_workflow(positive_prompt, index, prefix="AudioBatch"):
    return {
        "1": {
            "inputs": {"unet_name": "z_image_turbo-Q5_K_M.gguf"},
            "class_type": "UnetLoaderGGUF"
        },
        "2": {
            "inputs": {"clip_name": "qwen_3_4b_fp8_mixed.safetensors", "type": "lumina2"},
            "class_type": "CLIPLoader"
        },
        "3": {
            "inputs": {"vae_name": "ae.safetensors"},
            "class_type": "VAELoader"
        },
        "4": {
            "inputs": {"width": 1024, "height": 1024, "batch_size": 1},
            "class_type": "EmptyLatentImage"
        },
        "5": {
            "inputs": {"text": positive_prompt, "clip": ["2", 0]},
            "class_type": "CLIPTextEncode"
        },
        "6": {
            "inputs": {
                "seed": 42 + index,
                "steps": 6,
                "cfg": 1.0,
                "sampler_name": "euler",
                "scheduler": "simple",
                "denoise": 1.0,
                "model": ["1", 0],
                "positive": ["5", 0],
                "negative": ["7", 0],
                "latent_image": ["4", 0]
            },
            "class_type": "KSampler"
        },
        "7": {
            "inputs": {"text": "cleavage, low-cut, nudity, nipples, naked, bare skin, exposure, bikini, lingerie, underwear, uncensored, low quality, blurry, distorted, messy, animation, anime, cartoon, painting, drawing, hanbok, traditional korean clothes, traditional clothing, western face, caucasian, blonde hair, blue eyes, foreigner, man, male, boy, son, husband, father, text, watermark, writing, letters, signature, child, children, baby, kid, infant, teenager, young boy, young girl", "clip": ["2", 0]},
            "class_type": "CLIPTextEncode"
        },
        "8": {
            "inputs": {"samples": ["6", 0], "vae": ["3", 0]},
            "class_type": "VAEDecode"
        },
        "9": {
            "inputs": {"filename_prefix": f"{prefix}_{index+1:03d}", "images": ["8", 0]},
            "class_type": "SaveImage"
        }
    }

def download_image(filename, target_dir):
    """런팟 서버에서 특정 이미지를 scp로 즉시 다운로드"""
    remote_path = f"root@{RP_IP}:/workspace/ComfyUI/output/{filename}"
    local_path = os.path.join(target_dir, filename)
    
    cmd = [
        "scp", "-P", RP_PORT, "-i", RP_KEY,
        "-o", "StrictHostKeyChecking=no",
        remote_path, local_path
    ]
    
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except Exception as e:
        print(f"   ❌ 다운로드 실패 ({filename}): {e}")
        return False

def listen_and_download(target_dir, expected_count, prefix):
    """웹소켓을 통해 생성 완료를 감지하고 즉시 다운로드 (로컬 001부터 리네이밍)"""
    ws = websocket.WebSocket()
    ws.settimeout(120)  # 120초 타임아웃: 2분 동안 새 이미지 안 오면 종료
    ws.connect(f"ws://{SERVER_ADDRESS}/ws?clientId={CLIENT_ID}")
    
    print(f"📡 실시간 모니터링 시작... (저장위치: {target_dir})")
    downloaded_count = 0
    
    while downloaded_count < expected_count:
        try:
            out = ws.recv()
        except websocket.WebSocketTimeoutException:
            print(f"\n⏰ 120초간 새 이미지 없음. 수신 종료. ({downloaded_count}/{expected_count} 완료)")
            break
        except Exception as e:
            print(f"\n❌ WebSocket 에러: {e}")
            break
            
        if isinstance(out, str):
            message = json.loads(out)
            if message['type'] == 'executed':
                if 'images' in message.get('data', {}).get('output', {}):
                    for img in message['data']['output']['images']:
                        server_filename = img['filename']
                        # 로컬에서 001부터 순차 리네이밍
                        downloaded_count += 1
                        local_filename = f"{prefix}_{downloaded_count:03d}.png"
                        
                        print(f"✅ 생성 완료: {server_filename} -> 다운로드 중...")
                        
                        # 서버에서 원본 이름으로 다운로드
                        if download_image(server_filename, target_dir):
                            # 로컬에서 리네이밍
                            old_path = os.path.join(target_dir, server_filename)
                            new_path = os.path.join(target_dir, local_filename)
                            os.rename(old_path, new_path)
                            print(f"   📥 로컬 저장 완료! [{downloaded_count}/{expected_count}] -> {local_filename}")
                        else:
                            downloaded_count -= 1  # 실패 시 카운트 롤백
    
    ws.close()
    if downloaded_count >= expected_count:
        print(f"\n✨ 모든 파일의 실시간 다운로드가 완료되었습니다! ({downloaded_count}개)")
    else:
        print(f"\n⚠️ {downloaded_count}/{expected_count}개 다운로드 완료. 나머지는 서버에서 직접 확인해 주세요.")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", required=True, help="Path to visual_prompts.json")
    parser.add_argument("--server", default="127.0.0.1:8181", help="ComfyUI server address")
    parser.add_argument("--prefix", default="AudioBatch", help="Filename prefix for generated images")
    args = parser.parse_args()

    global SERVER_ADDRESS
    SERVER_ADDRESS = args.server

    if not os.path.exists(args.json):
        print(f"❌ 에러: JSON 파일을 찾을 수 없습니다: {args.json}")
        return

    with open(args.json, 'r', encoding='utf-8') as f:
        scenes = json.load(f)

    # 다운로드 폴더 생성
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    download_dir = os.path.join(os.path.expanduser("~"), "Downloads", f"Batch_GGUF_{timestamp}")
    os.makedirs(download_dir, exist_ok=True)

    # 유효한 프롬프트만 필터링
    valid_scenes = [(i, s) for i, s in enumerate(scenes) if s.get("visual_prompt", "")]
    actual_count = len(valid_scenes)

    print(f"🚀 총 {actual_count}개의 장면 생성을 런팟(GGUF)에 요청합니다...")
    print(f"⚡ 실시간 다운로드 모드 활성화됨 (v2 - WebSocket 선연결)")

    # ──────────────────────────────────────────────
    # [핵심 수정] WebSocket을 먼저 연결한 뒤 큐에 등록
    # ──────────────────────────────────────────────
    ws = websocket.WebSocket()
    ws.settimeout(120)
    ws.connect(f"ws://{SERVER_ADDRESS}/ws?clientId={CLIENT_ID}")
    print(f"📡 WebSocket 선연결 완료! 이제 큐에 등록합니다...")

    # 큐에 프롬프트 등록
    for i, scene in valid_scenes:
        p_text = scene["visual_prompt"]

        # [🚨 GENDER SAFETY FILTER] 프롬프트에서 남성 관련 단어 강제 제거
        forbidden_male_terms = ["man", "male", "boy", "son", "husband", "father"]
        cleaned_text = p_text
        for term in forbidden_male_terms:
            cleaned_text = re.sub(rf'\b{term}\b', '', cleaned_text, flags=re.IGNORECASE)
        cleaned_text = ' '.join(cleaned_text.split())

        if p_text != cleaned_text:
            print(f"   ⚠️ 남성 키워드 제거됨: {p_text[:40]}... -> {cleaned_text[:40]}...")

        print(f"📸 [{valid_scenes.index((i, scene))+1}/{actual_count}] 요청 중: {cleaned_text[:60]}...")
        workflow = get_workflow(cleaned_text, i, args.prefix)
        queue_prompt(workflow)
        time.sleep(0.5)

    print(f"✅ {actual_count}개 요청 완료. 실시간 수신 대기 중...")

    # WebSocket으로 생성 완료 대기 및 다운로드
    downloaded_count = 0
    try:
        while downloaded_count < actual_count:
            try:
                out = ws.recv()
            except websocket.WebSocketTimeoutException:
                print(f"\n⏰ 120초간 새 이미지 없음. 수신 종료. ({downloaded_count}/{actual_count} 완료)")
                break
            except Exception as e:
                print(f"\n❌ WebSocket 에러: {e}")
                break

            if isinstance(out, str):
                message = json.loads(out)
                if message['type'] == 'executed':
                    if 'images' in message.get('data', {}).get('output', {}):
                        for img in message['data']['output']['images']:
                            server_filename = img['filename']
                            downloaded_count += 1
                            local_filename = f"{args.prefix}_{downloaded_count:03d}.png"

                            print(f"✅ 생성 완료: {server_filename} -> 다운로드 중...")

                            if download_image(server_filename, download_dir):
                                old_path = os.path.join(download_dir, server_filename)
                                new_path = os.path.join(download_dir, local_filename)
                                os.rename(old_path, new_path)
                                print(f"   📥 로컬 저장 완료! [{downloaded_count}/{actual_count}] -> {local_filename}")
                            else:
                                downloaded_count -= 1
    except KeyboardInterrupt:
        print("\n⚠️ 사용자에 의해 중단되었습니다.")
    finally:
        ws.close()

    if downloaded_count >= actual_count:
        print(f"\n✨ 모든 파일의 실시간 다운로드가 완료되었습니다! ({downloaded_count}개)")
    else:
        print(f"\n⚠️ {downloaded_count}/{actual_count}개 다운로드 완료. 나머지는 서버에서 직접 확인해 주세요.")

if __name__ == "__main__":
    main()

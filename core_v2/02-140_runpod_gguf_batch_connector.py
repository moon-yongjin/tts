import json
import urllib.request
import urllib.parse
import uuid
import time
import argparse
import os
import websocket
import subprocess

# ---------------------------------------------------------
# [CONFIG] RunPod ComfyUI 접속 정보
# ---------------------------------------------------------
SERVER_ADDRESS = "https://zk5ekw6ljugl1u-8188.proxy.runpod.net"
CLIENT_ID = str(uuid.uuid4())

def get_base_url():
    return SERVER_ADDRESS.rstrip('/')

def get_ws_url():
    base = get_base_url()
    if base.startswith('https://'):
        return base.replace('https://', 'wss://')
    elif base.startswith('http://'):
        return base.replace('http://', 'ws://')
    return f'ws://{base}'

def queue_prompt(prompt):
    p = {"prompt": prompt, "client_id": CLIENT_ID}
    data = json.dumps(p).encode('utf-8')
    req = urllib.request.Request(f"{get_base_url()}/prompt", data=data)
    req.add_header('Content-Type', 'application/json')
    req.add_header('User-Agent', 'ComfyUI-Client/1.0')
    req.add_header('Accept', '*/*')
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
    """런팟 ComfyUI API로 이미지 다운로드"""
    url = f"{get_base_url()}/view?filename={urllib.parse.quote(filename)}&type=output"
    local_path = os.path.join(target_dir, filename)
    
    try:
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'ComfyUI-Client/1.0')
        with urllib.request.urlopen(req) as response:
            with open(local_path, 'wb') as f:
                f.write(response.read())
        return True
    except Exception as e:
        print(f"   ❌ 다운로드 실패 ({filename}): {e}")
        return False

def get_history():
    """ComfyUI 실행 히스토리 가져오기"""
    try:
        url = f"{get_base_url()}/history"
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'ComfyUI-Client/1.0')
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read())
    except Exception as e:
        print(f"   ⚠️ 히스토리 체크 실패: {e}")
        return {}

def listen_and_download(target_dir, expected_count):
    """웹소켓 + 폴링 하이브리드 방식으로 생성 완료 감지 및 다운로드"""
    downloaded_filenames = set()
    downloaded_count = 0
    
    # [1] 웹소켓 연결 시도
    ws = None
    try:
        ws = websocket.WebSocket()
        ws.settimeout(10.0) # 10초 타임아웃 설정 (폴링 병행을 위함)
        ws.connect(f"{get_ws_url()}/ws?clientId={CLIENT_ID}", header={"User-Agent: ComfyUI-Client/1.0"})
        print(f"📡 실시간 모니터링 시작... (저장위치: {target_dir})")
    except Exception as e:
        print(f"⚠️ 웹소켓 연결 실패 ({e}). 폴링 모드로만 작동합니다.")

    last_poll_time = 0
    
    while downloaded_count < expected_count:
        # [A] 웹소켓 메시지 수신 시도
        if ws:
            try:
                out = ws.recv()
                if isinstance(out, str):
                    message = json.loads(out)
                    if message['type'] == 'executing' and message['data'].get('node'):
                        print(f"⏳ 진행 중... (노드 {message['data']['node']})")
                    
                    if message['type'] == 'executed' and 'images' in message['data']['output']:
                        for img in message['data']['output']['images']:
                            filename = img['filename']
                            if filename not in downloaded_filenames:
                                print(f"✅ 웹소켓: {filename} 생성 감지!")
                                if download_image(filename, target_dir):
                                    downloaded_filenames.add(filename)
                                    downloaded_count = len(downloaded_filenames)
                                    print(f"   📥 저장 완료! [{downloaded_count}/{expected_count}]")
            except websocket.WebSocketTimeoutException:
                pass # 타임아웃 시 자연스럽게 폴링 단계로 넘어감
            except Exception as e:
                print(f"⚠️ 웹소켓 끊김 → 폴링 전용 모드로 전환: {e}")
                ws = None
        else:
            # 웹소켓이 없으면 3초 대기 (CPU 과부하 방지)
            time.sleep(3)

        # [B] 폴링 (10초마다 서버 히스토리 직접 확인 - 웹소켓 먹통 대비)
        current_time = time.time()
        if current_time - last_poll_time > 10:
            last_poll_time = current_time
            
            history = get_history()
            for prompt_id, data in history.items():
                if 'outputs' in data:
                    for node_id, node_output in data['outputs'].items():
                        if 'images' in node_output:
                            for img in node_output['images']:
                                filename = img['filename']
                                if filename not in downloaded_filenames:
                                    print(f"🔍 폴링: 새 이미지 발견! ({filename})")
                                    if download_image(filename, target_dir):
                                        downloaded_filenames.add(filename)
                                        downloaded_count = len(downloaded_filenames)
                                        print(f"   📥 저장 완료! [{downloaded_count}/{expected_count}]")
            
            if downloaded_count < expected_count:
                print(f"💬 대기 중... 현재 {downloaded_count}/{expected_count} 완료")

    if ws: ws.close()
    print("\n✨ 모든 파일의 다운로드가 완료되었습니다!")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", required=True, help="Path to visual_prompts.json")
    parser.add_argument("--server", default=None, help="ComfyUI server URL (e.g., https://xxx-8188.proxy.runpod.net)")
    parser.add_argument("--prefix", default="AudioBatch", help="Filename prefix for generated images")
    args = parser.parse_args()

    global SERVER_ADDRESS
    if args.server:
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

    print(f"🚀 총 {len(scenes)}개의 장면 생성을 런팟(GGUF)에 요청합니다...")
    print(f"⚡ 실시간 다운로드 모드 활성화됨")
    
    # 큐에 프롬프트 먼저 등록
    for i, scene in enumerate(scenes):
        p_text = scene.get("visual_prompt", "")
        if not p_text: continue

        # [🚨 GENDER SAFETY FILTER] 프롬프트에서 남성 관련 단어 강제 제거
        forbidden_male_terms = ["man", "male", "boy", "son", "husband", "father"]
        cleaned_text = p_text
        for term in forbidden_male_terms:
            # 대소문자 구분 없이 단어 단위로 제거
            import re
            cleaned_text = re.sub(rf'\b{term}\b', '', cleaned_text, flags=re.IGNORECASE)
        
        # 연속된 공백 정리
        cleaned_text = ' '.join(cleaned_text.split())

        if p_text != cleaned_text:
            print(f"   ⚠️ 남성 키워드 제거됨: {p_text[:40]}... -> {cleaned_text[:40]}...")

        print(f"📸 [{i+1}/{len(scenes)}] 요청 중: {cleaned_text[:60]}...")
        workflow = get_workflow(cleaned_text, i, args.prefix)
        queue_prompt(workflow)
        time.sleep(0.5)

    print(f"✅ {len(scenes)}개 요청 완료. 실시간 수신 대기 중...")
    
    # 웹소켓 리스너 실행 (모든 파일 받을 때까지 대기)
    try:
        listen_and_download(download_dir, len(scenes))
    except KeyboardInterrupt:
        print("\n⚠️ 사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"❌ 오류 발생: {e}")

if __name__ == "__main__":
    main()

import json
import urllib.request
import time
import re

# [설정]
COMFY_URL = "http://127.0.0.1:8188"

# JSON 프롬프트로 캐릭터 고정
CHARACTER_PROFILES = {
    "점례": "an elderly Korean woman, simple traditional clothes or work clothes, messy grey hair, hardworking appearance, kind but strong face",
    "지윤": "a beautiful Korean woman in her 30s, expensive luxury coat and bag, elegant but arrogant face, long black hair, flawless makeup",
    "민석": "a tall Korean man in his 30s, high-end power suit, sharp handsome face, serious and charismatic gaze, corporate leader style"
}

def parse_script(file_path, total_count):
    """대본 파일에서 장면과 대사를 추출하여 이미지 수량만큼 분배"""
    print(f"📖 대본 읽는 중: {file_path}")
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # 1. 쉼표, 마침표, 줄바꿈 등으로 문장/장면 분리
        raw_scenes = []
        paragraphs = [p.strip() for p in content.split("\n") if p.strip()]
        
        for p in paragraphs:
            # 대사 추출 로직 추가
            # "대사"를 찾아서 별도로 저장하거나, 장면 설명과 함께 튜플로 저장
            dialogue_match = re.search(r'"([^"]+)"', p)
            dialogue = dialogue_match.group(1) if dialogue_match else ""
            
            # 장면 설명 (대사 제외)
            scene_desc = re.sub(r'"[^"]+"', '', p).strip()
            if not scene_desc: scene_desc = "A cinematic movie scene"
            
            raw_scenes.append({"scene": scene_desc, "dialogue": dialogue})

        if not raw_scenes:
            return [{"scene": "A cinematic movie scene", "dialogue": ""}] * total_count

        # 2. 이미지 수량만큼 적절히 선택 (보간 또는 샘플링)
        final_scenes = []
        for i in range(total_count):
            idx = int((i / total_count) * len(raw_scenes))
            final_scenes.append(raw_scenes[idx])
        
        return final_scenes
    except Exception as e:
        print(f"⚠️ 대본 파싱 에러: {e}")
        return [{"scene": "A cinematic movie scene", "dialogue": ""}] * total_count

def build_character_prompt(scene_data):
    """대본 내용을 바탕으로 캐릭터 특징을 찾아 프롬프트 구성"""
    scene_description = scene_data["scene"]
    
    # 2. Positive 프롬프트 단어 치환 및 보강
    scene_description = scene_description.replace("screenshot", "photography").replace("still", "photography").replace("frame", "photography")
    
    # 캐릭터 키워드 매핑
    char_traits = ""
    for name, traits in CHARACTER_PROFILES.items():
        if name in scene_description:
            char_traits = f", {traits}"
            break 
    
    # 3. [전략] 인물 중심 + 꽉 찬 화면 (깨끗한 배경)
    full_prompt = f"(({scene_description})), (close-up shot:1.3), (medium shot:1.2), (focus on character:1.4), (detailed background:1.3), (cinematic atmosphere:1.2), (vivid facial expression:1.4), photography, depth of field{char_traits}, Korean drama style, 8k, high quality, clean image"
    
    return full_prompt

def optimize_workflow(workflow_json):
    """지시된 에이전트 최적화 로직 적용"""
    for node_id in workflow_json:
        node = workflow_json[node_id]
        if "FaceDetailer" in node.get("class_type", ""):
            node["mode"] = 4
        if "ZSamplerTurbo" in node.get("class_type", ""):
            node["inputs"]["cfg"] = 1.0
            node["inputs"]["steps"] = 6
        if "UNETLoader" in node.get("class_type", ""):
            node["inputs"]["weight_dtype"] = "fp8_e4m3fn"
    return workflow_json

def queue_prompt(prompt):
    p = {"prompt": prompt}
    data = json.dumps(p).encode('utf-8')
    req = urllib.request.Request(f"{COMFY_URL}/prompt", data=data)
    return json.loads(urllib.request.urlopen(req).read())

def get_history(prompt_id):
    with urllib.request.urlopen(f"{COMFY_URL}/history/{prompt_id}") as response:
        return json.loads(response.read())

def generate_image(prompt_text, dialogue_text, img_num):
    """단일 이미지 생성 (AnyText 자막 포함)"""
    
    # AnyText를 위한 워크플로우 (인메모리 JSON 구성)
    # 1. 기본 이미지 생성 (ZSamplerTurbo)
    # 2. AnyText로 자막 합성
    
    workflow = {
      "32": { "inputs": { "width": 1152, "height": 768, "batch_size": 1 }, "class_type": "EmptyLatentImage" },
      "35": { "inputs": { "unet_name": "z_image_turbo_bf16.safetensors", "weight_dtype": "fp8_e4m3fn" }, "class_type": "UNETLoader" },
      "37": { "inputs": { "vae_name": "ae.safetensors" }, "class_type": "VAELoader" },
      "44": { "inputs": { "clip_name": "qwen_3_4b.safetensors", "type": "lumina2" }, "class_type": "CLIPLoader" },
      "42": { "inputs": { "text": prompt_text, "clip": ["44", 0] }, "class_type": "CLIPTextEncode" },
      "18": { 
          "inputs": { 
              "seed": int(time.time() * 1000) + img_num, "steps": 6, "cfg": 1.5, "sampler_name": "euler", "scheduler": "normal", "denoise": 1.0, 
              "model": ["35", 0], "positive": ["42", 0], "latent_input": ["32", 0] 
          }, 
          "class_type": "ZSamplerTurbo //ZImagePowerNodes"
      },
      "8": { "inputs": { "samples": ["18", 0], "vae": ["37", 0] }, "class_type": "VAEDecode" },
      
      # AnyText 부분 (자막 합성)
      "50": {
          "inputs": {
              "ckpt_name": "anytext_v1.1_fp16.safetensors",
              "control_net_name": "anytext_v1.1_controlnet.safetensors", # Auto-loaded usually
              "miaobi_clip": "false",
              "weight_dtype": "fp16",
              "init_device": "cuda",
              "backend_for_v1": False
          },
          "class_type": "UL_AnyTextLoader"
      },
      "51": {
          "inputs": {
              "prompt": f"subtitle: {dialogue_text}", # 프롬프트에 텍스트 내용 포함
              "mode": "text-generation",
              "sort_radio": "↔ horizontal",
              "a_prompt": "best quality, 4k",
              "n_prompt": "lowres, bad anatomy, bad hands, text, error, missing fingers, extra digit, fewer digits, cropped, worst quality, low quality, normal quality, jpeg artifacts, signature, watermark, username, blurry",
              "revise_pos": False,
              "random_mask": False,
              "model": ["50", 0],
              "image": ["8", 0],  # 생성된 이미지 입력
              "font_name": "NotoSansKR-Medium.otf", # 다운로드한 폰트
              # 마스크 이미지가 필요함 (서버에 생성해둠)
              "mask_img": ["60", 0] 
          },
          "class_type": "UL_AnyTextEncoder"
      },
      "52": {
          "inputs": {
              "seed": int(time.time() * 1000) + img_num + 1,
              "steps": 20,
              "cfg": 9.0,
              "strength": 1.0,
              "keep_load": True,
              "keep_device": True,
              "model": ["50", 0],
              "positive": ["51", 0],
              "negative": ["51", 1]
          },
          "class_type": "UL_AnyTextSampler"
      },
      "53": { "inputs": { "samples": ["52", 0], "vae": ["37", 0] }, "class_type": "VAEDecode" },
      
      # 마스크 이미지 로드
      "60": {
          "inputs": { "image": "subtitle_mask.png", "upload": "image" },
          "class_type": "LoadImage"
      },

      "31": { 
          "inputs": { "images": ["53", 0], "filename_prefix": f"Drama48/Scene_{img_num:04d}", "civitai_compatible_metadata": False }, 
          "class_type": "SaveImage //ZImagePowerNodes"
      }
    }
    
    # 에이전트 지시 최적화 적용
    # workflow = optimize_workflow(workflow) # AnyText 추가로 인해 구조 변경됨, 일단 제외
    
    try:
        res = queue_prompt(workflow)
        prompt_id = res['prompt_id']
        
        timeout = 180 # AnyText 추가로 시간 더 필요
        start = time.time()
        while True:
            if time.time() - start > timeout:
                return False
            
            history = get_history(prompt_id)
            if prompt_id in history:
                return True
            time.sleep(1)
    except Exception as e:
        print(f"  ❌ 에러: {e}")
        return False

if __name__ == "__main__":
    import sys
    import os
    
    total_images = int(sys.argv[1]) if len(sys.argv) > 1 else 48
    
    if os.path.exists("/workspace/대본.txt"):
        script_file = "/workspace/대본.txt"
    else:
        script_file = "대본.txt"
    
    print(f"🚀 {total_images}장 드라마 이미지 생성 시작 (AnyText 자막 포함)...")
    
    dynamic_scenes = parse_script(script_file, total_images)
    
    total_start = time.time()
    success_count = 0
    
    for i, scene_data in enumerate(dynamic_scenes):
        img_num = i + 1
        prompt = build_character_prompt(scene_data)
        dialogue = scene_data["dialogue"]
        
        # 대사가 없으면 임의로 채움 (테스트용)
        if not dialogue: dialogue = "......"

        print(f"\n[{img_num}/{total_images}] 장면 생성")
        print(f"  📜 장면: {scene_data['scene'][:50]}...")
        print(f"  💬 자막: {dialogue}")
        
        if generate_image(prompt, dialogue, img_num):
            print(f"  ✅ 완료! (Scene_{img_num:04d})")
            success_count += 1
        else:
            print(f"  ❌ 실패")
    
    total_time = time.time() - total_start
    print(f"\n✅ 완료!")
    print(f"⏱️  총 시간: {total_time:.1f}초")

import json
import urllib.request
import sys
import time

COMFY_URL = "http://127.0.0.1:8188"
WORKFLOW_PATH = "/workspace/runpod-slim/ComfyUI/custom_nodes/ComfyUI-ZImagePowerNodes/workflows/safetensors_versions/z-image_turbo_main_workflow-ST.json"

def queue_prompt(prompt):
    p = {"prompt": prompt}
    data = json.dumps(p).encode('utf-8')
    req = urllib.request.Request(f"{COMFY_URL}/prompt", data=data)
    return json.loads(urllib.request.urlopen(req).read())

def get_history(prompt_id):
    with urllib.request.urlopen(f"{COMFY_URL}/history/{prompt_id}") as response:
        return json.loads(response.read())

def workflow_to_api(workflow):
    """워크플로우 JSON을 API 포맷으로 변환"""
    api_prompt = {}
    for node in workflow.get("nodes", []):
        node_id = str(node["id"])
        api_prompt[node_id] = {
            "class_type": node["type"],
            "inputs": {}
        }
        
        # inputs 처리
        if "inputs" in node:
            for inp in node["inputs"]:
                if "link" in inp and inp["link"] is not None:
                    # 링크된 입력은 나중에 처리
                    pass
        
        # widgets_values를 inputs로 매핑
        if "widgets_values" in node and node["widgets_values"]:
            # 노드 타입별로 위젯을 적절한 input 이름으로 매핑
            if node["type"] == "StylePromptEncoder //ZImagePowerNodes":
                # widgets: [visual_technique, style, customization]
                if len(node["widgets_values"]) >= 2:
                    api_prompt[node_id]["inputs"]["style"] = node["widgets_values"][1]
                if len(node["widgets_values"]) >= 3:
                    api_prompt[node_id]["inputs"]["text"] = node["widgets_values"][2]
            elif node["type"] == "EmptyZImageLatentImage //ZImagePowerNodes":
                # widgets: [upscale_to_uhd, ratio, size, batch_size]
                if len(node["widgets_values"]) >= 4:
                    api_prompt[node_id]["inputs"]["landscape"] = node["widgets_values"][0]
                    api_prompt[node_id]["inputs"]["ratio"] = node["widgets_values"][1]
                    api_prompt[node_id]["inputs"]["size"] = node["widgets_values"][2]
                    api_prompt[node_id]["inputs"]["batch_size"] = node["widgets_values"][3]
            elif node["type"] == "ZSamplerTurbo //ZImagePowerNodes":
                # widgets: [batch_size, seed_mode, seed, steps]
                if len(node["widgets_values"]) >= 4:
                    api_prompt[node_id]["inputs"]["batch_size"] = node["widgets_values"][0]
                    api_prompt[node_id]["inputs"]["seed"] = node["widgets_values"][2]
                    api_prompt[node_id]["inputs"]["steps"] = node["widgets_values"][3]
    
    # 링크 처리
    for link in workflow.get("links", []):
        # link: [link_id, source_node, source_slot, target_node, target_slot, type]
        if len(link) >= 5:
            target_node = str(link[3])
            source_node = str(link[1])
            source_slot = link[2]
            
            # target_node의 inputs에서 해당 슬롯에 맞는 이름 찾기
            if target_node in api_prompt:
                target_node_data = workflow["nodes"][int(target_node) - 1] if int(target_node) <= len(workflow["nodes"]) else None
                if target_node_data and "inputs" in target_node_data:
                    for inp in target_node_data["inputs"]:
                        if inp.get("link") == link[0]:
                            api_prompt[target_node]["inputs"][inp["name"]] = [source_node, source_slot]
                            break
    
    return api_prompt

def test_gen(user_prompt):
    print(f"🎨 Z-Image Turbo 생성 (워크플로우 기반): {user_prompt}")
    
    # 워크플로우 로드
    with open(WORKFLOW_PATH, 'r') as f:
        workflow = json.load(f)
    
    # API 포맷으로 변환
    api_prompt = workflow_to_api(workflow)
    
    # 프롬프트 텍스트 교체 (노드 42가 StylePromptEncoder)
    if "42" in api_prompt:
        api_prompt["42"]["inputs"]["text"] = user_prompt
    
    print(f"📤 API 페이로드 생성 완료 (노드 수: {len(api_prompt)})")
    
    try:
        res = queue_prompt(api_prompt)
        prompt_id = res['prompt_id']
        print(f"🚀 큐 등록 완료 (ID: {prompt_id})")
        
        start_time = time.time()
        while True:
            history = get_history(prompt_id)
            if prompt_id in history:
                print("✅ 생성 성공!")
                print(f"📂 출력: /workspace/runpod-slim/ComfyUI/output/ZImage/")
                break
            
            if time.time() - start_time > 120:
                print("⏳ 타임아웃")
                break
                
            time.sleep(2)
    except Exception as e:
        print(f"❌ 실패: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    p = sys.argv[1] if len(sys.argv) > 1 else "A beautiful cyberpunk girl with neon hair, cinematic, 8k"
    test_gen(p)

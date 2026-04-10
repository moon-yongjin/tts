import urllib.request
import urllib.parse
import json
import sys
import time
import uuid

# ==========================================
# 1. Config
# ==========================================
SERVER_ADDRESS = "w4kbyfstjq0vvy-8188.proxy.runpod.net"
WORKFLOW_FILE = "/Users/a12/projects/tts/core_v2/LTX_TURBO_I2V_API.json"

# ==========================================
# 2. Helper Logic
# ==========================================
def clean_workflow(workflow):
    new_workflow = {}
    id_map = {}
    for old_id in workflow.keys():
        new_id = old_id.replace(":", "_")
        id_map[old_id] = new_id
        new_workflow[new_id] = workflow[old_id]
    for node in new_workflow.values():
        if "inputs" in node:
            for key, val in node["inputs"].items():
                if isinstance(val, list) and len(val) >= 1:
                    target_id = str(val[0])
                    if target_id in id_map:
                        val[0] = id_map[target_id]
    return new_workflow

def upload_image(filename):
    """Downloads from output and uploads to input so ComfyUI can use it."""
    try:
        # Download from view
        print(f"   Downloading '{filename}' from RunPod output...")
        url = f"https://{SERVER_ADDRESS}/view?filename={urllib.parse.quote(filename)}&type=output"
        req = urllib.request.Request(url)
        # Bypassing 403 Forbidden
        req.add_header("User-Agent", "Mozilla/5.0")
        img_data = urllib.request.urlopen(req).read()

        # Upload to /upload/image
        print(f"   Uploading '{filename}' back to RunPod input...")
        boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
        body = (
            f'--{boundary}\r\n'
            f'Content-Disposition: form-data; name="image"; filename="{filename}"\r\n'
            f'Content-Type: image/png\r\n\r\n'
        ).encode('utf-8') + img_data + f'\r\n--{boundary}--\r\n'.encode('utf-8')
        
        req_up = urllib.request.Request(f"https://{SERVER_ADDRESS}/upload/image", data=body)
        req_up.add_header('Content-type', f'multipart/form-data; boundary={boundary}')
        req_up.add_header("User-Agent", "Mozilla/5.0")
        res = urllib.request.urlopen(req_up)
        return json.loads(res.read())['name']
    except Exception as e:
        print(f"❌ Upload Error: {e}")
        return filename # Fallback

def queue_prompt(prompt):
    p = {"prompt": prompt}
    data = json.dumps(p).encode('utf-8')
    req = urllib.request.Request(f"https://{SERVER_ADDRESS}/prompt", data=data)
    req.add_header("Content-Type", "application/json")
    req.add_header("User-Agent", "Mozilla/5.0")
    try:
        response = urllib.request.urlopen(req)
        result = json.loads(response.read())
        print(f"✅ Success! Prompt ID: {result['prompt_id']}")
        return result['prompt_id']
    except Exception as e:
        print(f"❌ Error queuing prompt: {e}")
        if hasattr(e, 'read'):
            print(f"   Response: {e.read().decode('utf-8')}")
        return None

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python comfy_ltx_video_gen.py <input_image_name> \"<video_prompt>\"")
        sys.exit(1)

    input_img = sys.argv[1]
    prompt_text = sys.argv[2]
    
    # 1. Upload image to input folder
    uploaded_name = upload_image(input_img)

    # 2. Load workflow
    with open(WORKFLOW_FILE, "r", encoding="utf-8") as f:
        workflow = json.load(f)

    workflow = clean_workflow(workflow)

    # Inject
    workflow["98"]["inputs"]["image"] = uploaded_name
    workflow["92_3"]["inputs"]["text"] = prompt_text
    workflow["92_11"]["inputs"]["noise_seed"] = int(time.time() * 1000) % 1000000000

    print(f"🚀 Sending Image-to-Video request...")
    queue_prompt(workflow)

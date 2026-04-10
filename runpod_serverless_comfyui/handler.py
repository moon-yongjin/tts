import os
import time
import json
import base64
import urllib.request
import urllib.error
import runpod

COMFYUI_URL = "http://127.0.0.1:8188"

def check_comfyui_ready():
    """Wait for ComfyUI to start up and be responsive (up to 120s)."""
    retries = 120  # ZImagePowerNodes clone + ComfyUI boot can take up to ~60s
    while retries > 0:
        try:
            req = urllib.request.Request(f"{COMFYUI_URL}/system_stats")
            with urllib.request.urlopen(req, timeout=3) as response:
                if response.status == 200:
                    print(f"ComfyUI is ready! ({120 - retries}s elapsed)")
                    return True
        except Exception:
            pass
        time.sleep(1)
        retries -= 1
        if retries % 10 == 0:
            print(f"Still waiting for ComfyUI... ({120 - retries}s elapsed)")
    return False

def queue_prompt(prompt_workflow):
    """Queue the prompt to ComfyUI."""
    data = json.dumps({"prompt": prompt_workflow}).encode('utf-8')
    req = urllib.request.Request(f"{COMFYUI_URL}/prompt", data=data, headers={'Content-Type': 'application/json'})
    
    with urllib.request.urlopen(req) as response:
        result = json.loads(response.read().decode('utf-8'))
        return result['prompt_id']

def get_history(prompt_id):
    """Wait for the prompt to finish and get history (up to 300s)."""
    timeout = 300
    start = time.time()
    while time.time() - start < timeout:
        try:
            req = urllib.request.Request(f"{COMFYUI_URL}/history/{prompt_id}")
            with urllib.request.urlopen(req) as response:
                history = json.loads(response.read().decode('utf-8'))
                if prompt_id in history:
                    return history[prompt_id]
        except urllib.error.HTTPError as e:
            if e.code != 404:
                raise
        time.sleep(2)
    raise TimeoutError(f"Generation timed out after {timeout}s for prompt_id: {prompt_id}")

def get_image(filename, subfolder, folder_type):
    """Download the generated image from ComfyUI."""
    url = f"{COMFYUI_URL}/view?filename={filename}&subfolder={subfolder}&type={folder_type}"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as response:
        return response.read()

def handler(job):
    """RunPod Serverless Handler function."""
    job_input = job['input']
    
    # Check if a custom workflow is provided, otherwise expect error
    if 'workflow' not in job_input:
        return {"error": "Missing 'workflow' in input. Provide a complete ComfyUI prompt JSON."}
        
    prompt_workflow = job_input['workflow']

    if not check_comfyui_ready():
        return {"error": "ComfyUI failed to start or is unresponsive."}

    try:
        # Submit the job to ComfyUI
        prompt_id = queue_prompt(prompt_workflow)
        
        # Wait for the job to finish
        history = get_history(prompt_id)
        
        images_output = []
        outputs = history.get('outputs', {})
        for node_id, node_output in outputs.items():
            if 'images' in node_output:
                for image in node_output['images']:
                    image_data = get_image(image['filename'], image.get('subfolder', ''), image.get('type', 'output'))
                    base64_img = base64.b64encode(image_data).decode('utf-8')
                    images_output.append(f"data:image/png;base64,{base64_img}")
        
        return {"images": images_output}
        
    except Exception as e:
        return {"error": f"Generation failed: {str(e)}"}

if __name__ == '__main__':
    runpod.serverless.start({"handler": handler})

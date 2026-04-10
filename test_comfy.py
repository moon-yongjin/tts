import json
import urllib.request
import urllib.parse
import os
import time

def queue_prompt(prompt):
    p = {"prompt": prompt}
    data = json.dumps(p).encode('utf-8')
    req = urllib.request.Request("http://127.0.0.1:8188/prompt", data=data)
    return json.loads(urllib.request.urlopen(req).read())

def get_history(prompt_id):
    with urllib.request.urlopen(f"http://127.0.0.1:8188/history/{prompt_id}") as response:
        return json.loads(response.read())

def get_image(filename, subfolder, folder_type):
    data = {"filename": filename, "subfolder": subfolder, "type": folder_type}
    url_values = urllib.parse.urlencode(data)
    with urllib.request.urlopen(f"http://127.0.0.1:8188/view?{url_values}") as response:
        return response.read()

def generate_image(workflow, prompt_text):
    # Update prompt in workflow (Id 6 in the JSON I saw)
    workflow["6"]["inputs"]["text"] = prompt_text
    
    # Randomize seed to avoid cache
    import random
    seed = random.randint(0, 0xffffffffffffffff)
    if "3" in workflow: workflow["3"]["inputs"]["seed"] = seed
    if "10" in workflow: workflow["10"]["inputs"]["seed"] = seed
    
    # Queue the work
    prompt_id = queue_prompt(workflow)['prompt_id']
    print(f"Queued prompt: {prompt_id}")
    
    while True:
        history = get_history(prompt_id)
        if prompt_id in history:
            break
        time.sleep(1)
    
    history = history[prompt_id]
    images = []
    for node_id in history['outputs']:
        node_output = history['outputs'][node_id]
        if 'images' in node_output:
            for image in node_output['images']:
                images.append(image)
    
    return images

if __name__ == "__main__":
    # Load workflow
    workflow_path = "/Users/a12/telegram_bot/ComfyUI/comfy_shima_workflow.json"
    with open(workflow_path, "r") as f:
        workflow = json.load(f)
    
    prompt = "score_9, score_8_up, (art by Hirokane Kenshi:1.2), mature male, 40s, salaryman, business suit, sharp eyes, serious expression, office background, film grain"
    print(f"Generating image with prompt: {prompt}")
    
    images = generate_image(workflow, prompt)
    
    for i, img in enumerate(images):
        img_data = get_image(img['filename'], img['subfolder'], img['type'])
        output_filename = f"comfy_test_{i}.png"
        with open(output_filename, "wb") as f:
            f.write(img_data)
        print(f"Saved: {output_filename}")

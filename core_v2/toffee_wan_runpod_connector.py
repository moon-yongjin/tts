import requests
import json
import time
import os
import uuid
import random

# ---------------------------------------------------------
# [CONFIG] RunPod ComfyUI Connection Info
# ---------------------------------------------------------
RUNPOD_API_URL = "https://ktshs13vdfmcia-8188.proxy.runpod.net"
CLIENT_ID = str(uuid.uuid4())

def upload_image(image_path):
    """Uploads an image to ComfyUI's /upload/image endpoint."""
    print(f"📤 Uploading: {os.path.basename(image_path)}...")
    url = f"{RUNPOD_API_URL}/upload/image"
    with open(image_path, 'rb') as f:
        files = {'image': (os.path.basename(image_path), f, 'image/png')}
        data = {'overwrite': 'true'}
        response = requests.post(url, files=files, data=data)
        if response.status_code == 200:
            return response.json().get('name')
    return None

def queue_prompt(prompt, custom_name="Chosun_Snack"):
    """Queues a prompt via ComfyUI API with a custom name/client_id for tracking."""
    p = {"prompt": prompt, "client_id": f"{CLIENT_ID}_{custom_name}"}
    response = requests.post(f"{RUNPOD_API_URL}/prompt", json=p)
    if response.status_code == 200:
        return response.json().get('prompt_id')
    return None

def check_and_download(prompt_id, output_path, result_node_id='9'):
    """Polls for completion and downloads the final video/image."""
    print(f"⏳ Polling for result (ID: {prompt_id})...")
    start_time = time.time()
    while time.time() - start_time < 600: # 10 minute timeout
        try:
            res = requests.get(f"{RUNPOD_API_URL}/history/{prompt_id}", timeout=10)
            if res.status_code == 200:
                history = res.json().get(prompt_id)
                if history:
                    outputs = history.get('outputs', {})
                    if result_node_id in outputs:
                        # Depending on node type, look for 'images' or 'videos'
                        if 'videos' in outputs[result_node_id]:
                            media = outputs[result_node_id]['videos'][0]
                        else:
                            media = outputs[result_node_id]['images'][0]
                        
                        filename = media['filename']
                        media_url = f"{RUNPOD_API_URL}/view?filename={filename}&type=output"
                        print(f"🎬 Generation complete. Downloading {filename}...")
                        media_data = requests.get(media_url, timeout=120).content
                        with open(output_path, "wb") as f:
                            f.write(media_data)
                        return True
            time.sleep(5)
        except Exception as e:
            print(f"⚠️ Polling error: {e}")
            time.sleep(5)
    return False

def generate_wan_interpolation(start_img, end_img, prompt, output_filename, workflow_json_path, custom_name="Chosun_Interpolation"):
    """
    Orchestrates the interpolation process with custom naming.
    """
    # 1. Upload
    start_name = upload_image(start_img)
    end_name = upload_image(end_img)
    if not start_name or not end_name:
        print("❌ Image upload failed.")
        return None

    # 2. Load Workflow
    if not os.path.exists(workflow_json_path):
        print(f"❌ Workflow JSON not found: {workflow_json_path}")
        return None
    
    with open(workflow_json_path, 'r', encoding='utf-8') as f:
        workflow = json.load(f)

    # 3. Customize (This part is workflow-dependent)
    for node_id, node_info in workflow.items():
        class_type = node_info.get('class_type')
        
        # LoadImage nodes
        if class_type == "LoadImage":
            if "start" in node_info.get('_meta', {}).get('title', '').lower() or not hasattr(generate_wan_interpolation, 'start_set'):
                node_info['inputs']['image'] = start_name
                generate_wan_interpolation.start_set = True
            else:
                node_info['inputs']['image'] = end_name
        
        # Prompt nodes
        if class_type == "CLIPTextEncode" and "positive" in node_info.get('_meta', {}).get('title', '').lower():
            node_info['inputs']['text'] = prompt
            
        # Seed nodes
        if 'seed' in node_info.get('inputs', {}):
            node_info['inputs']['seed'] = random.randint(1, 1000000000)

    # Reset static var for next call
    if hasattr(generate_wan_interpolation, 'start_set'):
        del generate_wan_interpolation.start_set

    # 4. Queue with custom name
    p_id = queue_prompt(workflow, custom_name=custom_name)
    if p_id:
        print(f"🚀 Prompt queued. ID: {p_id}")
        if check_and_download(p_id, output_filename, result_node_id='9'): # Adjust result_node_id based on workflow
            print(f"✅ Finished: {output_filename}")
            return output_filename
    return None

def stitch_images_in_folder(folder_path, prompt, workflow_json_path, output_dir):
    """
    Takes a folder of images, sorts them, and creates interpolation videos between each pair.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    images = sorted([os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.endswith(".png")])
    if len(images) < 2:
        print("❌ At least 2 images required for stitching.")
        return

    print(f"🚀 [Chained Stitching] Processing {len(images)} images ( {len(images)-1} segments )...")
    
    generated_clips = []
    for i in range(len(images) - 1):
        out_clip = os.path.join(output_dir, f"segment_{i+1:03d}.mp4")
        success = generate_wan_interpolation(images[i], images[i+1], prompt, out_clip, workflow_json_path)
        if success:
            generated_clips.append(out_clip)
        time.sleep(1)

    # Create concat list for FFmpeg
    list_path = os.path.join(output_dir, "concat_list.txt")
    with open(list_path, "w", encoding="utf-8") as f:
        for clip in generated_clips:
            f.write(f"file '{os.path.abspath(clip)}'\n")
    
    print(f"📜 Concat list created: {list_path}")
    return list_path

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--folder", type=str, help="Folder with PNG images")
    parser.add_argument("--prompt", type=str, default="Natural cinematic movement, high quality.", help="Video prompt")
    parser.add_argument("--workflow", type=str, default="core_v2/WAN_22_INTERPOLATION_API.json", help="ComfyUI API JSON path")
    parser.add_argument("--output", type=str, default="/Users/a12/Downloads/Toffee_Wan_RunPod", help="Output directory")
    
    args = parser.parse_args()
    
    if args.folder:
        stitch_images_in_folder(args.folder, args.prompt, args.workflow, args.output)
    else:
        print("💡 Usage: python toffee_wan_runpod_connector.py --folder [image_folder]")

import urllib.request
import json
import uuid
import time

SERVER_ADDRESS = "127.0.0.1:8181"
CLIENT_ID = str(uuid.uuid4())

def queue_prompt(prompt):
    p = {"prompt": prompt, "client_id": CLIENT_ID}
    data = json.dumps(p).encode('utf-8')
    req = urllib.request.Request(f"http://{SERVER_ADDRESS}/prompt", data=data)
    with urllib.request.urlopen(req) as response:
        return json.loads(response.read())

def get_history(prompt_id):
    req = urllib.request.Request(f"http://{SERVER_ADDRESS}/history/{prompt_id}")
    with urllib.request.urlopen(req) as response:
        return json.loads(response.read())

def main():
    # Exact prompt from Civitai for the subway girl image
    prompt_text = (
        "这是一张充满日系亚文化与地铁日常感的真实自拍照片（疑似手机竖拍），拍摄于东京地铁车厢内，背景是典型的紫黄色调车厢（疑似都营大江户线或类似线路），车门玻璃反射出站台标识“寺尾達”（Teraodachi站）。"
        "主角是一位约20-25岁的可爱日本女孩（或coser），身材纤细高挑，皮肤白皙，五官精致甜美。她cos的是带有哥特+水手服元素的原创或混搭角色：超长直黑发及腰，前刘海齐眉，头顶扎着红色蝴蝶结，戴黑色蕾丝颈圈。妆容偏病娇风：大眼睛画着红色眼影+细长眼线，睫毛纤长，嘴唇涂着亮泽의 裸粉或豆沙色，表情冷艳中带点俏皮，微微歪头看向镜头，嘴角含笑，像在故意撩拨观众。"
        "她穿着改装版水手服+哥特风外套：灰色军装式短外套（肩部有红色十字装饰，袖子破洞露肩），内搭经典蓝白水手服（领结红色，胸前大蝴蝶结），超短海军蓝百褶裙（裙摆短到大腿根，露出白色过膝袜和黑色乐福鞋）。外套敞开，露出纤细腰肢和锁骨，整体造型既清纯又性感，裙底风光若隐若现。"
        "她单手扶着车厢扶手，另一手举着手机自拍，身体微微侧倾，一条腿自然弯曲踩在车厢地面，另一条腿伸直，黑色乐福鞋脱在一旁，露出白袜包裹的脚踝。车厢内光线明亮，荧光灯+窗外隧道灯光交织在她脸上 and 身上，形成柔和高光与阴影对比。背景模糊可见空荡车厢、黄色扶手和站台标牌，整个画面透出地铁coser常见的“通勤即舞台”의 私密与大胆感，带着一丝青春叛逆与可爱撩人的张力，像深夜地铁里最吸睛的一瞬。"
        "A Dark artistic logo in the upper center of the screen that reads 'DarkBeastZ Blitz6 FP32' , 右下角精致极小字体标注“based on BEYOND REALITY3 超越真实3”"
    )
    
    print(f"🚀 [Civitai Reproduction] Dark Beast LoRA + Z-Image Base 생성 시작")

    workflow = {
        "1": {
            "inputs": {"unet_name": "z_image_bf16.safetensors", "weight_dtype": "default"},
            "class_type": "UNETLoader"
        },
        "2": {
            "inputs": {"clip_name": "qwen_3_4b_fp8_mixed.safetensors", "type": "lumina2"},
            "class_type": "CLIPLoader"
        },
        "3": {
            "inputs": {"vae_name": "ae.safetensors"},
            "class_type": "VAELoader"
        },
        "10": {
            "inputs": {
                "lora_name": "dark_beast_zit_final.safetensors",
                "strength_model": 1.0,
                "model": ["1", 0]
            },
            "class_type": "LoraLoaderModelOnly"
        },
        "4": {
            "inputs": {"width": 896, "height": 1152, "batch_size": 1}, # Vertical mobile shot aspect
            "class_type": "EmptyLatentImage"
        },
        "5": {
            "inputs": {"text": prompt_text, "clip": ["2", 0]},
            "class_type": "CLIPTextEncode"
        },
        "7": {
            "inputs": {"text": "nsfw, lowres, text, watermark, bad anatomy", "clip": ["2", 0]},
            "class_type": "CLIPTextEncode"
        },
        "6": {
            "inputs": {
                "seed": 650709711001427, # Exact seed from Civitai
                "steps": 8,
                "cfg": 1.0,
                "sampler_name": "euler",
                "scheduler": "simple",
                "denoise": 1.0,
                "model": ["10", 0],
                "positive": ["5", 0],
                "negative": ["7", 0],
                "latent_image": ["4", 0]
            },
            "class_type": "KSampler"
        },
        "8": {
            "inputs": {"samples": ["6", 0], "vae": ["3", 0]},
            "class_type": "VAEDecode"
        },
        "9": {
            "inputs": {"filename_prefix": "DarkBeast_Test", "images": ["8", 0]},
            "class_type": "SaveImage"
        }
    }

    try:
        res = queue_prompt(workflow)
        prompt_id = res['prompt_id']
        print(f"✅ 큐 등록 완료! (ID: {prompt_id})")
        print("⏳ 생성 대기 중...")

        while True:
            history = get_history(prompt_id)
            if prompt_id in history:
                status = history[prompt_id].get('status', {})
                if status.get('status_str') == 'error':
                    msgs = status.get('messages', [])
                    for m in msgs:
                        if m[0] == 'execution_error':
                            print(f"❌ 에러: {m[1].get('exception_message', 'unknown')}")
                    break
                outputs = history[prompt_id].get('outputs', {})
                if outputs:
                    for node_id in outputs:
                        for img in outputs[node_id].get('images', []):
                            print(f"🎉 생성 완료! 파일: {img['filename']}")
                    break
            time.sleep(2)

    except Exception as e:
        print(f"❌ 접속 실패: {e}")

if __name__ == "__main__":
    main()

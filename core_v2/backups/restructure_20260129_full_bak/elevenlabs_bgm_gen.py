import os
import requests

# [설정]
BASE_PATH = os.path.dirname(os.path.abspath(__file__))
BGM_LIB_DIR = os.path.join(BASE_PATH, "Library", "bgm")
ELEVENLABS_API_KEY = "4ac65146a95169cd5530e663dfd89d5b41b05a6d503007f7256861dfc41de97d"

def generate_and_save_to_lib(prompt, filename):
    if not os.path.exists(BGM_LIB_DIR):
        os.makedirs(BGM_LIB_DIR)
        
    output_path = os.path.join(BGM_LIB_DIR, f"{filename}.mp3")
    
    if os.path.exists(output_path):
        print(f"⏩ [Skip] {filename}.mp3 이미 라이브러리에 존재합니다.")
        return

    url = "https://api.elevenlabs.io/v1/sound-generation"
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY, 
        "Content-Type": "application/json"
    }
    data = {
        "text": prompt,
        "duration_seconds": 22.0,
        "prompt_influence": 0.5
    }
    
    print(f"🎵 ElevenLabs로 '{filename}' BGM 제작 중...")
    try:
        resp = requests.post(url, json=data, headers=headers)
        if resp.status_code == 200:
            with open(output_path, "wb") as f:
                f.write(resp.content)
            print(f"✅ 라이브러리 저장 성공: {output_path}")
        else:
            print(f"❌ 생성 실패 ({resp.status_code}): {resp.text}")
    except Exception as e:
        print(f"⚠️ 오류 발생: {e}")

if __name__ == "__main__":
    # 라이브러리 기본 세트 구성
    assets = [
        ("Cinematic tense orchestral background music, fast suspenseful rhythm, dark wuxia atmosphere", "Tense"),
        ("Cinematic serene flute and guzheng melody, peaceful mountain atmosphere, calm wuxia mood", "Calm"),
        ("Cinematic heroic grand orchestral theme, triumphant and powerful wuxia inspiration", "Heroic")
    ]
    
    for prompt, name in assets:
        generate_and_save_to_lib(prompt, name)

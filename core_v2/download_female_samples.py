import os
import requests
from pathlib import Path

# Target Directory
DOWNLOAD_DIR = Path.home() / "Downloads" / "Korean_Voice_Samples"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

FEMALE_VOICES = [
    ("01_Conan_Child.wav", "https://huggingface.co/gahyunlee/GPT-SoVITS-ko-character/resolve/main/examples/conan.wav"),
    ("02_Jjanggu_Unique.wav", "https://huggingface.co/gahyunlee/GPT-SoVITS-ko-character/resolve/main/examples/jjanggu.wav"),
    ("03_Keroro_Energetic.wav", "https://huggingface.co/gahyunlee/GPT-SoVITS-ko-character/resolve/main/examples/keroro.wav"),
    ("04_Nexdata_G0051_Calm.wav", "https://huggingface.co/datasets/Nexdata/Korean_Speech_Data_by_Mobile_Phone_Reading/resolve/main/T0138G0051S0001.wav"),
    ("05_Nexdata_G0097_Adult.wav", "https://huggingface.co/datasets/Nexdata/Korean_Speech_Data_by_Mobile_Phone_Reading/resolve/main/T0138G0097S0006.wav"),
    ("06_Nexdata_G0133_Mature.wav", "https://huggingface.co/datasets/Nexdata/Korean_Speech_Data_by_Mobile_Phone_Reading/resolve/main/T0139G0133S0001.wav"),
    ("07_Nexdata_G0141_Fast.wav", "https://huggingface.co/datasets/Nexdata/Korean_Speech_Data_by_Mobile_Phone_Reading/resolve/main/T0139G0141S0001.wav"),
    ("08_Nexdata_G1042_Guide.wav", "https://huggingface.co/datasets/Nexdata/Korean_Speech_Data_by_Mobile_Phone_Guiding/resolve/main/T0137G1042S0403.wav"),
    ("09_Nexdata_O1_0021_Conversation.wav", "https://huggingface.co/datasets/Nexdata/Korean_Conversational_Speech_Data_by_Mobile_Phone/resolve/main/cel_O1_0021.wav"),
    ("10_Nexdata_O2_0049_Casual.wav", "https://huggingface.co/datasets/Nexdata/Korean_Conversational_Speech_Data_by_Mobile_Phone/resolve/main/cel_O2_0049.wav")
]

def download_files():
    print(f"🚀 Starting download of 10 female voice samples to {DOWNLOAD_DIR}...")
    for name, url in FEMALE_VOICES:
        target_path = DOWNLOAD_DIR / name
        print(f"📥 Downloading: {name}...")
        try:
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()
            with open(target_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            print(f"   ✅ Done: {name}")
        except Exception as e:
            print(f"   ❌ Failed {name}: {e}")

if __name__ == "__main__":
    download_files()

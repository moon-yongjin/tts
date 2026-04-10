import os
import shutil
import time
from gradio_client import Client
from pathlib import Path
import pydub # Assuming pydub is available or can be used for concatenation

# Configuration
SPACE_ID = "Qwen/Qwen3-TTS"
SCRIPT_PATH = Path("/Users/a12/projects/tts/대본.txt")
DOWNLOAD_DIR = Path.home() / "Downloads"
OUTPUT_FILENAME = "qwen3_tts_serena_arrogant.wav"
OUTPUT_PATH = DOWNLOAD_DIR / OUTPUT_FILENAME

def split_text(text, max_len=200):
    # Simple split by punctuation
    sentences = text.replace(" , ", ".\n").split("\n")
    chunks = []
    current_chunk = ""
    for s in sentences:
        if len(current_chunk) + len(s) < max_len:
            current_chunk += s + " "
        else:
            chunks.append(current_chunk.strip())
            current_chunk = s + " "
    if current_chunk:
        chunks.append(current_chunk.strip())
    return chunks

def generate_qwen3_tts_chunked():
    if not SCRIPT_PATH.exists():
        print(f"❌ Error: Script file not found at {SCRIPT_PATH}")
        return

    with open(SCRIPT_PATH, "r", encoding="utf-8") as f:
        text_content = f.read().strip()

    if not text_content:
        print("❌ Error: Script file is empty.")
        return

    chunks = split_text(text_content)
    print(f"🚀 [Qwen3-TTS] Splitting into {len(chunks)} chunks...")

    audio_files = []
    client = Client(SPACE_ID)

    for i, chunk in enumerate(chunks):
        print(f"🎙️ Generating chunk {i+1}/{len(chunks)}: \"{chunk[:30]}...\"")
        success = False
        retries = 3
        while not success and retries > 0:
            try:
                result = client.predict(
                    text=chunk,
                    language="Korean",
                    speaker="Serena",
                    instruct="Speak in an arrogant, sharp, and high-tone voice, like a wealthy young woman.",
                    model_size="0.6B",
                    api_name="/generate_custom_voice"
                )
                
                audio_temp_path = result[0]
                if audio_temp_path and os.path.exists(audio_temp_path):
                    chunk_path = DOWNLOAD_DIR / f"chunk_{i}.wav"
                    shutil.copy(audio_temp_path, chunk_path)
                    audio_files.append(chunk_path)
                    print(f"✅ Chunk {i+1} success.")
                    success = True
                else:
                    print(f"⚠️ Chunk {i+1} failed result: {result}")
                    retries -= 1
                    time.sleep(10)
            except Exception as e:
                print(f"⚠️ Exception on chunk {i+1}: {e}")
                retries -= 1
                time.sleep(10)
        
        if not success:
            print(f"❌ Failed to generate chunk {i+1} after retries.")
            return

    # Concatenate audio files using simple binary append if they are WAV with same params?
    # Better to use pydub if possible, or just notify user about chunks if pydub is missing.
    # Let's try to check if pydub is installed.
    print(f"🔗 Concatenating {len(audio_files)} files...")
    
    try:
        from pydub import AudioSegment
        combined = AudioSegment.empty()
        for f in audio_files:
            combined += AudioSegment.from_wav(f)
        combined.export(OUTPUT_PATH, format="wav")
        print(f"🎉 Success: Full audio saved to {OUTPUT_PATH}")
        
        # Cleanup chunks
        for f in audio_files:
            os.remove(f)
            
    except ImportError:
        print("⚠️ pydub not found. Saving chunks individually or using ffmpeg.")
        # Fallback to ffmpeg if pydub is missing
        chunk_list = "|".join([str(f) for f in audio_files])
        os.system(f"ffmpeg -i 'concat:{chunk_list}' -acodec copy {OUTPUT_PATH} -y")
        print(f"✅ Attempted concatenation via ffmpeg. Saved to {OUTPUT_PATH}")

if __name__ == "__main__":
    generate_qwen3_tts_chunked()

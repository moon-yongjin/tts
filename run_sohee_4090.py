
import os
import sys
import torch
import soundfile as sf
import re
from datetime import datetime

# Add qwen_tts to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from qwen_tts import Qwen3TTSModel

# [Configuration]
MODEL_ID = "Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice"
SPEAKER = "sohee"
INSTRUCT = "An extremely breathy and airy voice of a 40-year-old woman. The tone is solemn, tragic, and grave, as if speaking with a heavy heart."
OUTPUT_DIR = "/workspace/Qwen3-TTS/output_sohee"
SCRIPT_FILE = "/workspace/Qwen3-TTS/대본.txt"

os.makedirs(OUTPUT_DIR, exist_ok=True)

def clean_text(text):
    # Basic cleanup for TTS
    text = re.sub(r'\[.*?\]', '', text) # Remove [BGM], [SFX] etc.
    text = re.sub(r'\(.*?\)', '', text)
    return text.strip()

def split_text(text, chunk_size=150):
    sentences = re.split(r'(?<=[.!?])\s+', text)
    chunks = []
    current_chunk = ""
    for sentence in sentences:
        if len(current_chunk) + len(sentence) < chunk_size:
            current_chunk += " " + sentence
        else:
            chunks.append(current_chunk.strip())
            current_chunk = sentence
    if current_chunk:
        chunks.append(current_chunk.strip())
    return chunks

def main():
    print(f"🚀 Starting Sohee Voice Generation on RTX 4090...")
    
    if not os.path.exists(SCRIPT_FILE):
        print(f"❌ Script file not found: {SCRIPT_FILE}")
        return

    with open(SCRIPT_FILE, 'r', encoding='utf-8') as f:
        full_text = f.read()

    chunks = split_text(full_text)
    print(f"📄 Loaded script. Split into {len(chunks)} chunks.")

    print("📡 Loading Model...")
    try:
        model = Qwen3TTSModel.from_pretrained(
            MODEL_ID,
            torch_dtype=torch.float16, # Use float16 for stability if bfloat16 issues
            device_map="cuda"
        )
        print("✅ Model Loaded!")
    except Exception as e:
        print(f"❌ Model Load Error: {e}")
        return

    print("🎤 Generating Audio...")
    
    # Process 5 chunks at a time (Batch 5)
    BATCH_SIZE = 5
    
    for i in range(0, len(chunks), BATCH_SIZE):
        batch = chunks[i:i+BATCH_SIZE]
        cleaned_batch = [clean_text(c) for c in batch]
        
        print(f"   Processing Batch {i//BATCH_SIZE + 1} ({len(batch)} chunks)...")
        
        try:
            wavs, sr = model.generate_custom_voice(
                text=cleaned_batch,
                speaker=SPEAKER,
                language="Korean",
                instruct=INSTRUCT
            )
            
            for j, wav in enumerate(wavs):
                idx = i + j
                filename = f"sohee_{idx:04d}.wav"
                path = os.path.join(OUTPUT_DIR, filename)
                sf.write(path, wav, sr)
                print(f"      💾 Saved: {filename}")
                
        except Exception as e:
            print(f"      ❌ Batch Error: {e}")

    print("✨ All done!")

if __name__ == "__main__":
    main()

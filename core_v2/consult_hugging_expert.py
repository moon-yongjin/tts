import os
import sys
from pathlib import Path

# Add project root to path for imports
PROJ_ROOT = Path("/Users/a12/projects/tts")
sys.path.append(str(PROJ_ROOT))

try:
    from Ollama_Studio.llm_router import ask_huggingface
except ImportError:
    print("❌ llm_router import failed.")
    sys.exit(1)

def consult_expert():
    print("🧠 Consulting 'Hugging Writer' (Llama-3-70B) for ACE-Step API details...")
    
    question = """
    You are an expert in AI Music Generation and the ACE-Step v1.5 model.
    The user is running ACE-Step v1.5 locally on port 7861 (Gradio).
    
    Current task: Generate a 30-second 'K-Funk' (Funk + Korean fusion) BGM at 85 BPM.
    
    Please provide the exact Python code using `gradio_client` to call the local API.
    Specifically, I need the correct list of arguments for `client.predict(...)`.
    
    The local ACE-Step v1.5 Gradio interface typically has many parameters:
    audio_duration, prompt, lyrics, infer_step, guidance_scale, scheduler_type, etc.
    
    Provide the code snippet that will work perfectly for local generation.
    """
    
    try:
        answer = ask_huggingface(question)
        print("\n📜 --- Hugging Writer's Expert Advice ---")
        print(answer)
        print("------------------------------------------\n")
        
        # Save to temporary file for reference
        with open("/tmp/ace_step_expert_advice.txt", "w", encoding="utf-8") as f:
            f.write(answer)
            
    except Exception as e:
        print(f"❌ Consultation failed: {e}")

if __name__ == "__main__":
    consult_expert()

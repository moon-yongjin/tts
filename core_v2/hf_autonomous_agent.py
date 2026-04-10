import os
import sys
import json
import time
import re
from pathlib import Path

# Add project root to path for imports
PROJ_ROOT = Path("/Users/a12/projects/tts")
sys.path.append(str(PROJ_ROOT))

try:
    from Ollama_Studio.llm_router import ask_huggingface
except ImportError:
    print("❌ llm_router import failed.")
    sys.exit(1)

PENDING_FILE = PROJ_ROOT / "core_v2" / "pending_proposals.json"
MAX_QUOTA_SECONDS = 25 * 60
START_TIME = time.time()

def get_repo_summary():
    summary = []
    for root, dirs, files in os.walk(PROJ_ROOT):
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', 'venv', '__pycache__']]
        rel_path = os.path.relpath(root, PROJ_ROOT)
        if rel_path == ".": rel_path = ""
        for file in files:
            if file.endswith(('.py', '.sh', '.command', '.txt', '.json')):
                summary.append(os.path.join(rel_path, file))
    return "\n".join(summary[:150])

def run_agent():
    print("🚀 [Proposal Agent] Generating Project Improvement Proposals...")
    
    elapsed = time.time() - START_TIME
    if elapsed > MAX_QUOTA_SECONDS:
        print("🛑 Quota exceeded.")
        return

    repo_context = get_repo_summary()
    
    prompt = f"""
    You are a Senior AI Architect for the 'tts' project.
    Your task is to propose 3-5 DISTINCT and HIGH-VALUE improvements to the codebase.
    
    ### [Repository Structure]
    {repo_context}
    
    ### [Task]
    Analyze the project structure and suggest 2-3 small, specific, and safe improvements.
    
    ### [CRITICAL SAFETY RULES]
    1. **NEW FILE ONLY**: Every proposal must be a NEW file. NEVER suggest modifying an existing file.
    2. **COMMAND FILES ARE SACRED**: NEVER move, modify, or delete any file ending in `.command` or `.sh`.
    3. **NO ARCHIVING**: Do not suggest moving existing files.
    
    ### [Mandatory Response Format]
    Provide the output in a single RAW JSON list. 
    IMPORTANT: Use \\\\n for newlines and \\\\" for internal quotes in the 'new_content' string.
    [
        {{
            "id": 1,
            "name": "Short Name",
            "reasoning": "Why this is useful",
            "file_path": "Absolute path to a NEW file",
            "action": "CREATE_ONLY",
            "new_content": "Full code content"
        }}
    ]
    """
    
    try:
        print("🧠 Consulting Llama-3-70B for multiple proposals...")
        response_text = ask_huggingface(prompt)
        
        start_idx = response_text.find('[')
        end_idx = response_text.rfind(']')
        if start_idx == -1 or end_idx == -1:
            print("❌ Failure: Invalid JSON format from LLM.")
            return

        proposals = json.loads(response_text[start_idx:end_idx+1])
        
        with open(PENDING_FILE, "w", encoding="utf-8") as f:
            json.dump(proposals, f, indent=4, ensure_ascii=False)
            
        print(f"✅ Success! {len(proposals)} proposals saved to {PENDING_FILE.name}")
        print("\n--- Current Proposals ---")
        for p in proposals:
            print(f"[{p['id']}] {p['name']} - {p['file_path']}")
            
    except Exception as e:
        print(f"❌ Proposal Generation Failed: {e}")

if __name__ == "__main__":
    run_agent()

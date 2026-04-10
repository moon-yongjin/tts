import os
import sys
import json
from pathlib import Path

# Add project root to path for imports
PROJ_ROOT = Path("/Users/a12/projects/tts")
sys.path.append(str(PROJ_ROOT))

try:
    from Ollama_Studio.llm_router import ask_huggingface
except ImportError:
    print("❌ llm_router import failed.")
    sys.exit(1)

SCRIPT_FILE = PROJ_ROOT / "대본.txt"
LEARNED_FILE = PROJ_ROOT / "core_v2" / "learned_patterns.json"

def run_mentor():
    print("🧠 Starting Hugging Face Autonomous Mentor (Llama-3-70B)...")
    
    # 1. Load Content
    content = ""
    if SCRIPT_FILE.exists():
        with open(SCRIPT_FILE, "r", encoding="utf-8") as f:
            content = f.read()
    
    # 2. Prepare Prompt
    prompt = f"""
    You are an Autonomous AI Mentor for a Short-form Video Production project called 'tts'.
    
    ### [Context]
    The user is creating high-impact, emotional/humorous Korean short-form content (YouTube Shorts/TikTok style).
    They have a system with:
    - Zero-shot voice cloning
    - Background music mixing
    - Automated video segment generation (partially implemented)
    
    ### [Task 1: Content Audit]
    Below is the latest script (Korean). 
    1. Evaluate its 'Hook' and 'Viral Potential'.
    2. Suggest a more provocative or emotional Title.
    3. Suggest a 10-word 'Master Rule' for this specific style of story to be used by the AI Director.
    
    [Latest Script]:
    {content}
    
    ### [Task 2: Code/Project Insight]
    The project uses a 'SelfLearningBrain' and 'ScenarioBrain'. 
    Suggest ONE innovative feature that would make this project 'next-level' (e.g., auto-dubbing, real-time feedback loop, etc.).
    
    ### [Format]
    Provide the output in RAW JSON format only. DO NOT include any markdown code blocks like ```json.
    Ensure all strings are properly escaped.
    {{
        "content_audit": {{
            "viral_score_1_10": 0,
            "title_recommendation": "String",
            "improvement_tip": "String",
            "master_rule": "String"
        }},
        "feature_idea": "String"
    }}
    """
    
    try:
        print("⏳ Sending analysis request to Hugging Face...")
        response_text = ask_huggingface(prompt)
        print("\n📜 [Raw LLM Response]:")
        print(response_text)
        
        # Robust JSON extraction: Find the first '{' and the last '}'
        start_idx = response_text.find('{')
        end_idx = response_text.rfind('}')
        if start_idx != -1 and end_idx != -1:
            json_str = response_text[start_idx:end_idx+1]
            try:
                analysis = json.loads(json_str)
            except json.JSONDecodeError as je:
                print(f"⚠️ JSON parsing failed: {je}. Attempting to fix common issues...")
                # Try to fix unescaped double quotes inside strings (common LLM mistake)
                # This is a very basic fix
                json_str = re.sub(r'(?<!\\)"', r'\"', json_str)
                # Restore structural quotes
                json_str = json_str.replace('\"{', '{').replace('}\"', '}').replace('\":\"', '":"').replace('\":', '":').replace(',\"', ',"')
                analysis = json.loads(json_str)

            print("\n✅ Analysis Successfully Decoded!")
            print(json.dumps(analysis, indent=4, ensure_ascii=False))
            
            # Save to learned_patterns.json
            if not LEARNED_FILE.parent.exists():
                LEARNED_FILE.parent.mkdir(parents=True)
            
            data = {"history": []}
            if LEARNED_FILE.exists():
                try:
                    with open(LEARNED_FILE, "r", encoding="utf-8") as f:
                        existing_data = json.load(f)
                        if isinstance(existing_data, dict):
                            data = existing_data
                            if "history" not in data:
                                data["history"] = []
                except Exception as e:
                    print(f"⚠️ Could not load existing data: {e}. Starting fresh.")
            
            data["history"].append({
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "analysis": analysis
            })
            
            with open(LEARNED_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            
            print(f"✨ Insight saved to {LEARNED_FILE}")
            return analysis
        else:
            print("❌ Could not parse JSON from response.")
            print(response_text)
            
    except Exception as e:
        print(f"❌ Mentor execution failed: {e}")

if __name__ == "__main__":
    import re
    import time
    run_mentor()

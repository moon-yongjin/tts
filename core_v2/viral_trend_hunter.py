import os
import sys
import json
import time
from pathlib import Path

# Add project root to path for imports
PROJ_ROOT = Path("/Users/a12/projects/tts")
sys.path.append(str(PROJ_ROOT))

from Ollama_Studio.llm_router import ask_llm
import reddit_scraper

# --- Configuration ---
INPUT_DIR = os.path.expanduser("~/Downloads/Grok_Video_Input")
os.makedirs(INPUT_DIR, exist_ok=True)

def generate_viral_content():
    print("🕵️‍♂️ [Viral Hunter] Scouting for hot trends on Reddit...")
    
    # 1. Scrape top posts (getting current month's hits)
    # Based on reddit_scraper.py SUBREDDITS
    subreddits = ["interestingasfuck", "BeAmazed", "NextFuckingLevel"]
    all_summaries = []
    
    for sub in subreddits:
        print(f"   -> Scanning r/{sub}...")
        posts = reddit_scraper.get_reddit_posts(sub)
        # Take the top 3 fresh ones
        for post in posts[:3]:
            data = post['data']
            summary = f"Subreddt: r/{sub}\nTitle: {data['title']}\nScore: {data['score']}\n"
            all_summaries.append(summary)
            
    if not all_summaries:
        print("📭 [Viral Hunter] No trends found. Check your internet connection.")
        return

    trend_payload = "\n---\n".join(all_summaries)
    
    # 2. Analyze with HF Llama-3-70B (Brain)
    print("🧠 [Viral Hunter] Sending trends to Llama-3-70B for deep analysis...")
    analysis_prompt = f"""
    [MISSION: ANALYZE VIRAL TRENDS & DRAFT A MASTERPIECE]
    Here are the top trending topics from Reddit today:
    
    {trend_payload}
    
    [TASK]
    1. Identify ONE topic with the highest potential for a 1-minute 'Satisfying/Educational' video.
    2. Explain the 'Psychological Hook' (Why will people watch?).
    3. Write a high-impact script (6-8 scenes).
    4. Provide a 'God-Tier' Grok Image-to-Video prompt for the visual style.
    5. Output the result in JSON format only.
    
    [JSON Format]
    {{
      "topic": "...",
      "hook": "...",
      "script": [
        "Scene 1: ...",
        "Scene 2: ..."
      ],
      "grok_visual_prompt": "...",
      "suggested_filename": "viral_gen_01.png"
    }}
    """
    
    try:
        raw_response = ask_llm(analysis_prompt, role="writer")
        # Extract JSON from response
        json_match = raw_response.split('{', 1)
        if len(json_match) > 1:
            json_str = '{' + json_match[1].rsplit('}', 1)[0] + '}'
            result = json.loads(json_str)
        else:
            print("❌ [Viral Hunter] LLM response was not in JSON format.")
            return

        print(f"🔥 [Viral Hunter] Selected Topic: {result['topic']}")
        print(f"🪝 [Viral Hunter] Hook: {result['hook']}")
        
        # 3. Save to Grok Input Folder
        output_path = os.path.join(INPUT_DIR, result['suggested_filename'])
        # In a real scenario, we might generate/copy an image here. 
        # For now, we save the text metadata so the extension can pick it up or the user can review.
        
        metadata_path = output_path + ".prompt.txt"
        with open(metadata_path, "w", encoding="utf-8") as f:
            f.write(f"PROMPT: {result['grok_visual_prompt']}\n\n")
            f.write(f"SCRIPT:\n" + "\n".join(result['script']))
            
        print(f"✅ [Viral Hunter] Success! Prompt saved to {metadata_path}")
        print("🏎️ [Viral Hunter] Grok Turbo Pro is ready to generate this sequence.")

    except Exception as e:
        print(f"💥 [Viral Hunter] Error during analysis: {e}")

if __name__ == "__main__":
    generate_viral_content()

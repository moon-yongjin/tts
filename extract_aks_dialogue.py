import os
import re

SOURCE_DIR = "/Users/a12/projects/tts/aks_classics"
TARGET_DIR = "/Users/a12/projects/tts/aks_classics_dialogue"

def extract_dialogue():
    if not os.path.exists(TARGET_DIR):
        os.makedirs(TARGET_DIR)
        
    # Pattern for marker-based speakers (#, @)
    marker_pattern = re.compile(r'^\s*([#@][^:]*)\s*:\s*(.*)$')
    # Pattern for text in quotes (direct speech in narration)
    quote_pattern = re.compile(r'["“]([^"“”]*?)["”]')
    # Pattern for investigator prompts in brackets
    bracket_pattern = re.compile(r'\[(.*?)\]')
    
    files_processed = 0
    
    for filename in sorted(os.listdir(SOURCE_DIR)):
        if not filename.endswith(".txt"):
            continue
            
        filepath = os.path.join(SOURCE_DIR, filename)
        target_path = os.path.join(TARGET_DIR, f"pure_{filename}")
        
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        dialogue_turns = []
        is_transcript_body = False
        
        for line in lines:
            line = line.strip()
            if not line: continue

            # Skip until we hit the actual transcript section
            if "채록내용" in line:
                is_transcript_body = True
                continue
            
            if not is_transcript_body:
                continue
                
            # Stop at footer or end of content
            if "사이트 소개" in line or "Copyright" in line or "Family Site" in line:
                break
            
            # 1. Check for marker-based dialogue (#, @)
            match = marker_pattern.match(line)
            if match:
                speaker_marker = match.group(1).strip()
                text = match.group(2).strip()
                dialogue_turns.append(f"{speaker_marker}: {text}")
                continue

            # 2. Check for quotes in narrative-style transcripts
            quotes = quote_pattern.findall(line)
            for q in quotes:
                dialogue_turns.append(f"Dialogue: {q.strip()}")
            
            # 3. Check for investigator prompts/actions in brackets
            brackets = bracket_pattern.findall(line)
            for b in brackets:
                dialogue_turns.append(f"Prompt/Action: {b.strip()}")
        
        if dialogue_turns:
            with open(target_path, 'w', encoding='utf-8') as f:
                f.write("\n".join(dialogue_turns))
            files_processed += 1
            print(f"[{files_processed:02d}] Extracted {len(dialogue_turns)} dialogue items from {filename}")
        else:
            print(f"  No dialogue markers found in {filename} (Content matches narrative style or placeholder)")

if __name__ == "__main__":
    extract_dialogue()

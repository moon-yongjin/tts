import json
import sys
from pathlib import Path

PROJ_ROOT = Path("/Users/a12/projects/tts")
PENDING_FILE = PROJ_ROOT / "core_v2" / "pending_proposals.json"
LEARNED_FILE = PROJ_ROOT / "core_v2" / "learned_patterns.json"

def apply_proposal(proposal_id):
    if not PENDING_FILE.exists():
        print("❌ No pending proposals found.")
        return

    with open(PENDING_FILE, "r", encoding="utf-8") as f:
        proposals = json.load(f)

    target = next((p for p in proposals if p["id"] == proposal_id), None)
    if not target:
        print(f"❌ Proposal ID {proposal_id} not found.")
        return

    target_path = PROJ_ROOT / target["file_path"].lstrip('/')
    
    # Safety Check: Path must be within PROJ_ROOT
    if not str(target_path.resolve()).startswith(str(PROJ_ROOT.resolve())):
        print("⚠️ Safety Rejection: Path outside project root.")
        return

    # User Safety Rule: Do not overwrite existing files
    if target_path.exists():
        print(f"⚠️ Safety Warning: {target_path.name} already exists. Creating a versioned copy...")
        timestamp = time.strftime("%Y%M%S")
        target_path = target_path.with_name(f"{target_path.stem}_improved_{timestamp}{target_path.suffix}")

    print(f"🛠️ Applying '{target['name']}' to {target_path}...")
    target_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(target_path, "w", encoding="utf-8") as f:
        f.write(target["new_content"])
    
    print("✅ Successfully applied change.")

    # Record history
    history_data = {"history": []}
    if LEARNED_FILE.exists():
        with open(LEARNED_FILE, "r", encoding="utf-8") as f:
            try: history_data = json.load(f)
            except: pass
    
    import time
    history_data["history"].append({
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "agent_action": "proposal_applied",
        "proposal_id": proposal_id,
        "name": target["name"]
    })
    
    with open(LEARNED_FILE, "w", encoding="utf-8") as f:
        json.dump(history_data, f, indent=4, ensure_ascii=False)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 apply_proposal.py <proposal_id>")
    else:
        try:
            apply_proposal(int(sys.argv[1]))
        except ValueError:
            print("❌ ID must be an integer.")

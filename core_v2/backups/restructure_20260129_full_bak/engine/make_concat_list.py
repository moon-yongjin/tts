import os
import sys
import re

def create_concat_list(target_dir):
    if not os.path.exists(target_dir):
        print(f"Error: Directory not found: {target_dir}")
        return False

    output_file = os.path.join(target_dir, "mylist.txt")
    
    # Get all mp4 files
    files = [f for f in os.listdir(target_dir) if f.lower().endswith('.mp4') and "합본" not in f]
    
    # Natural sort logic (key function)
    def natural_keys(text):
        return [int(c) if c.isdigit() else c for c in re.split(r'(\d+)', text)]
    
    files.sort(key=natural_keys)
    
    if not files:
        print("No MP4 files found.")
        return False

    with open(output_file, 'w', encoding='utf-8') as f:
        for file in files:
            # Escape single quotes if necessary, though distinct filenames shouldn't have them usually
            safe_name = file.replace("'", "'\\''") 
            f.write(f"file '{safe_name}'\n")
            
    print(f"[OK] Generated clean file list: {output_file} ({len(files)} files)")
    return True

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python make_concat_list.py <target_dir>")
        sys.exit(1)
    
    target_dir = sys.argv[1]
    create_concat_list(target_dir)

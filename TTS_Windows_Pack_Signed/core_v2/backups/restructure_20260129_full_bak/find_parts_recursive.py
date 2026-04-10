import os
d = os.path.join(os.path.expanduser("~"), "Downloads")
found = []
for root, dirs, files in os.walk(d):
    for f in files:
        if "part" in f.lower() and f.endswith((".mp3", ".srt")):
            found.append(os.path.join(root, f))

# Sort by modification time
found.sort(key=lambda x: os.path.getmtime(x), reverse=True)
for f in found[:20]:
    print(f)

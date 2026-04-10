import os
d = os.path.join(os.path.expanduser("~"), "Downloads")
files = [f for f in os.listdir(d) if "part" in f.lower()]
files.sort(key=lambda x: os.path.getmtime(os.path.join(d, x)), reverse=True)
for f in files[:20]:
    print(f)

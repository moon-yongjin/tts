import os
d = os.path.join(os.path.expanduser("~"), "Downloads")
files = os.listdir(d)
# Print latest 50 files
files.sort(key=lambda x: os.path.getmtime(os.path.join(d, x)), reverse=True)
for f in files[:50]:
    print(f)

import re
with open('대본.txt', 'r', encoding='utf-8') as f:
    text = f.read()
# Split by common sentence delimiters
sentences = [s.strip() for s in re.split(r'[.!?\n]', text) if s.strip()]
print(f"Total sentences: {len(sentences)}")
for i, s in enumerate(sentences[:10]):
    print(f"{i}: {s[:50]}...")

with open('c:/Users/tirth/.gemini/antigravity/scratch/groq/output.txt', 'r', encoding='utf-16le', errors='replace') as f:
    text = f.read()
with open('c:/Users/tirth/.gemini/antigravity/scratch/groq/output_utf8.txt', 'w', encoding='utf-8') as f:
    f.write(text)

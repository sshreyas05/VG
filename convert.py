import json

with open("aaahhaa.ipynb", "r", encoding="utf-8") as f:
    nb = json.load(f)

code_cells = [cell["source"] for cell in nb["cells"] if cell["cell_type"] == "code"]
with open("gemma_video_pipeline.py", "w", encoding="utf-8") as f:
    for cell in code_cells:
        for line in cell:
            f.write(line)
        f.write("\n\n")

print("Converted!")

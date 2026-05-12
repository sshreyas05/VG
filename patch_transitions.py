import json

path = 'c:/Users/tirth/OneDrive/Desktop/OSC/aaahhaa.ipynb'

try:
    with open(path, 'r', encoding='utf-8') as f:
        nb = json.load(f)
except Exception as e:
    print(e)
    exit(1)

for cell in nb['cells']:
    if cell['cell_type'] == 'code':
        full_text = "".join(cell['source'])
        if "VISUAL DESIGN REQUIREMENTS" in full_text and "WAN 2.1" not in full_text:
            new_text = full_text.replace(
"""    --------------------------------\n    VISUAL DESIGN REQUIREMENTS\n    --------------------------------\n    - Each clip represents a continuous time progression (~5 seconds each).\n    - The sequence must feel like a smooth camera capture, not disconnected frames.\n    - Maintain:\n    • same characters\n    • same environment (unless gradually changing)\n    • consistent lighting transitions\n    • logical motion flow""", 
"""    --------------------------------\n    VISUAL DESIGN REQUIREMENTS\n    --------------------------------\n    - Each clip represents a continuous time progression (~5 seconds each).\n    - The sequence must feel like a smooth camera capture, not disconnected frames.\n    - WAN 2.1 COMPATIBILITY: Focus on a SINGLE Dominant Motion per clip. \n      • DO NOT describe 3-5 simultaneous actions (e.g. lighting shift + camera arc + character move all at once).\n      • Pick ONE primary action or camera movement for the 5-second clip and keep the rest stable or secondary.\n    - Maintain:\n    • same characters\n    • same environment (unless gradually changing)\n    • consistent lighting\n    • logical motion flow"""
            )
            # Make sure we re-split preserving notebook newline formatting
            # Keep in mind `replace` might not split properly if notebook newlines have '\r' or end with '\n'
            # Let's do a more robust substring replace.
            
            # Re-split to lines:
            lines = new_text.splitlines(True)
            cell['source'] = lines

with open(path, 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=1)

print("Notebook transition prompts updated for WAN 2.1 successfully!")

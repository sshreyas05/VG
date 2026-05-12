import json

path = 'c:/Users/tirth/OneDrive/Desktop/OSC/aaahhaa.ipynb'
try:
    with open(path, 'r', encoding='utf-8') as f:
        nb = json.load(f)
except Exception as e:
    print(e)
    exit(1)

# Ensure modal is imported
source_0 = nb['cells'][0]['source']
if not any('import modal' in line for line in source_0):
    source_0.insert(0, "import modal\n")
for i, line in enumerate(source_0):
    if line.startswith('LLAMA_MODEL'):
        source_0[i] = 'GEMMA_MODEL = "gemma4:31b"\n'
nb['cells'][0]['source'] = source_0

# Rewrite call_model
source_1 = [
    "def call_model(model, prompt):\n",
    "    if 'gemma' in model.lower():\n",
    "        print(f'Calling Modal Gemma: {model}')\n",
    "        OllamaServer = modal.Cls.from_name('ollama-creative-director', 'OllamaServer')\n",
    "        # Pass the prompt as the system_prompt instead so it correctly overrides prompt_enhancer default\n",
    "        return OllamaServer().generate.remote(text='Please process the request according to the system instructions.', model=model, system_prompt=prompt)\n",
    "    else:\n",
    "        print(f'Calling local Ollama: {model}')\n",
    "        response = ollama.chat(\n",
    "            model=model,\n",
    "            messages=[{\"role\": \"user\", \"content\": prompt}]\n",
    "        )\n",
    "        return response[\"message\"][\"content\"]\n"
]
nb['cells'][1]['source'] = source_1

# Replace LLAMA_MODEL -> GEMMA_MODEL everywhere
for cell in nb['cells']:
    if cell['cell_type'] == 'code':
        new_src = []
        for line in cell['source']:
            new_src.append(line.replace('LLAMA_MODEL', 'GEMMA_MODEL'))
        cell['source'] = new_src

# Also add a final cell to run it and save to file as requested:
# "whatever output gemma gives it is stored in a file in the format given in aaahhaa file"
save_cell = {
   "cell_type": "code",
   "execution_count": None,
   "id": "save_to_json_cell",
   "metadata": {},
   "outputs": [],
   "source": [
    "story = \"\"\"\n",
    "A lone hacker investigates a neon-lit alleyway.\n",
    "\"\"\"\n",
    "T = 60\n",
    "# run it\n",
    "output = generate_video_json(story, T)\n",
    "with open('output_gemma.json', 'w', encoding='utf-8') as f:\n",
    "    json.dump(output, f, indent=4)\n",
    "print('Saved to output_gemma.json')\n"
   ]
}
nb['cells'].append(save_cell)

with open(path, 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=1)

print("Notebook patched successfully!")

import os

path = "gemma_video_pipeline.py"

with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# Fix 1: Transitions Prompt WAN 2.1 Compatibility

old_design_req = """    --------------------------------
    VISUAL DESIGN REQUIREMENTS
    --------------------------------
    - Each clip represents a continuous time progression (~5 seconds each).
    - The sequence must feel like a smooth camera capture, not disconnected frames.
    - Maintain:
    • same characters
    • same environment (unless gradually changing)
    • consistent lighting transitions
    • logical motion flow"""

new_design_req = """    --------------------------------
    VISUAL DESIGN REQUIREMENTS
    --------------------------------
    - Each clip represents a continuous time progression (~5 seconds each).
    - The sequence must feel like a smooth camera capture, not disconnected frames.
    - WAN 2.1 COMPATIBILITY: Focus on a SINGLE Dominant Motion per clip.
      • DO NOT describe 3-5 simultaneous actions (e.g. lighting shift + camera arc + character move all at once).
      • Pick ONE primary action or camera movement for the 5-second clip and keep the rest stable or secondary.
    - Maintain:
    • same characters
    • same environment (unless gradually changing)
    • consistent lighting
    • logical motion flow"""

content = content.replace(old_design_req.replace('\n', '\r\n'), new_design_req)
content = content.replace(old_design_req, new_design_req)

# Fix 2: Audio Prompt Metadata Guidelines

old_audio_req = """STRICT REQUIREMENTS
1. Output MUST be valid JSON only.
2. Output MUST contain EXACTLY 4 objects (clip 1 to 4).
3. Each object MUST have:
   - "clip"
   - "music"
   - "sound_effect"
4. No explanations, no extra text outside JSON."""

new_audio_req = """For EACH clip, produce:
- "music": background score description
- "sound_effect": environmental and action-based sounds
- "duration": length of clip in seconds (typically 5.0)
- "dialogue_start": timestamp in seconds when speech begins
- "dialogue_volume": volume level (e.g. 1.0) for dialogue
- "sfx_volume": volume level for SFX
- "music_volume": volume level for music

STRICT REQUIREMENTS
1. Output MUST be valid JSON only.
2. Output MUST contain EXACTLY 4 objects (clip 1 to 4).
3. No explanations, no extra text outside JSON.

DYNAMIC MIXING RULES
- dialogue_start: Determines when speech enters. Music and SFX MUST account for what is happening at that timestamp and leave sonic space for the voice.
- dialogue_volume: Above 1.0 means the music prompt must explicitly describe sitting beneath the dialogue — use words like "underscore," "restrained," "bed".
- sfx_volume: At 1.0 means SFX is the dominant physical layer — describe it with full impact language.
- music_volume: Below 0.5 means music should never be described as "full," "blaring," or "fortissimo" — it is a texture, not a feature.
- duration: Controls total clip length — pacing of all three layers must fit within it.
- Empty dialogue: If dialogue is an empty string for the clip, music and sfx can be described at full intensity with no ducking requirement."""

content = content.replace(old_audio_req.replace('\n', '\r\n'), new_audio_req)
content = content.replace(old_audio_req, new_audio_req)

old_audio_format = """OUTPUT FORMAT

[
  {
    "clip": 1,
    "music": "...",
    "sound_effect": "..."
  },
  {
    "clip": 2,
    "music": "...",
    "sound_effect": "..."
  },
  {
    "clip": 3,
    "music": "...",
    "sound_effect": "..."
  },
  {
    "clip": 4,
    "music": "...",
    "sound_effect": "..."
  }
]"""

new_audio_format = """DIALOGUES (4 clips):
{json.dumps(dialogues, indent=2)}

OUTPUT FORMAT
[
  {{
    "clip": 1,
    "music": "...",
    "sound_effect": "...",
    "duration": 5.0,
    "dialogue_start": 0.0,
    "dialogue_volume": 1.0,
    "sfx_volume": 1.0,
    "music_volume": 0.5
  }},
  {{
    "clip": 2,
    "music": "...",
    "sound_effect": "...",
    "duration": 5.0,
    "dialogue_start": 0.0,
    "dialogue_volume": 1.0,
    "sfx_volume": 1.0,
    "music_volume": 0.5
  }},
  {{
    "clip": 3,
    "music": "...",
    "sound_effect": "...",
    "duration": 5.0,
    "dialogue_start": 0.0,
    "dialogue_volume": 1.0,
    "sfx_volume": 1.0,
    "music_volume": 0.5
  }},
  {{
    "clip": 4,
    "music": "...",
    "sound_effect": "...",
    "duration": 5.0,
    "dialogue_start": 0.0,
    "dialogue_volume": 1.0,
    "sfx_volume": 1.0,
    "music_volume": 0.5
  }}
]"""

# Since `{{` is escaping `{` in f-strings:
old_audio_fmt_in_script = old_audio_format.replace("{", "{{").replace("}", "}}")
content = content.replace(old_audio_fmt_in_script.replace('\n', '\r\n'), new_audio_format)
content = content.replace(old_audio_fmt_in_script, new_audio_format)


# Fix the generate_audio signature to accept dialogues
content = content.replace("def generate_audio(scene, transitions):", "def generate_audio(scene, transitions, dialogues):")

# Fix the sequence inside generate_video_json:
old_sequence = """        print("Generating Audio...")
        audio = generate_audio(desc, transitions)

        print("Extracting Dialogues...")
        dialogues = extract_dialogues(desc, transitions)

        clips = []
        for j in range(4):
            clips.append({
                "clip": j+1,
                "transition_prompt": transitions[j].get("prompt", ""),
                "music": audio[j].get("music", ""),
                "sound_effect": audio[j].get("sound_effect", "")
            })"""

new_sequence = """        print("Extracting Dialogues...")
        dialogues = extract_dialogues(desc, transitions)

        print("Generating Audio...")
        audio = generate_audio(desc, transitions, dialogues)

        clips = []
        for j in range(4):
            clips.append({
                "clip": j+1,
                "transition_prompt": transitions[j].get("prompt", ""),
                "music": audio[j].get("music", ""),
                "sound_effect": audio[j].get("sound_effect", ""),
                "duration": audio[j].get("duration", 5.0),
                "dialogue_start": audio[j].get("dialogue_start", 0.0),
                "dialogue_volume": audio[j].get("dialogue_volume", 1.0),
                "sfx_volume": audio[j].get("sfx_volume", 1.0),
                "music_volume": audio[j].get("music_volume", 0.5)
            })"""

content = content.replace(old_sequence.replace('\n', '\r\n'), new_sequence)
content = content.replace(old_sequence, new_sequence)

with open(path, "w", encoding="utf-8") as f:
    f.write(content)

print("Updated gemma_video_pipeline.py successfully!")

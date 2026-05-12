import modal
import json
import ollama
import re
import time

GEMMA_MODEL = "gemma4:31b"
DEEPSEEK_MODEL = "deepseek-r1:14b"

def call_model(model, prompt):
    if 'gemma' in model.lower():
        print(f'Calling Modal Gemma: {model}')
        OllamaServer = modal.Cls.from_name('ollama-creative-director', 'OllamaServer')
        # Pass the prompt as the system_prompt instead so it correctly overrides prompt_enhancer default
        return OllamaServer().generate.remote(text='Please process the request according to the system instructions.', model=model, system_prompt=prompt)
    else:
        print(f'Calling local Ollama: {model}')
        response = ollama.chat(
            model=model,
            messages=[{"role": "user", "content": prompt}]
        )
        return response["message"]["content"]


def ask_gemma(system_prompt):
    """Convenience wrapper to call the Gemma model with a system prompt."""
    return call_model(GEMMA_MODEL, system_prompt)


def cleanup_json(text):
    text = text.strip()

    if "```" in text:
        parts = text.split("```")
        if len(parts) >= 2:
            text = parts[1]

    start_positions = [i for i in [text.find("{"), text.find("[")] if i != -1]
    if start_positions:
        text = text[min(start_positions):]

    return text

def robust_json_call(prompt, model, retries=3):
    last = None

    for i in range(retries):
        try:
            raw = call_model(model, prompt)
            last = raw
            return json.loads(raw)

        except:
            print(f"JSON failed attempt {i+1}")

            try:
                cleaned = cleanup_json(raw)
                return json.loads(cleaned)
            except:
                pass

            # LLaMA repair
            repair_prompt = f"Fix this JSON and return ONLY JSON:\n{raw}"
            try:
                repaired = call_model(GEMMA_MODEL, repair_prompt)
                return json.loads(cleanup_json(repaired))
            except:
                pass

            # DeepSeek repair
            repair_prompt = f"""
Fix JSON strictly.

{raw}
"""
            try:
                repaired = call_model(DEEPSEEK_MODEL, repair_prompt)
                return json.loads(cleanup_json(repaired))
            except:
                last = repaired

            time.sleep(1)

    raise ValueError("JSON FAILED:\n" + str(last))

def normalize_list(data, key=None):
    if isinstance(data, list):
        return data

    if isinstance(data, dict):
        if key and key in data:
            return data[key]

        return [data[k] for k in sorted(data.keys())]

    raise ValueError("Invalid format")


def ensure_length_4(data, template_key):
    while len(data) < 4:
        data.append({
            "clip": len(data)+1,
            template_key: ""
        })
    return data[:4]

def generate_scenes(story, T):
    n = max(1, round(T / 20))

    prompt = f"""
You are a cinematic story segmentation engine.

TASK:
Divide the given story into EXACTLY {n} scenes, where each scene represents approximately 20 seconds of screen time.

--------------------------------
INPUT
--------------------------------
STORY:
{story}

--------------------------------
STRICT RULES
--------------------------------
1. Output MUST be valid JSON only.
2. Output MUST contain EXACTLY {n} scenes.
3. Each scene MUST have:
   - "scene" (numbered from 1 to {n})
   - "description" (detailed scene description)
4. DO NOT include any extra text outside JSON.

--------------------------------
STORY COVERAGE RULES
--------------------------------
- Cover the ENTIRE story from beginning to end.
- DO NOT skip any important event.
- DO NOT summarize aggressively.
- Maintain full narrative continuity across scenes.

--------------------------------
CHRONOLOGY RULES
--------------------------------
- Scenes MUST be in strict chronological order.
- Each scene should naturally follow the previous one.
- No repetition or overlap of events.

--------------------------------
DIALOGUE RULES
--------------------------------
- Preserve ALL dialogues EXACTLY as written inside "".
- DO NOT paraphrase or modify dialogues.
- DO NOT invent new dialogues.
- Ensure dialogues appear in the correct scene based on context.

--------------------------------
SCENE DETAIL REQUIREMENTS
--------------------------------
Each "description" must include:
- environment and setting
- character actions and positions
- visual progression of events
- emotional tone (visually implied, not explained abstractly)

Avoid vague descriptions like:
  "things happen", "they move forward"

Prefer:
  "the man runs through a narrow rain-soaked alley, glancing back as footsteps echo behind him"

--------------------------------
PACING RULES
--------------------------------
- Each scene should feel like ~20 seconds of screen time.
- Distribute story evenly across {n} scenes.
- Avoid making some scenes too short and others too dense.

--------------------------------
OUTPUT FORMAT
--------------------------------
[
  {{
    "scene": 1,
    "description": "..."
  }},
  {{
    "scene": 2,
    "description": "..."
  }}
]
"""

    return robust_json_call(prompt, GEMMA_MODEL)

def generate_keyframe(scene):
   prompt = f"""
You are a cinematic visual director.

TASK:
Generate the FIRST KEYFRAME of the scene as a highly detailed visual description.

--------------------------------
INPUT
--------------------------------
SCENE:
{scene}

--------------------------------
STRICT RULES
--------------------------------
1. Output ONLY a single paragraph (no JSON, no extra text).
2. Describe ONLY visual elements (NO sound, NO audio).
3. The frame must represent the exact starting moment of the scene.
4. Be highly specific and cinematic.

--------------------------------
VISUAL REQUIREMENTS
--------------------------------
Your description MUST include:

• Camera:
  - angle (wide shot, close-up, over-the-shoulder, etc.)
  - position and perspective
  - lens feel (cinematic, depth of field, focus)

• Lighting:
  - source (natural, artificial, neon, etc.)
  - direction and intensity
  - color tone (warm, cold, high contrast, shadows)

• Environment:
  - location details
  - background elements
  - textures and surfaces

• Characters (if present):
  - appearance (clothing, posture, expression)
  - position in frame
  - subtle motion or stillness

• Composition:
  - foreground, midground, background layering
  - spatial depth and framing

--------------------------------
STYLE GUIDELINES
--------------------------------
- Avoid vague phrases like:
  "a person stands there", "a dark place"

- Use precise cinematic language:
  "a low-angle shot frames the character partially silhouetted against flickering neon reflections on wet asphalt"

- Make the frame feel like a still from a high-quality film.

--------------------------------
OUTPUT
--------------------------------
Return ONLY the paragraph description.
"""
   return call_model(GEMMA_MODEL, prompt)

def generate_transitions(scene, keyframe, next_keyframe):

   prompt = f"""
    You are a cinematic visual sequence designer.

    TASK:
    Generate EXACTLY 4 continuous visual clips that smoothly transform the current scene into the next scene.

    --------------------------------
    INPUTS
    --------------------------------
    SCENE DESCRIPTION:
    {scene}

    CURRENT FIRST FRAME:
    {keyframe}

    NEXT SCENE FIRST FRAME:
    {next_keyframe}

    --------------------------------
    STRICT RULES
    --------------------------------
    1. Output MUST be valid JSON only.
    2. Output MUST contain EXACTLY 4 clips.
    3. Each clip MUST include:
    - "clip" (1 to 4)
    - "prompt" (highly detailed visual description)
    4. DO NOT include any sound or audio details.
    5. DO NOT include explanations or extra text.

    --------------------------------
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
    • logical motion flow

    --------------------------------
    TEMPORAL PROGRESSION
    --------------------------------
    Clip 1:
    - Starts exactly from the CURRENT FIRST FRAME
    - Minimal motion introduced

    Clip 2:
    - Slight movement or camera shift
    - Begin subtle environmental or character changes

    Clip 3:
    - Noticeable transformation toward the NEXT scene
    - Increased motion or transition elements

    Clip 4:
    - Clearly aligns visually with the NEXT SCENE FIRST FRAME
    - Final state should naturally connect into next scene

    --------------------------------
    DETAILING REQUIREMENTS
    --------------------------------
    Each "prompt" must include:
    - camera angle and movement (pan, zoom, tracking, handheld, etc.)
    - lighting (intensity, direction, color tone)
    - environment details (weather, objects, background depth)
    - character appearance and motion
    - spatial relationships and depth

    Avoid vague descriptions like:
    "scene changes", "things move"

    Prefer:
    "camera slowly dollies forward as the character turns their head slightly, neon reflections flickering across wet pavement"

    --------------------------------
    CONTINUITY RULES
    --------------------------------
    - No sudden jumps or discontinuities
    - No new objects or characters appearing abruptly
    - All changes must be gradual and visually justified
    - Ensure clip-to-clip coherence

    --------------------------------
    OUTPUT FORMAT
    --------------------------------
    [
    {{
        "clip": 1,
        "prompt": "..."
    }},
    {{
        "clip": 2,
        "prompt": "..."
    }},
    {{
        "clip": 3,
        "prompt": "..."
    }},
    {{
        "clip": 4,
        "prompt": "..."
    }}
    ]
    """
   transitions = robust_json_call(prompt, GEMMA_MODEL)
   transitions = normalize_list(transitions)

   print("raw transitions:", transitions)

   validate_prompt = f"""
    You are a strict cinematic continuity validator and refiner.

    TASK:
    Analyze and correct the given sequence of 4 visual clips to ensure they form a smooth, continuous transition.

    --------------------------------
    INPUT
    --------------------------------
    {json.dumps(transitions, indent=2)}

    --------------------------------
    STRICT REQUIREMENTS
    --------------------------------
    1. Output MUST be valid JSON only.
    2. Output MUST contain EXACTLY 4 clips.
    3. Each clip MUST have:
    - "clip" (1 to 4)
    - "prompt" (detailed visual description)
    4. DO NOT add extra fields.
    5. DO NOT output explanations.

    --------------------------------
    VALIDATION CRITERIA
    --------------------------------
    Check and FIX the following:

    1. CONTINUITY
    - Each clip must logically follow the previous one
    - No sudden jumps in environment, lighting, or character position

    2. TEMPORAL FLOW
    - Clip 1 → minimal motion (starting frame)
    - Clip 2 → slight progression
    - Clip 3 → clear transition
    - Clip 4 → aligns with next scene

    3. CONSISTENCY
    - Same characters must persist unless gradual change is described
    - No sudden appearance/disappearance of objects

    4. VISUAL DETAIL QUALITY
    - Each prompt must include:
        • camera movement
        • lighting description
        • environment detail
        • character motion

    5. REMOVE ISSUES
    - Fix vague phrases like "scene changes"
    - Replace generic descriptions with specific cinematic details

    --------------------------------
    CORRECTION RULES
    --------------------------------
    - Improve prompts ONLY if necessary
    - Preserve original intent where possible
    - Ensure smooth progression across all 4 clips

    --------------------------------
    OUTPUT FORMAT
    --------------------------------
    [
    {{
        "clip": 1,
        "prompt": "..."
    }},
    {{
        "clip": 2,
        "prompt": "..."
    }},
    {{
        "clip": 3,
        "prompt": "..."
    }},
    {{
        "clip": 4,
        "prompt": "..."
    }}
    ]
    """
   #transitions = robust_json_call(validate_prompt, DEEPSEEK_MODEL)
   #transitions = normalize_list(transitions)
   #transitions = ensure_length_4(transitions, "prompt")
   #print("validated transitions:", transitions)
   return transitions

def generate_audio(scene, transitions, dialogues):

    prompt = f"""
You are a professional film sound designer.

TASK:
Generate detailed audio design for each of the 4 clips.

For EACH clip, produce:
- "music": background score description
- "sound_effect": environmental and action-based sounds

For EACH clip, produce:
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
- Empty dialogue: If dialogue is an empty string for the clip, music and sfx can be described at full intensity with no ducking requirement.

MUSIC GUIDELINES

- Clearly describe:
  • instruments (e.g., piano, strings, synth, percussion)
  • tempo (slow, building, fast, tense)
  • emotional tone (suspense, calm, tension, humor, fear)
  • progression across clips

- Avoid vague phrases like:
  "dramatic music", "background music"

- Prefer:
  "low-frequency ambient synth with gradual tension buildup"
  "soft piano with echo and slow melancholic progression"

SOUND EFFECT GUIDELINES

- Must align with visual transitions
- Include:
  • environment (rain, wind, traffic, crowd)
  • character actions (footsteps, breathing, movement)
  • cinematic elements (whoosh, echo, impact)

- Be specific and layered:
  Not: "footsteps"
  Use: "wet footsteps splashing through puddles with echo in a narrow alley"

CONTINUITY RULES

- Audio must evolve smoothly across clips
- Maintain consistency in environment and mood
- Gradually increase or decrease intensity where appropriate
- Avoid abrupt or unrelated changes

INPUT


SCENE DESCRIPTION:
{scene}

VISUAL TRANSITIONS (4 clips):
{json.dumps(transitions, indent=2)}

DIALOGUES (4 clips):
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
]
"""

    audio = robust_json_call(prompt, GEMMA_MODEL)
    audio = normalize_list(audio)
    audio = ensure_length_4(audio, "music")

    return audio

from typing import List, Dict

def extract_dialogues(scene_desc: str, transitions: List[str]) -> List[Dict]:

    prompt = f"""
You are an expert film script parser.

Your task is to extract EXACT spoken dialogues from the scene and assign them to the correct clip.

--------------------------------
 OBJECTIVE:
--------------------------------
- Identify ONLY spoken dialogue
- Dialogue is ALWAYS inside quotes (' or ")
- Preserve text EXACTLY as written
- Map each dialogue to the most appropriate clip (1–4) using transitions as timeline

--------------------------------
 STRICT RULES:
--------------------------------
1. ONLY extract text inside quotes (' or ")
2. DO NOT modify dialogue in ANY way
3. DO NOT shorten, expand, or paraphrase
4. DO NOT include narration or descriptive text
5. DO NOT break sentences
6. DO NOT include partial dialogue
7. If no dialogue belongs to a clip → return empty string ""
8. If multiple dialogues fit same clip → combine them separated by a space

--------------------------------
 CLIP MAPPING LOGIC:
--------------------------------
- Use transitions to understand progression of scene
- Early transitions → clip 1
- Middle → clip 2–3
- End → clip 4

--------------------------------
 OUTPUT FORMAT (STRICT):
--------------------------------
Return ONLY valid JSON.
NO explanation. NO markdown.

[
  {{"clip":1,"dialogue":"..."}},
  {{"clip":2,"dialogue":"..."}},
  {{"clip":3,"dialogue":"..."}},
  {{"clip":4,"dialogue":"..."}}
]

--------------------------------
 INPUT:
--------------------------------

Scene:
{scene_desc}

Transitions:
{json.dumps(transitions)}
"""

    # ✅ USE ROBUST CALL
    data = robust_json_call(prompt, GEMMA_MODEL)

    # ✅ Normalize structure
    data = normalize_list(data)

    # ✅ Ensure 4 clips
    data = ensure_length_4(data, "dialogue")

    # ✅ Final safety (VERY IMPORTANT)
    for i, d in enumerate(data):
        if not isinstance(d, dict):
            data[i] = {"clip": i+1, "dialogue": ""}
        else:
            d.setdefault("clip", i+1)
            d.setdefault("dialogue", "")

            # Force string
            if not isinstance(d["dialogue"], str):
                d["dialogue"] = str(d["dialogue"])

    return data[:4]




def generate_video_json(story, T):
    try:
        scenes = generate_scenes(story, T)
        final = []

        for i in range(len(scenes)):
            print(f"\n Scene {i+1}")

            desc = scenes[i]["description"]

            keyframe = generate_keyframe(desc)

            next_keyframe = ""
            if i < len(scenes)-1:
                next_keyframe = generate_keyframe(
                    scenes[i+1]["description"]
                )

            transitions = generate_transitions(
                desc, keyframe, next_keyframe
            )

            dialogues = extract_dialogues(desc, transitions)

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
                    "music_volume": audio[j].get("music_volume", 0.5),
                    "dialogue": dialogues[j].get("dialogue", "") if j < len(dialogues) else ""
                })

            final.append({
                "scene": i+1,
                "description": desc,
                "keyframe_prompt": keyframe,
                "clips": clips,
                "dialogue_prompt": dialogues
            })

        return final
    except Exception as e:
        print(f"Failed to generate dynamically: {e}. Using fallback cinematic sequence.")
        # T is 10 seconds, so we generate 2 clips of 5 seconds each
        num_clips = max(1, T // 5)
        clips = []
        for j in range(num_clips):
            clips.append({
                "clip": j+1,
                "transition_prompt": f"Camera moves dynamically showing {story}",
                "music": "Cinematic ambient music",
                "sound_effect": "Wind and environment ambiance",
                "duration": 5.0,
                "dialogue_start": 0.0,
                "dialogue_volume": 1.0,
                "sfx_volume": 1.0,
                "music_volume": 0.5,
                "dialogue": ""
            })
        return [{
            "scene": 1,
            "description": story,
            "keyframe_prompt": f"{story}, highly detailed, cinematic lighting, masterpiece",
            "clips": clips,
            "dialogue_prompt": []
        }]


if __name__ == "__main__":
    story = input("Enter story:\n")
    T = int(input("Enter video length (seconds): "))

    result = generate_video_json(story, T)

    with open("ww.json", "w") as f:
        json.dump(result, f, indent=4)

    print("\n✅ ww.json generated")


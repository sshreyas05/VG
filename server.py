import modal
import os
import uuid
import shutil
from pathlib import Path

# ─────────────────────────────────────────
# 1. APP / IMAGE / VOLUME
# ─────────────────────────────────────────
app = modal.App("cinematic-audio-api")

volume = modal.Volume.from_name("model-cache", create_if_missing=True)

image = (
    modal.Image.debian_slim(python_version="3.10")
    .apt_install(
        "ffmpeg", "pkg-config", "libsndfile1", "espeak-ng",
        "libavformat-dev", "libavcodec-dev", "libavdevice-dev",
        "libavutil-dev", "libavfilter-dev", "libswscale-dev", "libswresample-dev",
    )
    .pip_install(
        "torch==2.1.0+cu118",
        "torchaudio==2.1.0+cu118",
        extra_index_url="https://download.pytorch.org/whl/cu118",
    )
    .pip_install(
        "transformers==4.41.2",
        "accelerate",
        "TTS",
        "audiocraft",
        "soundfile",
        "fastapi[standard]",
        "pydantic",
    )
)

# ─────────────────────────────────────────
# 2. SFX PROMPT TRANSLATOR
#    AudioGen generates SOUNDS, not speech.
#    Narrative text → acoustic description.
#    120+ patterns across 12 categories.
# ─────────────────────────────────────────
def translate_sfx_prompt(sfx_text: str) -> str:
    import re

    sfx_lower = sfx_text.lower().strip()

    ACOUSTIC_MAP = [

        # ── HUMAN VOICE & BODY ───────────────────────────────────────────────
        (r"scream(ing|s)?|shriek(ing|s)?|wail(ing|s)?",
            "loud agonized human scream, raw throat, peak intensity, close mic, reverb tail"),
        (r"whisper(ing|s)?|murmur(ing|s)?",
            "close-mic whisper, breathy, intimate, very low volume, slight room tone"),
        (r"laugh(ing|ter|s)?|giggl(ing|e|es)?|chuckl(ing|e)?",
            "natural human laughter, warm, genuine, slight breath between laughs"),
        (r"cry(ing)?|sob(bing|s)?|weep(ing|s)?",
            "person sobbing, wet breath, hitching inhale, emotional breakdown, quiet room"),
        (r"grunt(ing|s)?|groan(ing|s)?|moan(ing|s)?",
            "deep human grunt, exertion, strained effort, low frequency"),
        (r"pant(ing|s)?|gasp(ing|s)?|hyperventilat",
            "rapid panting, breathless, panicked breathing, close mic, irregular rhythm"),
        (r"heartbeat|heart beat|heart pound",
            "deep human heartbeat, slow thudding pulse, 60 BPM, low bass thump, wet organic"),
        (r"cough(ing|s)?|hack(ing)?",
            "sharp dry cough, single burst, slight echo, realistic close recording"),
        (r"sneez(ing|e|es)?",
            "sudden loud sneeze, nasal burst, short sharp impact"),
        (r"snor(ing|e|es)?",
            "deep rhythmic snoring, nasal rumble, slow cycle, bedroom ambience"),
        (r"yell(ing|s)?|shout(ing|s)?|holler(ing)?",
            "loud shouting voice, commanding, distance mic, natural reverb, aggressive tone"),
        (r"\bsing(ing|s)?\b|\bhum(ming|s)?\b",
            "human voice humming softly, single note, resonant, close mic, warm tone"),
        (r"swallow(ing)?|gulp(ing)?",
            "throat swallow sound, quiet, wet, close proximity recording"),
        (r"burp(ing)?|belch(ing)?",
            "loud belch, guttural resonance, mouth close to mic"),
        (r"stomp(ing|s)?|stamp(ing)?",
            "heavy boot stomping on wooden floor, deep thud, rhythmic, resonant"),
        (r"clap(ping|s)?|applaud|applause",
            "crowd applause, multiple hands clapping, building in intensity, large hall reverb"),
        (r"crowd(s)?|mob|audience|cheer(ing|s)?",
            "large crowd noise, hundreds of voices, distant roar, stadium ambience, chanting"),
        (r"whistle(ing|s)?",
            "sharp human whistle, piercing tone, short duration, outdoor ambience"),
        (r"teeth chatter|shiver(ing)?|trembl(ing|e)?",
            "teeth chattering rapidly, cold shivering, jaw trembling sound"),

        # ── FOOTSTEPS & MOVEMENT ─────────────────────────────────────────────
        (r"footstep(s)?|walk(ing)?|step(ping|s)?",
            "slow deliberate footsteps on hard concrete floor, slight echo, leather sole"),
        (r"run(ning)?|sprint(ing)?|jog(ging)?",
            "fast running footsteps, hard surface, rapid cadence, breathless momentum"),
        (r"creep(ing)?|sneak(ing)?|tiptoe",
            "very soft careful footsteps, near silent, slight floor creak, tense slow pace"),
        (r"march(ing)?|tromp(ing)?|parade",
            "military marching footsteps, synchronized, multiple soldiers, hard ground, rhythmic"),
        (r"stumbl(ing|e)?|trip(ping)?|fall(ing)?",
            "person stumbling and falling, scuffing feet, body impact with floor, grunt"),
        (r"crawl(ing)?|drag(ging)? body|dragging",
            "body crawling slowly across rough floor, fabric on concrete, labored movement"),
        (r"jump(ing)?|leap(ing)?|land(ing)?",
            "heavy jump landing, two feet impact, floor thud, slight grunt of effort"),

        # ── NATURE & WEATHER ─────────────────────────────────────────────────
        (r"rain(ing|fall|drop|storm)?|drizzl(e|ing)?|downpour",
            "heavy rain on asphalt, layered droplet impacts, puddle splashes, continuous ambient wash"),
        (r"thunder(storm|clap|bolt)?|lightning storm",
            "massive thunder crack, deep rolling rumble fading over 8 seconds, storm ambience"),
        (r"wind(y)?|breeze|gust(ing)?|gale|howl(ing)?",
            "strong wind howling through trees, leaves rustling, gusts varying in intensity, outdoor"),
        (r"blizzard|snowstorm|snow(fall)?|whiteout",
            "blizzard wind, howling cold gusts, snow particles, desolate frozen ambience"),
        (r"hail(storm)?",
            "hailstones hitting hard roof and ground, sharp irregular impacts, intense rattling"),
        (r"fog(horn)?|mist",
            "distant foghorn blast, low resonant drone, harbor ambience, muffled atmosphere"),
        (r"fire|flame(s)?|burn(ing)?|blaze|inferno",
            "roaring fire, deep crackling and popping, wood splitting, heat roar, intense combustion"),
        (r"campfire|bonfire",
            "gentle campfire crackling, soft pops, warm ambience, light wood settling"),
        (r"ocean|sea|wave(s)?|surf|tide",
            "large ocean waves crashing on rocky shore, deep water boom, foam hiss, seagulls distant"),
        (r"river|stream|creek|brook|babbl(ing|e)?",
            "shallow river flowing over rocks, constant water babble, gentle current, natural reverb"),
        (r"waterfall|cascade|rapids",
            "powerful waterfall roar, continuous white noise rush, mist ambience, canyon echo"),
        (r"lake|pond|still water",
            "still water lapping quietly at shore, minimal movement, peaceful ambience"),
        (r"swamp|marsh|bog",
            "swamp ambience, frogs croaking, insects, bubbling mud, humid dense atmosphere"),
        (r"earthquake|tremor|rumbl(ing)?|ground shak",
            "deep earth rumble, low frequency ground tremor, 20hz sub bass, building creak"),
        (r"avalanche|landslide|rockslide",
            "massive avalanche roar, tons of debris cascading, deep rumble, impact shockwave"),
        (r"volcano|lava|eruption",
            "volcanic rumble, deep magma movement, distant explosion, geological low frequency"),
        (r"tornado|cyclone|twister",
            "tornado wind roar, massive air pressure whoosh, debris flying, train-like rumble"),
        (r"flood|surge|tsunami",
            "massive water surge, deep rolling boom, flood rushing, overwhelming water noise"),

        # ── ANIMALS ──────────────────────────────────────────────────────────
        (r"dog(s)?|bark(ing)?|woof|growl(ing)? dog",
            "aggressive dog barking, deep chest resonance, territorial, close proximity"),
        (r"wolf|wolves|howl(ing)?",
            "lone wolf howling, mournful sustained tone, distant echo, night ambience"),
        (r"cat(s)?|meow|hiss(ing)? cat|purr(ing)?",
            "cat hissing aggressively, sharp burst, defensive, close mic"),
        (r"horse(s)?|gallop(ing)?|hoove(s)?|neigh(ing)?",
            "horse galloping on dirt, rhythmic four-beat canter, accelerating, ground vibration"),
        (r"bird(s)?|chirp(ing)?|tweet(ing)?|songbird",
            "morning birds chirping, multiple species, overlapping calls, forest dawn ambience"),
        (r"crow(s)?|raven(s)?|caw(ing)?",
            "crow cawing, harsh raspy call, single bird, ominous, distance echo"),
        (r"owl(s)?|hoot(ing)?",
            "owl hooting, deep resonant call, slow rhythm, night forest ambience"),
        (r"eagle|hawk|falcon|screech(ing)? bird",
            "eagle screeching, piercing high frequency cry, aerial, sharp and brief"),
        (r"insect(s)?|cricket(s)?|cicada(s)?|bug(s)?",
            "night insects, crickets and cicadas, dense layered chirping, warm summer ambience"),
        (r"bee(s)?|wasp(s)?|hornet(s)?|buzz(ing)?",
            "angry bee swarm buzzing, dense oscillating tone, threatening proximity"),
        (r"fly(ing)? insect|mosquito|gnat",
            "single mosquito buzzing near ear, irritating high pitch, close proximity"),
        (r"snake|hiss(ing)?|rattle(snake)?",
            "rattlesnake rattle, dry shaking, threatening warning, desert ambience"),
        (r"lion|tiger|roar(ing)?|big cat",
            "lion roaring, massive chest resonance, deep sub bass, savanna echo, power"),
        (r"bear(s)?|grizzly|growl(ing)? bear",
            "bear growling, low guttural rumble, dangerous proximity, heavy breath"),
        (r"elephant(s)?|trumpet(ing)?",
            "elephant trumpeting, powerful nasal blast, African plains ambience, dust"),
        (r"whale(s)?|dolphin(s)?|underwater mammal",
            "whale song, slow ethereal calls, deep underwater resonance, oceanic ambience"),
        (r"frog(s)?|toad(s)?|croak(ing)?",
            "frogs croaking rhythmically, pond ambience, night, layered calls"),
        (r"wolf pack|howling wolves|wolves",
            "wolf pack howling together, multiple harmonics, haunting night chorus, distant hills"),

        # ── WEAPONS & COMBAT ─────────────────────────────────────────────────
        (r"gunshot|gun(fire)?|pistol|shoot(ing)?|shot fired|rifle|sniper",
            "sharp gunshot crack, loud transient impact, reverb tail in open space, brass shell casing drop"),
        (r"machine gun|automatic fire|burst fire|submachine",
            "rapid automatic gunfire, stuttering bursts, mechanical cycling, brass ejection, echo"),
        (r"shotgun|pump action|blast(ed)? gun",
            "deep shotgun boom, massive low frequency blast, pump action cycling, shell ejection"),
        (r"silenced|suppressed|silencer",
            "suppressed gunshot, muffled thwick, near silent, mechanical action, no echo"),
        (r"explosion|explode|bomb|detonate|blast|dynamite",
            "massive explosion, initial shockwave crack, deep bass bloom, debris raining, dust settling"),
        (r"grenade|flash(bang)?",
            "grenade explosion, sharp crack then rolling echo, shrapnel hiss, ringing aftermath"),
        (r"rocket|missile|rpg|launch(ed)?",
            "rocket launch whoosh, tail flame roar, distant impact explosion, sonic trail"),
        (r"cannon|artillery|mortar|howitzer",
            "cannon fire, thunderous deep boom, muzzle blast pressure, far echo, earth shake"),
        (r"sword|blade|slash|clash|clang(ing)?|steel on steel",
            "metal sword clash, bright ringing impact, steel scraping, sparks, resonant ring"),
        (r"arrow(s)?|bow|twang|quiver",
            "arrow released, bow twang, shaft whoosh through air, impact thud in wood"),
        (r"knife|dagger|stab(bing)?|slash(ing)?",
            "blade drawn from sheath, sharp metallic ring, knife impact, handle rattle"),
        (r"punch(ing)?|hit(ting)?|impact|smash(ing)? fist|fight(ing)?",
            "hard fist impact, meaty thud, cartilage crunch, grunt of pain, body blow"),
        (r"kick(ing)?|stomp(ing)? fight",
            "powerful kick impact, deep body thud, boot on ribs, exhaled grunt"),
        (r"choke|strangle|neck snap",
            "neck crack, sharp pop, immediate silence, close mic, disturbing precision"),
        (r"whip(ping)?|lash(ing)?",
            "leather whip crack, sharp supersonic snap, air displacement, echo in space"),
        (r"chainsaw|buzz saw",
            "chainsaw revving and cutting, aggressive motor roar, blade teeth on wood, splatter"),
        (r"taser|stun gun|electrocute",
            "taser discharge, rapid electric clicking, buzz crackle, victim muscle contraction"),

        # ── VEHICLES & MACHINES ──────────────────────────────────────────────
        (r"car|vehicle engine|rev(ving)?|automobile",
            "car engine revving, exhaust note, RPM climb, mechanical vibration, road noise"),
        (r"car crash|collision|crash(ing)? car|accident",
            "violent car collision, metal impact, glass shattering, tires screech, steam hiss"),
        (r"tire(s)?|screech(ing)?|skid(ding)?",
            "tires screeching on asphalt, rubber burning, high pitched friction, deceleration"),
        (r"motorcycle|bike engine|motorbike",
            "motorcycle engine, aggressive exhaust note, gear shifts, acceleration roar"),
        (r"truck|semi|lorry|eighteen wheeler",
            "large truck engine, deep diesel rumble, air brakes hiss, heavy road vibration"),
        (r"helicopter|chopper|rotor(s)?",
            "helicopter blades chopping air, rhythmic thwump, engine whine, blade wash wind"),
        (r"airplane|aircraft|jet engine|turbine|plane",
            "jet engine roar, massive air intake whoosh, turbine whine, runway acceleration"),
        (r"train|locomotive|railway|rail(road)?",
            "steam locomotive, rhythmic steel wheels on track, whistle blast, station departure"),
        (r"subway|metro|underground train",
            "subway train arriving, tunnel echo, wind rush, screeching brakes, doors opening"),
        (r"boat|ship|vessel|engine boat",
            "boat engine chugging, water displacement, hull against waves, marine ambience"),
        (r"submarine|sonar|ping(ing)?",
            "sonar ping, single metallic tone, underwater reverb, silence between pulses"),
        (r"tank|armored vehicle|tracks",
            "tank tracks on rough terrain, massive engine rumble, mechanical clanking, weight"),
        (r"siren|alarm|emergency|police siren",
            "emergency siren wailing, rising and falling tone, Doppler effect, urgent"),
        (r"drill(ing)?|jackhammer|pneumatic",
            "pneumatic jackhammer, rapid hammer impacts, concrete breaking, construction site"),
        (r"chainsaw machine|industrial saw|circular saw",
            "circular saw blade spinning, high pitched whine, wood cutting, sawdust"),
        (r"generator|turbine hum|machine hum",
            "industrial generator hum, constant low frequency drone, mechanical oscillation"),
        (r"clock|tick(ing)?|tock|metronome",
            "mechanical clock ticking, precise rhythmic clicks, quiet room, pendulum swing"),

        # ── ENVIRONMENT & SPACES ─────────────────────────────────────────────
        (r"door|slam(ming)?|bang(ing)? door",
            "heavy wooden door slamming shut, deep bass thud, frame rattle, echo in hallway"),
        (r"creak(ing)?|squeak(ing)?|hinge",
            "old door hinge creaking slowly, rusted metal groan, horror atmosphere"),
        (r"window|glass break|shatter(ing)?",
            "window glass shattering, explosive impact, fragments cascading, frame vibration"),
        (r"footstep wood|floor creak|wooden floor",
            "old wooden floorboard creaking under weight, slow single step, house settling"),
        (r"drip(ping)?|faucet|tap water",
            "single water drop dripping, hollow plop, slow irregular interval, empty room"),
        (r"pipe(s)?|plumbing|water pipe",
            "metal water pipes clanging, pressure surge, banging in walls, building noise"),
        (r"church bell|toll(ing)?|cathedral bell",
            "deep church bell toll, massive bronze resonance, long sustain, outdoor echo"),
        (r"alarm clock|buzz(er)?|morning alarm",
            "alarm clock buzzing, repetitive electronic tone, persistent, close"),
        (r"phone ring(ing)?|telephone",
            "old telephone ringing, double ring pattern, mechanical bell, vintage"),
        (r"typewriter|key(s)? click|keyboard",
            "mechanical typewriter keys clacking, rhythmic typing, carriage return bell"),
        (r"radio static|white noise|interference",
            "radio static crackle, white noise hiss, signal interference, scan sweep"),
        (r"tv static|television noise",
            "old television static, white noise, electromagnetic hiss, CRT buzz"),
        (r"crowd murmur|restaurant noise|cafe ambience",
            "indoor crowd murmur, overlapping conversations, cutlery, ambient social noise"),
        (r"church|cathedral|holy|sacred space",
            "cathedral ambience, massive reverb, distant organ, silence with weight, stone walls"),
        (r"cave|cavern|underground|echo(ing)?",
            "cave ambience, deep reverb, water drips echo, dark resonant space, low rumble"),
        (r"forest|jungle|woodland|nature ambience",
            "dense forest ambience, wind in canopy, branch creak, distant animals, layered"),
        (r"desert|arid|sand|dune",
            "desert wind, sand grain movement, vast silence, dry air, distant howl"),
        (r"city|urban|street|traffic ambience",
            "city street ambience, distant traffic, voices, horns, urban white noise layer"),
        (r"underwater|submerged|diving",
            "underwater ambience, muffled pressure, bubble streams, deep resonance, silence"),

        # ── SCI-FI & FUTURISTIC ──────────────────────────────────────────────
        (r"laser|beam|zap|pew|ray gun",
            "laser beam discharge, bright electronic zap, sci-fi tonal burst, quick decay"),
        (r"spaceship|spacecraft|space engine|warp|hyperspace",
            "spaceship engine hum, deep resonant drone, thruster pulse, vacuum ambience"),
        (r"robot|android|servo|mechanical movement",
            "robotic servo motors, precise mechanical movement, electronic whir, joint articulation"),
        (r"computer|beep|electronic|digital",
            "computer processing beeps, digital tones, keyboard input, fan hum, electronic"),
        (r"portal|wormhole|dimension|rift",
            "dimensional portal opening, reality distortion, bass drop, swirling energy vortex"),
        (r"forcefield|shield|energy barrier",
            "energy shield activation, sustained electronic hum, impact deflection tone"),
        (r"teleport|beam up|dematerialize",
            "teleportation sound, rapid molecular scatter, bright electronic shimmer, silence"),
        (r"alien|extraterrestrial|ufo",
            "alien vocal communication, non-human frequency modulation, eerie harmonic"),
        (r"power up|charge(d|ing)?|energy buildup",
            "energy charging buildup, rising frequency sweep, escalating electrical hum, release"),
        (r"holo(gram)?|holographic|projection",
            "hologram activation, thin electronic shimmer, flickering digital tone"),
        (r"radar|sonar scan|sensor",
            "radar sweep, regular electronic ping, rotating scan tone, tracking beep"),

        # ── HORROR & SUPERNATURAL ────────────────────────────────────────────
        (r"ghost|spirit|haunt(ing)?|phantom",
            "ghostly moan, ethereal vocal drone, pitch shifting, reverb heavy, cold atmosphere"),
        (r"demon|evil|possessed|dark entity",
            "demonic growl, sub-harmonic distortion, layered voices, unnatural resonance"),
        (r"monster|creature|beast",
            "large creature growl, deep chest resonance, wet breath, predatory, threatening"),
        (r"horror ambience|scary|dread|terror",
            "horror atmosphere, sub bass drone, distant metallic scrape, unpredictable silence"),
        (r"heartbeat fast|panic|racing heart",
            "rapid panicked heartbeat, 120 BPM, heavy wet thud, increasing tempo, close mic"),
        (r"bones|skeleton|crack(ing)? bone|snap",
            "bone cracking, dry sharp snap, cartilage pop, disturbing close mic recording"),
        (r"blood|gore|flesh|visceral",
            "wet visceral impact, flesh sound, disturbing organic texture, close proximity"),
        (r"static horror|signal|interference horror",
            "distorted radio signal, corrupted audio, electronic screech buried in static"),

        # ── MAGIC & FANTASY ──────────────────────────────────────────────────
        (r"magic|spell|enchant|wizardry|sorcery",
            "magical spell casting, crystalline shimmer, sparkle burst, harmonic overtones, reverb"),
        (r"fireball|fire magic|flame spell",
            "fireball whoosh, combustion burst, crackling flame impact, heat roar"),
        (r"ice|freeze|frost|blizzard spell",
            "ice spell, crystalline freeze tone, glass-like shattering, cold air rush"),
        (r"lightning spell|thunder magic|electric spell",
            "lightning bolt crack, electrical discharge, thunder follow, ozone sizzle"),
        (r"potion|brew(ing)?|cauldron|bubble",
            "bubbling cauldron, thick liquid pops, steam hiss, magical brew ambience"),
        (r"dragon|roar(ing)? dragon|dragon fire",
            "dragon roar, massive sub bass resonance, chest rumble, prehistoric power"),
        (r"fairy|pixie|sprite|magical creature",
            "fairy chime, light delicate bell tones, shimmer, ethereal sparkle, tiny wings"),
        (r"sword magic|enchanted blade|magical weapon",
            "enchanted sword hum, resonant metallic tone, magical energy sustained note"),

        # ── IMPACTS & DESTRUCTION ────────────────────────────────────────────
        (r"massive explosion|nuclear|nuke|detonation",
            "nuclear scale explosion, earth-shaking sub bass, shockwave crack, total destruction roar"),
        (r"building collapse|structure fail|collaps(e|ing)|rubble fall",
            "building collapsing, cascading concrete and steel, massive rumble, dust cloud rush"),
        (r"earthquake large|magnitude|seismic",
            "major earthquake, deep earth fracture, 10hz sub bass, surface cracking, panic ambience"),
        (r"meteor|asteroid|impact from space",
            "meteor impact, atmospheric entry whoosh, earth-shattering collision, shockwave"),
        (r"thunder of war|battle ambience|warzone",
            "battle ambience, continuous distant explosions, gunfire layers, shouting, chaos"),
        (r"wood break|crack(ing)? wood|lumber snap",
            "thick wood beam snapping under tension, deep crack, splintering fiber, resonant break"),
        (r"metal tear|rip(ping)? metal|steel break",
            "metal tearing, high pitched screech, structural failure, jagged ripping"),
        (r"concrete break|cement crack|rubble",
            "concrete shattering, heavy dense impact, dust, fragments, construction demo"),

    ]

    # ── Multi-keyword combiner ──────────────────────────────────────────────
    # If the input contains multiple matched categories (e.g. "explosion then screaming"),
    # collect all matches and merge their acoustic descriptions for a richer output.
    matched = []
    for pattern, acoustic in ACOUSTIC_MAP:
        if re.search(pattern, sfx_lower):
            matched.append(acoustic)
        if len(matched) >= 3:   # cap at 3 combined descriptions to keep prompt clean
            break

    if matched:
        return ", then ".join(matched) if len(matched) > 1 else matched[0]

    # ── Intelligent fallback ────────────────────────────────────────────────
    # Strip narrative filler words, keep descriptive content, append acoustic context
    cleaned = re.sub(
        r"\b(a|an|the|is|are|was|were|man|woman|person|people|someone|there|with|and|of|in|on)\b",
        " ", sfx_lower
    )
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return f"{cleaned}, realistic high fidelity sound effect, detailed acoustic recording"


# ─────────────────────────────────────────
# 3. MODEL CACHE (stays warm between calls)
# ─────────────────────────────────────────
class _Models:
    music = None
    audio = None
    tts   = None


# ─────────────────────────────────────────
# 4. READ FRONTEND HTML AT DEPLOY TIME
# ─────────────────────────────────────────
_here = Path(__file__).parent
try:
    _FRONTEND_HTML = (_here / "frontend.html").read_text(encoding="utf-8")
except FileNotFoundError:
    _FRONTEND_HTML = "<h1>frontend.html missing — place it next to server.py</h1>"


# ─────────────────────────────────────────
# 5. FASTAPI APP  (defined at module level,
#    outside any Modal function)
# ─────────────────────────────────────────
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel

web_app = FastAPI(title="Cinematic Audio Engine")


class AudioRequest(BaseModel):
    dialogue:          str
    music:             str
    sfx:               str
    sfx_volume:        float = 1.0
    music_volume:      float = 0.4
    dialogue_volume:   float = 1.5
    # ── Timing controls ──────────────────────────────
    total_duration:    float          = 30.0  # total output length in seconds (1–60)
    music_duration:    Optional[float] = None  # defaults to total_duration if not set
    sfx_duration:      Optional[float] = None  # defaults to total_duration if not set
    sfx_start:         float          = 0.0   # seconds from start when SFX kicks in
    dialogue_start:    float          = 0.0   # seconds from start when dialogue kicks in


@web_app.get("/", response_class=HTMLResponse)
async def frontend():
    return HTMLResponse(_FRONTEND_HTML)


@web_app.post("/generate")
async def generate(req: AudioRequest):
    import torch, soundfile as sf, subprocess
    from audiocraft.models import MusicGen, AudioGen
    from TTS.api import TTS

    os.environ["COQUI_TOS_AGREED"] = "1"
    os.environ["HF_HOME"] = "/models"
    device = "cuda" if torch.cuda.is_available() else "cpu"

    # ── clamp total duration 1–60 s ──
    total   = max(1.0, min(60.0, req.total_duration))
    m_dur   = max(1.0, min(60.0, req.music_duration    or total))
    s_dur   = max(1.0, min(60.0, req.sfx_duration      or total))
    sfx_st  = max(0.0, req.sfx_start)
    dlg_st  = max(0.0, req.dialogue_start)

    print(f"[TIMING] total={total}s  music={m_dur}s  sfx={s_dur}s  "
          f"sfx_start={sfx_st}s  dialogue_start={dlg_st}s")

    if _Models.music is None:
        _Models.music = MusicGen.get_pretrained("facebook/musicgen-small")
    if _Models.audio is None:
        _Models.audio = AudioGen.get_pretrained("facebook/audiogen-medium")
    if _Models.tts is None:
        _Models.tts = TTS(model_name="tts_models/en/vctk/vits").to(device)

    # ── set duration on models before generating ──
    _Models.music.set_generation_params(duration=m_dur)
    _Models.audio.set_generation_params(duration=s_dur)

    acoustic = translate_sfx_prompt(req.sfx)
    print(f"[SFX] '{req.sfx}'  →  '{acoustic}'")

    music_out = _Models.music.generate([req.music])
    sfx_out   = _Models.audio.generate([acoustic])

    m_p, s_p, t_p = "/tmp/m.wav", "/tmp/s.wav", "/tmp/t.wav"
    sf.write(m_p, music_out[0].cpu().numpy().T, 32000)
    sf.write(s_p, sfx_out[0].cpu().numpy().T,  32000)
    _Models.tts.tts_to_file(text=req.dialogue, speaker="p226", file_path=t_p)

    # ── build ffmpeg filter with per-track delays + trim final to total ──
    # adelay applies millisecond offset so each track starts at the right time.
    # apad ensures shorter tracks don't cut the mix early.
    # atrim+asetpts clips the final mix to exactly total_duration seconds.
    mv, sv, tv = req.music_volume, req.sfx_volume, req.dialogue_volume
    sfx_ms  = int(sfx_st  * 1000)
    dlg_ms  = int(dlg_st  * 1000)

    filter_complex = (
        f"[0:a]volume={mv},apad[m];"
        f"[1:a]volume={sv},adelay={sfx_ms}|{sfx_ms},apad[s];"
        f"[2:a]volume={tv},adelay={dlg_ms}|{dlg_ms},apad[t];"
        f"[m][s][t]amix=inputs=3:duration=longest[mix];"
        f"[mix]atrim=0:{total},asetpts=PTS-STARTPTS[out]"
    )

    final = "/tmp/final.wav"
    subprocess.run([
        "ffmpeg", "-y",
        "-i", m_p, "-i", s_p, "-i", t_p,
        "-filter_complex", filter_complex,
        "-map", "[out]",
        final,
    ], check=True)

    os.makedirs("/models/outputs", exist_ok=True)
    fname = f"scene_{uuid.uuid4().hex[:8]}.wav"
    dest  = f"/models/outputs/{fname}"
    shutil.copy(final, dest)
    volume.commit()

    return {
        "status":          "success",
        "filename":        fname,
        "path_on_volume":  dest,
        "sfx_prompt_used": acoustic,
        "timing": {
            "total_duration":  total,
            "music_duration":  m_dur,
            "sfx_duration":    s_dur,
            "sfx_start":       sfx_st,
            "dialogue_start":  dlg_st,
        },
    }


@web_app.get("/download/{filename}")
async def download(filename: str):
    path = f"/models/outputs/{filename}"
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(path, media_type="audio/wav", filename=filename)


@web_app.get("/list")
async def list_files():
    out = "/models/outputs"
    if not os.path.exists(out):
        return {"files": []}
    return {"files": sorted(os.listdir(out), reverse=True)}


# ─────────────────────────────────────────
# 6. MODAL ENTRY POINT
#    In Modal 1.x the correct pattern is:
#    @app.function  then  @modal.asgi_app()
#    The function must RETURN the FastAPI app.
# ─────────────────────────────────────────
@app.function(
    image=image,
    gpu="T4",
    volumes={"/models": volume},
    timeout=600,
    container_idle_timeout=300,
)
@modal.asgi_app()
def serve():
    return web_app

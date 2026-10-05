"""Generate ElevenLabs voice clips for every phrase drill-caller.html can say.

Reads the GUARDS / DEFENSES / ATTACKS / FROM_POSITION tables straight from the app so the
clip set stays in sync, then writes one MP3 per phrase to voice-clips/. Existing clips are
kept (re-runs only fill gaps) unless --force or --only is given.

Clip keys (the app looks clips up by these):
  g-<guard>-<lang>              guard call, e.g. g-finD-it
  x-<defense>-<attack>-<lang>   defend-and-strike call, e.g. x-rebattere-mf-en
  done-en                       end of session
"""
import argparse, io, json, os, re, sys
from elevenlabs import tts
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HTML, OUT_DIR = "drill-caller.html", "voice-clips"
MODEL = "eleven_v3"
# Chosen by ear from voice-samples/: Arnold for Italian, Adam for English, both "punchy"
# (exclamation marks + stability 0.0, the most expressive v3 setting).
VOICE = {"it": "VR6AewLTigWG4xSOukaG", "en": "pNInz6obpgDQGcFmaJgB"}
SETTINGS = {"stability": 0.0}
# Wording picked by ear for clips whose default take sounded off (see archive/voice-clips-replaced/).
TEXT_OVERRIDES = {
    "done-en": "Done. Well fought.",
    "g-bicorno-it": "Posta di Bicorno.",
    "g-breve-it": "Posta Breve.",
    "g-longa-it": "Posta Longa.",
}
# 64 kbps keeps the embedded file small; spoken calls don't need more.
FORMAT = "mp3_44100_64"

def read_tables(src):
    def table(name):
        body = re.search(r"var " + name + r" = \{(.*?)\n  \};", src, re.S)
        if not body: raise SystemExit(f"Couldn't find the {name} table in {HTML}.")
        return {m.group(1): {"it": m.group(2), "en": m.group(3), "rest": m.group(4)}
                for m in re.finditer(r'(\w+):\s*\{\s*it: "([^"]+)",\s*en: "([^"]+)"(.*?)\}', body.group(1))}
    from_pos = json.loads("{" + re.search(r"var FROM_POSITION = \{(.*?)\};", src, re.S).group(1).replace("\n", "") + "}")
    return table("GUARDS"), table("DEFENSES"), table("ATTACKS"), from_pos

def phrases(src):
    """Every (key, lang, text) the app can speak, mirroring afterDefense() and the scambiar rule."""
    guards, defenses, attacks, from_pos = read_tables(src)
    flip = lambda s: {"R": "L", "L": "R"}.get(s, "C")
    out = []
    combos = set()
    for gk, g in guards.items():
        # English guards end in a period: with "!" Adam lifts the side ("…, left!") into an odd rising lilt.
        out += [(f"g-{gk}-it", "it", g["it"] + "!"), (f"g-{gk}-en", "en", g["en"] + ".")]
        h = re.search(r'h: "(\w+)"', g["rest"]).group(1); side = re.search(r's: "(\w)"', g["rest"]).group(1)
        for d in re.findall(r'"(\w+)"', g["rest"].split("def:")[1]):
            if d in ("incrosare", "scambiar") or h == "mid": pos = "mid-C"
            else: pos = ("low-" if h == "high" else "high-") + flip(side)
            combos.update((d, a) for a in from_pos[pos] if not (d == "scambiar" and a == "punta"))
    for d, a in sorted(combos):
        D, A = defenses[d], attacks[a]
        out.append((f"x-{d}-{a}-it", "it", f"{D['it']}, {A['it']}!"))
        out.append((f"x-{d}-{a}-en", "en", f"{D['en']}, then {A['en']}!"))  # matches the app's enJoined
    out.append(("done-en", "en", "Done!"))
    return [(k, lang, TEXT_OVERRIDES.get(k, text)) for k, lang, text in out]

parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
parser.add_argument("--dry-run", action="store_true", help="list what would be generated, call nothing")
parser.add_argument("--verbose", action="store_true", help="print each phrase's text")
parser.add_argument("--force", action="store_true", help="regenerate clips that already exist")
parser.add_argument("--only", nargs="+", metavar="KEY", help="regenerate just these clip keys (e.g. a bad take)")
args = parser.parse_args()

todo = phrases(open(HTML, encoding="utf-8").read())
if args.only:
    unknown = set(args.only) - {k for k, _, _ in todo}
    if unknown: raise SystemExit(f"Unknown clip keys: {', '.join(sorted(unknown))}")
    todo = [p for p in todo if p[0] in args.only]
elif not args.force:
    todo = [p for p in todo if not os.path.exists(f"{OUT_DIR}/{p[0]}.mp3")]

print(f"{len(todo)} clips to generate, {sum(len(t) for _, _, t in todo)} characters")
os.makedirs(OUT_DIR, exist_ok=True)
failed = []
for key, lang, text in todo:
    if args.verbose or args.dry_run: print(f"  {key}: {text}")
    if args.dry_run: continue
    try:
        open(f"{OUT_DIR}/{key}.mp3", "wb").write(tts(text, VOICE[lang], MODEL, lang, SETTINGS, FORMAT))
    except Exception as e:
        failed.append(key); print(f"  FAILED {key}: {e}")
if failed: sys.exit(f"{len(failed)} clips failed: {' '.join(failed)}. Re-run to retry just those.")

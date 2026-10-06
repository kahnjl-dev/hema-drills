"""Generate ElevenLabs voice clips for every call in drill-data.json.

Writes one MP3 per call to voice-clips/ and records each clip's exact text in
voice-clips/manifest.json. A clip is regenerated only when its text changes (compared
ignoring case) or its voice, model or settings change, so re-runs fill gaps and pick up
edits without touching takes you've already approved. Identical phrases are generated once and copied.

Clip keys (the app looks clips up by these):
  g-<guard>-<lang>     guard call, e.g. g-finD-it
  r-<remedy>-<lang>    defense-and-riposte (or thrust) call, e.g. r-tutta-cross-en
  done-en              end of session
"""
import argparse, io, json, os, shutil, sys
from elevenlabs import tts
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

DATA_FILE, OUT_DIR = "drill-data.json", "voice-clips"
MANIFEST = os.path.join(OUT_DIR, "manifest.json")
MODEL = "eleven_v3"
# Jordan's picks: Adam for English, Arnold for Italian, with the model's default delivery
# (no stability override) and no added punctuation, so calls sound plain rather than excited.
VOICE = {"it": "VR6AewLTigWG4xSOukaG", "en": "pNInz6obpgDQGcFmaJgB"}
SETTINGS = None
TEXT_OVERRIDES = {"done-en": "Done, well fought"}
# 64 kbps keeps the embedded file small; spoken calls don't need more.
FORMAT = "mp3_44100_64"

def phrases(data):
    """Every (key, lang, text) the app can speak."""
    out = []
    for k, g in data["guards"].items():
        out += [(f"g-{k}-it", "it", g["it"]), (f"g-{k}-en", "en", g["en"])]
    for r in data["remedies"]:
        it = ", ".join(l if i == 0 else l[0].lower() + l[1:] for i, l in enumerate(r["it"]))
        en = ", then ".join(l if i == 0 else l[0].lower() + l[1:] for i, l in enumerate(r["en"]))  # matches the app's enJoined
        out += [(f"r-{r['id']}-it", "it", it), (f"r-{r['id']}-en", "en", en)]
    out.append(("done-en", "en", "Done"))
    return [(k, lang, TEXT_OVERRIDES.get(k, text)) for k, lang, text in out]

parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
parser.add_argument("--dry-run", action="store_true", help="list what would be generated, call nothing")
parser.add_argument("--verbose", action="store_true", help="print each phrase's text")
parser.add_argument("--force", action="store_true", help="regenerate every clip")
parser.add_argument("--only", nargs="+", metavar="KEY", help="regenerate just these clip keys (e.g. a bad take)")
args = parser.parse_args()

all_phrases = phrases(json.load(open(DATA_FILE, encoding="utf-8")))
manifest = json.load(open(MANIFEST, encoding="utf-8")) if os.path.exists(MANIFEST) else {}
def signature(key, text):
    """What a clip was made from: voice, model, settings and text. A change to any of them remakes it."""
    lang = key.rsplit("-", 1)[1]
    return f"{VOICE[lang]}|{MODEL}|{json.dumps(SETTINGS)}|{text}"
def current(key, text):
    return os.path.exists(f"{OUT_DIR}/{key}.mp3") and manifest.get(key, "").lower() == signature(key, text).lower()

if args.only:
    unknown = set(args.only) - {k for k, _, _ in all_phrases}
    if unknown: raise SystemExit(f"Unknown clip keys: {', '.join(sorted(unknown))}")
    todo = [p for p in all_phrases if p[0] in args.only]
elif args.force:
    todo = all_phrases
else:
    todo = [p for p in all_phrases if not current(p[0], p[2])]

unique = {(lang, text) for _, lang, text in todo}
print(f"{len(todo)} clips to make, {len(unique)} distinct phrases, {sum(len(t) for _, t in unique)} characters")
os.makedirs(OUT_DIR, exist_ok=True)
made, failed = {}, []
for key, lang, text in todo:
    if args.verbose or args.dry_run: print(f"  {key}: {text}")
    if args.dry_run: continue
    try:
        if (lang, text) in made: shutil.copyfile(made[(lang, text)], f"{OUT_DIR}/{key}.mp3")
        else:
            open(f"{OUT_DIR}/{key}.mp3", "wb").write(tts(text, VOICE[lang], MODEL, lang, SETTINGS, FORMAT))
            made[(lang, text)] = f"{OUT_DIR}/{key}.mp3"
        manifest[key] = signature(key, text)
    except Exception as e:
        failed.append(key); print(f"  FAILED {key}: {e}")
if not args.dry_run:
    json.dump(manifest, open(MANIFEST, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
if failed: sys.exit(f"{len(failed)} clips failed: {' '.join(failed)}. Re-run to retry just those.")

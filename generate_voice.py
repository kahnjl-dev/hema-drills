"""Generate ElevenLabs voice clips for every call in drill-data.json.

Writes one MP3 per call to voice-clips/ and records each clip's exact text in
voice-clips/manifest.json. A clip is regenerated only when its text changes (compared
ignoring case) or its voice, model or settings change, so re-runs fill gaps and pick up
edits without touching takes you've already approved. Identical phrases are generated once and copied.

Clip keys (the app looks clips up by these):
  g-<guard>-<lang>     guard call, e.g. g-finD-it
  r-<remedy>-<lang>    defense-and-riposte (or thrust) call, e.g. r-tutta-cross-en
  s-<drill>-<n>-<lang> step n of a fixed drill, e.g. s-cutting-1-en (guard steps reuse g-<guard>)
  done-en              end of session
"""
import argparse, io, json, os, shutil, sys
from elevenlabs import tts
import drill_clips
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

DATA_FILE, OUT_DIR = "drill-data.json", "voice-clips"
MANIFEST = os.path.join(OUT_DIR, "manifest.json")
MODEL = "eleven_v3"
# Delivery: the model's default
# (no stability override) and no added punctuation, so calls sound plain rather than excited.
# Italian: Kallari (chosen Oct 2026). English: Rafael (chosen Oct 2026, replacing Kallari; those English
# clips are in archive/voice-clips-kallari-en/). Earlier Adam/Arnold clips: archive/voice-clips-adam-arnold/.
# Tried and passed over for English: Pharoah 3 (Qziuou6kCJ2R3w53L2Zs), Lane (QEmx0xOfbXnI0Aa5YAqD).
# Backup: Thomas (CITWdMEsnRduEUkNWXQv).
KALLARI = "2noihuQpglcWf1H9jf7J"
RAFAEL = "UGRSRN5yIPiE70HOrdJx"
VOICE = {"it": KALLARI, "en": RAFAEL}
SETTINGS = None
TEXT_OVERRIDES = {"done-en": "Done, well fought"}
# 64 kbps keeps the embedded file small; spoken calls don't need more.
FORMAT = "mp3_44100_64"

def phrases(data):
    """Every (key, lang, text) the app can speak (see drill_clips.py), with wording overrides."""
    return [(k, lang, TEXT_OVERRIDES.get(k, text)) for k, lang, text in drill_clips.phrases(data)]

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
# Reuse any existing clip already made from the same voice, settings and text (e.g. the same
# attack called from different guards), so only genuinely new phrases cost characters.
for k, sig in manifest.items():
    lang = k.rsplit("-", 1)[1]
    text = sig.split("|", 3)[3] if sig.count("|") >= 3 else None
    if text is not None and os.path.exists(f"{OUT_DIR}/{k}.mp3") and sig.lower() == signature(k, text).lower():
        made.setdefault((lang, text), f"{OUT_DIR}/{k}.mp3")
for key, lang, text in todo:
    if args.verbose or args.dry_run: print(f"  {key}: {text}")
    if args.dry_run: continue
    try:
        if (lang, text) in made: shutil.copyfile(made[(lang, text)], f"{OUT_DIR}/{key}.mp3")
        else:
            audio = tts(text, VOICE[lang], MODEL, lang, SETTINGS, FORMAT)  # fetch first: a failed request must not leave an empty file
            open(f"{OUT_DIR}/{key}.mp3", "wb").write(audio)
            made[(lang, text)] = f"{OUT_DIR}/{key}.mp3"
        manifest[key] = signature(key, text)
    except Exception as e:
        failed.append(key); print(f"  FAILED {key}: {e}")
if not args.dry_run:
    json.dump(manifest, open(MANIFEST, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
if failed: sys.exit(f"{len(failed)} clips failed: {' '.join(failed)}. Re-run to retry just those.")

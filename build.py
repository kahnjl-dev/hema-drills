"""Build the drill caller: embed the drill data, guard photos and voice clips into
drill-caller.html, then copy it to index.html (the page GitHub Pages serves).

Run after editing drill-data.json, the photos, or the voice clips (generate_voice.py).
Re-runnable: each embedded block is replaced, never duplicated.
"""
import argparse, base64, io, json, os, re, sys
from PIL import Image
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

SOURCE, OUT = "drill-caller.html", "index.html"
DATA_FILE, PHOTO_DIR, CLIP_DIR = "drill-data.json", "photos", "voice-clips"
# The Swordsman's Companion photos must never reach the published page (no permission for those).
COMPANION_PHOTO_DIR = "guard-photos"

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--dry-run", action="store_true", help="report what would change without writing")
parser.add_argument("--verbose", action="store_true")
args = parser.parse_args()

def fail(msg): sys.exit(f"build.py: {msg}")

data = json.load(open(DATA_FILE, encoding="utf-8"))
guards, remedies = data["guards"], data["remedies"]

# Check the data hangs together before building on it.
for r in remedies:
    for field in ("guard", "ends"):
        if r[field] not in guards: fail(f"remedy '{r['id']}' has unknown {field} '{r[field]}' in {DATA_FILE}")
    if len(r["it"]) != len(r["en"]): fail(f"remedy '{r['id']}' has {len(r['it'])} Italian lines but {len(r['en'])} English")
for dr in data.get("drills", []):
    if dr["type"] not in ("remedies", "sequence"): fail(f"drill '{dr['id']}' has unknown type '{dr['type']}'")
    for i, st in enumerate(dr.get("steps", [])):
        for field in ("guard", "ends"):
            if field in st and st[field] not in guards: fail(f"drill '{dr['id']}' step {i} has unknown {field} '{st[field]}'")
        if "guard" not in st and "cut" not in st: fail(f"drill '{dr['id']}' step {i} needs a guard or a cut")

# --- Guard photos ---
photos = {}
for g in guards.values():
    name = g["photo"]
    if name in photos: continue
    path = os.path.join(PHOTO_DIR, name + ".jpg")
    if not os.path.exists(path): fail(f"missing photo {path} (guard photo '{name}')")
    w, h = Image.open(path).size
    photos[name] = {"src": "data:image/jpeg;base64," + base64.b64encode(open(path, "rb").read()).decode(), "w": w, "h": h}

# --- Voice clips: only the keys the data actually uses ---
needed = ["done-en"] + [f"g-{k}-{l}" for k in guards for l in ("it", "en")] + [f"r-{r['id']}-{l}" for r in remedies for l in ("it", "en")]
needed += [f"s-{dr['id']}-{i}-{l}" for dr in data.get("drills", []) for i, st in enumerate(dr.get("steps", [])) if "guard" not in st for l in ("it", "en")]
clips, missing, first_with = {}, [], {}
for key in needed:
    path = os.path.join(CLIP_DIR, key + ".mp3")
    if not os.path.exists(path): missing.append(key); continue
    raw = open(path, "rb").read()
    # Many calls share a recording (the same phrase from different guards); embed it once.
    if raw in first_with: clips[key] = "@" + first_with[raw]
    else: first_with[raw] = key; clips[key] = "data:audio/mpeg;base64," + base64.b64encode(raw).decode()

# --- Splice into the page ---
src = open(SOURCE, encoding="utf-8").read()
def put(text, marker_re, block, insert_before):
    """Replace the block matching marker_re, or insert it before insert_before."""
    m = re.search(marker_re, text, re.S)
    if m: return text[:m.start()] + block + text[m.end():]
    i = text.find(insert_before)
    if i < 0: fail(f"can't find where to insert {block[:40]}…")
    return text[:i] + block + "\n" + text[i:]

src = put(src, r'<script type="application/json" id="drill-data">.*?</script>',
          '<script type="application/json" id="drill-data">' + json.dumps(data, ensure_ascii=False) + '</script>', "<script>\n(function () {")
src = put(src, r'<script>window\.(?:BOOK_IMG|GUARD_PHOTOS) = .*?;</script>',
          "<script>window.GUARD_PHOTOS = " + json.dumps(photos) + ";</script>", "<script>\n(function () {")
src = put(src, r'<script>window\.VOICE_CLIPS = .*?\};</script>',
          "<script>window.VOICE_CLIPS = {\n" + ",\n".join(f'"{k}": "{v}"' for k, v in clips.items()) + "\n};</script>", "<script>\n(function () {")

# Only the seven-swords figure is still drawn from Fiore; drop the rest.
m = re.search(r'<script>window\.FIORE_IMG = (.*?);</script>', src)
if not m: fail("can't find FIORE_IMG")
fiore = json.loads(m.group(1))
if "segno" not in fiore: fail("FIORE_IMG has no segno (cut diagram)")
src = src.replace(m.group(0), "<script>window.FIORE_IMG = " + json.dumps({"segno": fiore["segno"]}) + ";</script>")

# Safety: no Companion photo may survive into the page.
if os.path.isdir(COMPANION_PHOTO_DIR):
    for photo in os.listdir(COMPANION_PHOTO_DIR):
        sample = base64.b64encode(open(os.path.join(COMPANION_PHOTO_DIR, photo), "rb").read()).decode()[:2000]
        if sample in src: fail(f"a Swordsman's Companion photo ({photo}) is still embedded; it must not be published")

print(f"guards {len(guards)}, remedies {len(remedies)}, photos {len(photos)}, clips {len(clips)}/{len(needed)} ({len(first_with)} distinct recordings)")
if missing: print(f"  {len(missing)} calls have no clip yet and will use the phone's voice: {' '.join(missing[:8])}{' …' if len(missing) > 8 else ''}")
print(f"  {SOURCE} and {OUT}: {len(src.encode()) // 1024} KB")
if args.dry_run: print("Dry run, nothing written.")
else:
    for f in (SOURCE, OUT): open(f, "w", encoding="utf-8", newline="\n").write(src)

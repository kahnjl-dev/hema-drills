"""Build index.html, the public GitHub Pages version of drill-caller.html.

The private app embeds photos from The Swordsman's Companion, which can't be shared publicly.
This build drops them (BOOK_IMG becomes empty) and embeds Fiore's public-domain drawings
from fiore-drawings/ instead; the app falls back to those automatically.
"""
import argparse, base64, io, json, os, re, sys
from PIL import Image
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

SOURCE, OUT = "drill-caller.html", "index.html"
# FIORE_IMG key -> drawing file. Matches the app's original mapping; note "Iron Gate" is used
# for tutta and "Middle Iron Gate" for mezza, as the first version of the app did.
DRAWINGS = {
    "donna": "Lady's Guard.jpg", "finestra": "Window Guard.png", "frontale": "Crown Guard.png",
    "longa": "Long Guard.png", "breve": "Short Guard.png", "tutta": "Iron Gate.png",
    "mezza": "Middle Iron Gate.png", "dente": "Boar's Tusk.png", "coda": "Long Tail.png",
    "bicorno": "Two-Horned Guard.png",
}
MAX_WIDTH = 640  # what the original embedded drawings used; plenty for a phone
PUBLIC_CREDITS = ('<p class="note" id="credits">Voices generated with <a href="https://elevenlabs.io" style="color: inherit;">'
                  'ElevenLabs</a>. Figures from Fiore dei Liberi\'s <i>Fior di Battaglia</i> (public domain).</p>')

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--dry-run", action="store_true", help="report what would be written")
parser.add_argument("--verbose", action="store_true")
args = parser.parse_args()

def encode(path):
    im = Image.open(path).convert("RGB")
    if im.width > MAX_WIDTH:
        im = im.resize((MAX_WIDTH, round(im.height * MAX_WIDTH / im.width)), Image.LANCZOS)
    buf = io.BytesIO(); im.save(buf, "JPEG", quality=85)
    return {"src": "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode(), "w": im.width, "h": im.height}

src = open(SOURCE, encoding="utf-8").read()
lines = src.split("\n")
fiore_i = next((i for i, l in enumerate(lines) if l.startswith("<script>window.FIORE_IMG = ")), None)
book_i = next((i for i, l in enumerate(lines) if l.startswith("<script>window.BOOK_IMG = ")), None)
if fiore_i is None or book_i is None:
    sys.exit(f"Couldn't find the FIORE_IMG and BOOK_IMG script lines in {SOURCE}.")

fiore = json.loads(lines[fiore_i][len("<script>window.FIORE_IMG = "):-len(";</script>")])
for key, name in DRAWINGS.items():
    path = os.path.join("fiore-drawings", name)
    if not os.path.exists(path): sys.exit(f"Missing Fiore drawing for '{key}': {path}")
    fiore[key] = encode(path)
    if args.verbose: print(f"  {key}: {name} -> {fiore[key]['w']}x{fiore[key]['h']}")
lines[fiore_i] = "<script>window.FIORE_IMG = " + json.dumps(fiore) + ";</script>"
lines[book_i] = "<script>window.BOOK_IMG = {};</script>"
out = "\n".join(lines)

credits = re.search(r'<p class="note" id="credits">.*?</p>', out)
if not credits: sys.exit(f"Couldn't find the credits line in {SOURCE}.")
out = out.replace(credits.group(0), PUBLIC_CREDITS)

# Safety check: none of the book's photos may survive into the public file.
for photo in os.listdir("guard-photos") if os.path.isdir("guard-photos") else []:
    data = base64.b64encode(open(os.path.join("guard-photos", photo), "rb").read()).decode()
    if data[:2000] in out:
        sys.exit(f"Aborting: book photo {photo} would be published in {OUT}.")
if "personal copy, not for sharing" in out:
    sys.exit(f"Aborting: {OUT} still has the private build's credits line.")

print(f"{OUT}: {len(out.encode())//1024} KB, Fiore drawings: {', '.join(DRAWINGS)}; book photos: none")
if args.dry_run: print("Dry run, nothing written.")
else: open(OUT, "w", encoding="utf-8", newline="\n").write(out)

"""Embed voice-clips/*.mp3 into drill-caller.html as window.VOICE_CLIPS (key -> data URI).
Re-runnable: an existing VOICE_CLIPS script line is replaced, not duplicated."""
import argparse, base64, glob, io, os, sys
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HTML, PREFIX = "drill-caller.html", "<script>window.VOICE_CLIPS = "
parser = argparse.ArgumentParser()
parser.add_argument("--dry-run", action="store_true", help="report what would change without writing")
parser.add_argument("--verbose", action="store_true")
args = parser.parse_args()

clips = {}
for path in sorted(glob.glob("voice-clips/*.mp3")):
    key = os.path.splitext(os.path.basename(path))[0]
    clips[key] = "data:audio/mpeg;base64," + base64.b64encode(open(path, "rb").read()).decode()
    if args.verbose: print(f"  {key}: {os.path.getsize(path)//1024} KB")
if not clips: sys.exit("No clips in voice-clips/ — run generate_voice.py first.")

# One key per line keeps the HTML diffable and the line readable in an editor.
line = PREFIX + "{\n" + ",\n".join(f'"{k}": "{v}"' for k, v in clips.items()) + "\n};</script>"
src = open(HTML, encoding="utf-8").read()
start = src.find(PREFIX)
if start >= 0:
    end = src.index("</script>", start) + len("</script>")
    out = src[:start] + line + src[end:]
else:
    anchor = src.find("<script>window.BOOK_IMG = ")
    if anchor < 0: sys.exit(f"Couldn't find where to insert clips in {HTML} (no BOOK_IMG line).")
    anchor = src.index("\n", anchor) + 1
    out = src[:anchor] + line + "\n" + src[anchor:]

print(f"{len(clips)} clips; file size {os.path.getsize(HTML)//1024} KB -> {len(out.encode())//1024} KB")
if args.dry_run: print("Dry run, nothing written.")
else: open(HTML, "w", encoding="utf-8", newline="\n").write(out)

"""Which spoken calls the app needs, and the clip key for each.

Shared by generate_voice.py (makes the clips) and build.py (embeds them) so the two can't
disagree about clip names. Keys:
  g-<guard>-<lang>              guard name
  r-<remedy>-<lang>             defense-and-riposte (or attack) from a guard
  s-<drill>-<n>-<lang>          step n of a fixed-sequence drill
  o-<drill>-<outcome>-<n>-<lang> step n of one outcome in an outcomes drill
  p-<drill>-<item>-<lang>       one call from a staged drill's pool
  t-<term>-<lang>               a building-blocks term: Italian term / English term and meaning
  done-en                       end of session
A step that names a "guard" and has no text of its own is spoken with that guard's g- clip.
"""

def join_lines(lines, lang):
    """How a multi-line call is spoken: Italian joined with commas, English with ", then"."""
    rest = [l[0].lower() + l[1:] for l in lines[1:]]
    return ", ".join([lines[0]] + rest) if lang == "it" else ", then ".join([lines[0]] + rest)

def term_spoken_en(t):
    """English for a building-blocks term: the term, then what it means."""
    return f"{t['en']}. {t['means']}"

def step_uses_guard_clip(step):
    return "guard" in step

def drill_steps(drill):
    """(clip key prefix, step) for every spoken step in a drill, in a stable order."""
    d = drill["id"]
    if drill["type"] == "sequence":
        for i, st in enumerate(drill["steps"]): yield f"s-{d}-{i}", st
    elif drill["type"] == "outcomes":
        for i, st in enumerate(drill.get("start", [])): yield f"s-{d}-start{i}", st
        for o in drill["outcomes"]:
            for i, st in enumerate(o["steps"]): yield f"o-{d}-{o['id']}-{i}", st
    elif drill["type"] == "staged":
        for i, st in enumerate(drill.get("start", [])): yield f"s-{d}-start{i}", st
        for item in drill["pool"]: yield f"p-{d}-{item['id']}", item

def phrases(data):
    """Every (key, lang, text) the app can speak."""
    out = []
    for k, g in data["guards"].items():
        out += [(f"g-{k}-it", "it", g["it"]), (f"g-{k}-en", "en", g["en"])]
    for r in data["remedies"] + data.get("attacks", []):
        out += [(f"r-{r['id']}-it", "it", join_lines(r["it"], "it")), (f"r-{r['id']}-en", "en", join_lines(r["en"], "en"))]
    for drill in data.get("drills", []):
        for key, st in drill_steps(drill):
            if step_uses_guard_clip(st): continue
            out += [(f"{key}-it", "it", st["it"]), (f"{key}-en", "en", st["en"])]
    for t in data.get("terms", []):
        if t["it"]: out.append((f"t-{t['id']}-it", "it", t["it"]))
        out.append((f"t-{t['id']}-en", "en", term_spoken_en(t)))
    out.append(("done-en", "en", "Done"))
    return out

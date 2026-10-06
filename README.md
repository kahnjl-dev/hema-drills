# HEMA Drills: Drill Caller

A phone-friendly drill caller for Fiore dei Liberi's longsword, following Guy Windsor's *The Medieval Longsword*. Set your phone down, tap Start, and it calls a guard, then a defense and riposte from that guard (or a thrust, from the centreline guards), with the footwork.

**Run it:** https://kahnjl-dev.github.io/hema-drills/

- Guards and calls follow the book's rules for a right-handed fencer: each defense leads to the riposte the book teaches, and every guard gets practiced evenly.
- Speed, session length (time or number of exchanges), and language (Italian, English, or both in either order).
- Recorded voice calls in Italian and English, with the phone's text-to-speech as a fallback.
- Keeps the screen awake while running, where the browser allows it.

## Credits

- Drills follow Guy Windsor's *The Medieval Longsword* ([swordschool.com](https://swordschool.com)).
- Guard photos by Jari Juslin, from *The Medieval Longsword*, used with permission. See `photos/CREDITS.md`.
- Cut diagram from Fiore dei Liberi's *Fior di Battaglia* (public domain).
- Voices generated with [ElevenLabs](https://elevenlabs.io).

## Building

- `drill-data.json`: every guard and call, with book page references. Edit this to change what the app calls.
- `generate_voice.py`: makes a voice clip for every call in the data (only new or changed wording). Needs an ElevenLabs API key in `ELEVENLABS_API_KEY`.
- `build.py`: embeds the data, photos and clips into `drill-caller.html` and writes `index.html`, the page GitHub Pages serves.

# HEMA Drills: Drill Caller

A phone-friendly drill caller for Fiore dei Liberi's longsword. Set your phone down, tap Start, and it calls a guard, then a defense and strike, chaining each attack into the guard it ends in.

**Run it:** https://kahnjl-dev.github.io/hema-drills/

- Speed, session length (time or number of exchanges), and language (Italian, English, or both in either order)
- Recorded voice calls (Italian and English), with the phone's text-to-speech as a fallback
- Keeps the screen awake while running, where the browser allows it

## Credits

- Voices generated with [ElevenLabs](https://elevenlabs.io).
- Figures from Fiore dei Liberi's *Fior di Battaglia* (public domain).

## Building

`index.html` is a single self-contained file built from a private working copy:

- `generate_voice.py`: generates the voice clips with ElevenLabs. Needs an API key in `ELEVENLABS_API_KEY`.
- `embed_voice.py`: embeds the clips into the app.
- `build_public.py`: produces `index.html` with Fiore's drawings from `fiore-drawings/`.

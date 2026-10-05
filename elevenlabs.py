"""Minimal ElevenLabs text-to-speech client. Reads the key from 'eleven labs api key.txt'
(or ELEVENLABS_API_KEY) so it never has to appear in code or command lines."""
import json, os, re, urllib.error, urllib.request

KEY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "eleven labs api key.txt")

def api_key():
    if os.environ.get("ELEVENLABS_API_KEY"):
        return os.environ["ELEVENLABS_API_KEY"]
    m = re.search(r"sk_\w+", open(KEY_FILE, encoding="utf-8-sig").read())
    if not m:
        raise SystemExit(f"No ElevenLabs key (sk_...) found in {KEY_FILE}")
    return m.group(0)

def tts(text, voice_id, model_id="eleven_multilingual_v2", language_code=None, voice_settings=None,
        output_format="mp3_44100_128"):
    """Return MP3 bytes for text. language_code forces pronunciation on models that support it."""
    body = {"text": text, "model_id": model_id}
    if language_code: body["language_code"] = language_code
    if voice_settings: body["voice_settings"] = voice_settings
    req = urllib.request.Request(
        f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}?output_format={output_format}",
        data=json.dumps(body).encode(), headers={"xi-api-key": api_key(), "Content-Type": "application/json"})
    try:
        return urllib.request.urlopen(req).read()
    except urllib.error.HTTPError as e:
        detail = e.read().decode(errors="replace")[:300]
        raise RuntimeError(f"ElevenLabs TTS failed ({e.code}) for voice {voice_id}, model {model_id}: {detail}")

"""Text-to-speech: browser speechSynthesis (primary) and optional offline pyttsx3 (server-side fallback)."""
from __future__ import annotations

import json
import re

import streamlit.components.v1 as components


def plain_text_for_speech(text: str) -> str:
    """Remove markdown/emoji-ish formatting and demo-mode prefixes so speech sounds natural."""
    text = re.sub(r"\*\*\[[^\]]*\]\*\*", "", text)
    text = re.sub(r"[*_`#>]", "", text)
    text = re.sub(r"\(Simulated[^)]*\)", "", text)
    return re.sub(r"\s+", " ", text).strip()


_HTML = """
<div style="font-family:system-ui,sans-serif">
 <button id="play" style="background:#0B2545;color:#fff;border:0;border-radius:20px;padding:6px 14px;cursor:pointer">🔊 Read aloud</button>
 <button id="stop" style="margin-left:6px;border:1px solid #0B2545;background:#fff;color:#0B2545;border-radius:20px;padding:5px 12px;cursor:pointer">⏹ Stop</button>
 <span id="msg" style="margin-left:8px;font-size:13px;color:#4a5b73"></span>
</div>
<script>
const TEXT = __TEXT__;
const msg = document.getElementById('msg');
if (!('speechSynthesis' in window)) {
  document.getElementById('play').disabled = true;
  msg.textContent = 'Speech playback is not supported in this browser.';
} else {
  document.getElementById('play').onclick = () => {
    window.speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(TEXT); u.lang = 'en-GB';
    u.onend = () => msg.textContent = ''; u.onerror = () => msg.textContent = 'Playback failed.';
    msg.textContent = 'Speaking...'; window.speechSynthesis.speak(u);
  };
  document.getElementById('stop').onclick = () => { window.speechSynthesis.cancel(); msg.textContent = 'Stopped.'; };
}
</script>
"""


def render_speech_controls(text: str, height: int = 48) -> None:
    components.html(_HTML.replace("__TEXT__", json.dumps(plain_text_for_speech(text))), height=height)


def offline_tts_available() -> bool:
    try:
        import pyttsx3  # noqa: F401
        return True
    except Exception:  # noqa: BLE001
        return False


def speak_offline(text: str) -> bool:
    """Speak on the machine running Streamlit (useful for local demos). Returns False if unavailable."""
    try:
        import pyttsx3
        engine = pyttsx3.init()
        engine.say(plain_text_for_speech(text))
        engine.runAndWait()
        return True
    except Exception:  # noqa: BLE001
        return False

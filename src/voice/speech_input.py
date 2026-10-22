"""Browser speech-to-text widget (Web Speech API).

Works in browsers that expose SpeechRecognition (Chrome/Edge; Safari partially). Firefox does not.
The transcript is shown immediately and (best effort) inserted into the Streamlit message box so the
user can EDIT it before sending. If insertion is blocked, the transcript box has a Copy button.
The text workflow always remains available. This is a browser demo, not telephony."""
from __future__ import annotations

import streamlit.components.v1 as components

_HTML = """
<div style="font-family:system-ui,sans-serif;font-size:14px;color:#0B2545">
  <button id="mic" style="background:#13A89E;color:#fff;border:0;border-radius:20px;padding:8px 16px;cursor:pointer;font-weight:600">🎤 Start speaking</button>
  <button id="copy" style="display:none;margin-left:6px;border:1px solid #13A89E;background:#fff;color:#0B2545;border-radius:20px;padding:7px 12px;cursor:pointer">Copy text</button>
  <div id="status" style="margin-top:6px;color:#4a5b73">Click the microphone and speak. Your browser may ask for permission.</div>
  <div id="out" style="margin-top:6px;padding:6px 8px;background:#eef7f6;border-radius:8px;display:none"></div>
</div>
<script>
const LABEL = __LABEL__;
const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
const mic = document.getElementById('mic'), st = document.getElementById('status'),
      out = document.getElementById('out'), copy = document.getElementById('copy');
function fillParent(text) {
  try {
    const ta = window.parent.document.querySelector('textarea[aria-label="' + LABEL + '"]');
    if (!ta) return false;
    const setter = Object.getOwnPropertyDescriptor(window.parent.HTMLTextAreaElement.prototype, 'value').set;
    setter.call(ta, text);
    ta.dispatchEvent(new Event('input', {bubbles: true}));
    return true;
  } catch (e) { return false; }
}
if (!SR) {
  mic.disabled = true; mic.style.opacity = .5;
  st.textContent = 'Speech recognition is not supported in this browser. Please type your question instead (try Chrome or Edge for voice).';
} else {
  const rec = new SR(); rec.lang = 'en-GB'; rec.interimResults = true; rec.continuous = false;
  let listening = false, finalText = '';
  mic.onclick = () => { if (listening) { rec.stop(); return; } finalText = ''; try { rec.start(); } catch (e) {} };
  rec.onstart = () => { listening = true; mic.textContent = '⏹ Stop'; st.textContent = 'Listening...'; };
  rec.onresult = (ev) => {
    let t = ''; for (const r of ev.results) { t += r[0].transcript; if (r.isFinal) finalText = t; }
    out.style.display = 'block'; out.textContent = t; copy.style.display = 'inline-block';
  };
  rec.onerror = (ev) => {
    const m = {'not-allowed': 'Microphone permission was denied. Allow microphone access in your browser, or type instead.',
               'service-not-allowed': 'Speech service blocked by the browser. Type your question instead.',
               'no-speech': 'No speech detected. Try again.', 'audio-capture': 'No microphone found.',
               'network': 'Speech recognition needs a network connection in this browser.'};
    st.textContent = m[ev.error] || ('Speech error: ' + ev.error);
  };
  rec.onend = () => {
    listening = false; mic.textContent = '🎤 Start speaking';
    const text = (out.textContent || '').trim();
    if (text) { st.textContent = fillParent(text) ? 'Transcript added to the message box below - edit it if needed, then press Send.'
                                               : 'Transcript ready - use Copy text and paste it into the box below.'; }
  };
  copy.onclick = () => { navigator.clipboard && navigator.clipboard.writeText(out.textContent); st.textContent = 'Copied.'; };
}
</script>
"""


def render_mic_widget(textarea_label: str, height: int = 150) -> None:
    import json
    components.html(_HTML.replace("__LABEL__", json.dumps(textarea_label)), height=height)

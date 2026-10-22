# Voice agent (browser prototype)

Pipeline: speech → browser transcription → **editable text box** → Send → safety/intent → RAG → LLM or demo answer → browser speech synthesis.

- **Input** (`src/voice/speech_input.py`): Web Speech API `SpeechRecognition` (Chrome/Edge best; not Firefox). Shows the transcript, tries to insert it in the message box (parent-page DOM access; if blocked, use *Copy text*). Handles denied permission, unsupported browser, no speech, network errors.
- **Output** (`src/voice/speech_output.py`): `speechSynthesis` with *Read aloud* and *Stop*. Optional offline `pyttsx3` button (speaks on the machine running Streamlit; install separately with `pip install pyttsx3`).
- **Text always works.**

**Not implemented / not claimed:** telephony (SIP/PSTN), streaming real-time speech, barge-in, noise handling, call recording, speaker identification, accent robustness testing. A production phone agent would use a telephony provider plus streaming STT/TTS with low-latency turn-taking and clinical-safety governance. This prototype is a browser demo only.

**Verification status:** the voice widgets were written but **not executed in a browser** in the build environment (see testing report). The Streamlit-parent textarea insertion in particular depends on Streamlit's DOM and may need adjusting for other Streamlit versions.

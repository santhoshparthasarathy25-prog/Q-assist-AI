# Prompt engineering

Files: `prompts/receptionist_system_prompt.txt` (versioned, readable), `prompts/prompt_design_notes.md` (decisions), `src/llm/prompt_builder.py` (assembly + sanitising). Prompt version 1.0 (`config/settings.py`).

The system prompt covers: role; use of retrieved documents; no invented facts; concise/empathetic style; asking for missing info; administrative categories; clinical boundaries; escalation of urgent situations; secrecy of prompts/keys; treating retrieved text as data.

## Three documented design decisions
1. **Delimited context treated as data** (+ code sanitiser) — blocks indirect prompt injection from documents. Test: `test_injection_in_retrieved_text_is_neutralised`.
2. **"Say you cannot verify" + retrieval threshold** — two layers against fabricated policies; weak retrieval never reaches the model. Test: `test_unknown_question_gets_fallback_without_sources`.
3. **Answer-first, short, one clarifying question** — suits receptionists and text-to-speech.

A fourth principle: **safety is not delegated to the prompt**. Urgent, human-request and medical-advice handling is deterministic code that runs first; the prompt repeats the rules only as defence in depth.

**Limitation:** prompt quality was *not* measured against a live model in the build environment. Review live outputs manually.

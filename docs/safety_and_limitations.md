# Safety, privacy and limitations

**This is a fictional, NHS-inspired administrative demonstration. It is NOT NHS-approved, DTAC-certified, clinically validated, or compliant with NHS clinical safety standards (e.g. DCB0129/DCB0160). It performs no clinical triage.** Real deployment would need clinical governance, a clinical safety case, privacy/DPIA work, security review and regulatory assessment.

## Safety design
- Deterministic urgent-risk rules (`src/safety/safety_rules.py`) run first; the LLM is never consulted for them.
- Urgent response: general UK guidance (999 for emergencies, NHS 111 for urgent non-emergencies), clearly labelled as general guidance rather than the fictional clinic's policy.
- Medical-advice requests (doses, diagnosis, "should I stop…") are declined and signposted.
- Escalations are simulated; the stored reason is a category (e.g. `urgent_phrase:chest_pain`), and urgent message text is not stored.
- No AI-generated diagnosis, treatment or medication advice; no claim that anything was booked, issued or sent.

## Known limitations
- **Keyword rules** miss paraphrases ("my chest feels like it's being squeezed") and ignore negation ("I do not have chest pain" still escalates). The design prefers false alarms. The phrase list is small and not clinically reviewed.
- **Intent classifier** is rule-based: limited vocabulary; `rule_matches` is a count, not a calibrated probability.
- **TF-IDF fallback** is lexical: it misses plural/synonym differences (e.g. "complaint" vs "complaints" was a measured miss). Sentence Transformers handles these better but its path was not run in the build sandbox.
- **Sessions:** a random session id lives in Streamlit `session_state`; history is read only by conversation id. This is isolation by design, **not authentication**: anyone with access to the running app/DB file can read stored data; no encryption at rest.
- **Redaction** is regex-based and incomplete; do not enter real personal data.
- **Single language (English)**, no accessibility audit of the UI beyond Streamlit defaults.
- **Voice:** browser prototype only (see `voice_agent.md`).
- **LLM:** answers from a live model can still be imperfect; the prompt and retrieval threshold reduce, not eliminate, errors.

## Security notes
API key only via environment/`.env` (git-ignored), never logged or stored. Retrieved documents are sanitised and delimited. The TF-IDF vectorizer is stored with `pickle` in `data/storage/index/` — it is written and read only by this app; do not load index files from untrusted sources.

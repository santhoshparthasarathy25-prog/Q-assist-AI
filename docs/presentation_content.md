# Q-assist AI - 7-slide mini-project presentation

> Note: the brief was cut off mid-way through this section, so each slide below provides: **title, key points, speaker notes, and a suggested visual**. Adjust if your template differs.

## Slide 1 - Title and introduction
**Title:** Q-assist AI - Intelligent Healthcare Receptionist Assistant
- LLM + RAG + prompt engineering + NLP + voice
- Inspired by challenges tackled by AI receptionists in UK primary care (fictional clinic, simulated workflows)
- Built by: *[your name]* · AI/ML & Prompt Engineer mini-project
**Speaker notes:** "I built a working prototype showing how an AI receptionist can answer administrative questions from a knowledge base, safely escalate urgent language and log simulated requests. It is a demo, not a clinical product."
**Visual:** Logo/banner screenshot of the Chat page.

## Slide 2 - Problem statement and motivation
- Reception phone lines are overloaded at peak times (8am rush); many calls are routine admin questions
- Answers must be consistent, grounded in clinic policy, and safe
- LLMs can hallucinate - risky when facts or safety matter
**Speaker notes:** "The challenge isn't just chatting; it's accuracy, safety and traceability."
**Visual:** Simple before/after: queue of calls vs assistant handling routine questions.

## Slide 3 - Proposed solution and features
- Typed + spoken questions; grounded answers with visible sources
- Intent detection, request status, human-escalation indicator
- Deterministic urgent-risk escalation (999 / NHS 111 guidance)
- Dashboard from real stored data; knowledge-base management; evaluation page
- Works in **demo mode** without an API key (clearly labelled)
**Speaker notes:** Demo flow: ask opening hours → show source panel → type "chest pain" → show escalation → open dashboard.
**Visual:** Screenshot montage of Chat, Dashboard, Knowledge base.

## Slide 4 - System architecture and data flow
- Streamlit UI → ReceptionistService → [safety → intent → RAG → prompt → Gemini/demo] → workflow router → SQLite
- Safety runs before the LLM; weak retrieval returns a fallback without calling the LLM
**Speaker notes:** Walk through `docs/architecture_diagram.mmd`; stress "separation of concerns" and "LLM only sees vetted context".
**Visual:** Render the Mermaid architecture diagram.

## Slide 5 - LLM, RAG, prompt engineering, NLP and voice
- **RAG:** chunking, embeddings (MiniLM, TF-IDF fallback), persistent index, similarity threshold, citations
- **Prompting:** versioned system prompt; delimited context treated as data; "cannot verify" rule; injection sanitiser
- **NLP:** transparent rule-based intents with reasons (rule-match count ≠ probability)
- **LLM service:** Gemini via env config; timeouts/rate-limit/auth/network handled; honest demo fallback
- **Voice:** browser speech-to-text → editable text; speech synthesis; text always available
**Speaker notes:** Be ready to explain why safety isn't left to the prompt, and why a threshold beats trusting the model.
**Visual:** Table of module → technique.

## Slide 6 - Evaluation results and limitations
- 27 synthetic scenarios, LLM disabled: **27/27 passed** (development set, tuned after seeing first run: 24/27 before fixes)
- 12 fresh questions: **11/12** (miss: "complaint" vs "complaints" - keyword matching limit)
- Automated tests: 47 passed (DB tests, live API and UI not executed in the build sandbox)
- Latency: ~0.6 ms mean in demo mode (TF-IDF, local, no network) - not an LLM latency figure
- Limits: not clinically validated; keyword safety rules; no telephony; small synthetic KB
**Speaker notes:** Be upfront: results are on small synthetic data and indicate the pipeline works, not real-world accuracy.
**Visual:** Metrics table + "limitations" panel.

## Slide 7 - Conclusion and future scope
- Delivered an end-to-end, explainable, safe-by-design prototype
- Future: dense-embedding calibration, hybrid search + reranking, semantic safety classifier with clinical review, streaming telephony STT/TTS, authentication and audit logging, real system integrations behind governance, larger human-labelled evaluation
**Speaker notes:** Close with what you learned: grounding, safety layering, evaluation honesty.
**Visual:** Roadmap timeline.

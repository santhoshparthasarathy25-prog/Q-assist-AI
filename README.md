# Q-assist AI - Intelligent Healthcare Receptionist Assistant

> **Fictional demo. Not medical software.** Not NHS-approved, DTAC-certified or clinically validated. All clinic details are invented, workflows are simulated, and nothing contacts real systems. Please read `docs/testing_report.md` for exactly what was and was not verified.

## 1. Overview
Q-assist AI is a Streamlit mini-project that shows how an AI receptionist can: understand enquiries (NLP intents), answer from a local knowledge base (RAG), generate grounded replies with Gemini (prompt engineering), accept spoken questions and read answers aloud (browser voice), escalate urgent-risk language with deterministic rules, and log **simulated** requests in SQLite with a live dashboard. It is inspired by the problems AI receptionists such as QuantumLoopAI's EMMA address in UK primary care, but shares no code or data with it.

**Problem:** reception lines are overloaded with routine admin questions; answers must be consistent, grounded and safe.
**Objectives:** working end-to-end prototype · grounded answers with visible sources · safety before LLM · honest demo mode · measurable evaluation.

## 2. Features
Chat with sources, intent, request status and escalation indicators · voice input/output (browser) · RAG with threshold and fallback · demo mode without API key (labelled, never passed off as LLM) · dashboard from real DB data with filters · knowledge-base upload/re-index/search · evaluation page · settings/status page · session memory with a "clear conversation" button.

## 3. Technology stack
Python · Streamlit · Google Gen AI SDK (Gemini) · Sentence Transformers (MiniLM) with scikit-learn TF-IDF fallback · NumPy vector index (persistent) · SQLite + SQLAlchemy 2 · pypdf · python-dotenv · pytest. *Deviations from the brief:* NumPy index instead of FAISS/Chroma; no LangChain (custom pipeline); dataclasses instead of Pydantic.

## 4. Folder structure
```
app.py                     Streamlit entry point
config/settings.py         settings from env (no .env needed)
prompts/                   system prompt + design notes
src/llm/                   prompt_builder, llm_service, demo_responder
src/rag/                   loader, chunker, embeddings, vector_store, retriever, pipeline
src/nlp/                   intent_classifier
src/safety/                safety_rules, escalation
src/workflows/             request_router (simulated)
src/voice/                 speech_input, speech_output
src/database/              models, connection, repository, init_db
src/services/              receptionist, conversation, evaluation services
src/ui/                    pages + context
data/knowledge_base/       fictional clinic documents (TXT/PDF)
data/evaluation/ data/seed/ data/storage/   scenarios, seed questions, DB + index (generated)
tests/  docs/  scripts/
```

## 5. Requirements
Python **3.10-3.12** recommended (3.13 may lack wheels for some pinned versions). ~2 GB free disk if you install Sentence Transformers (PyTorch); use `requirements-lite.txt` otherwise. Internet is needed once to install packages and (optionally) download the ~90 MB embedding model.

## 6. Install and run - Windows PowerShell
From the extracted `Q-assist-AI` folder:
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1          # if blocked: Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
python -m pip install --upgrade pip
pip install -r requirements.txt       # lighter: pip install -r requirements-lite.txt
streamlit run app.py
```
## macOS / Linux
```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt       # or requirements-lite.txt
streamlit run app.py
```
The app opens at http://localhost:8501. **No `.env` is needed**: without an API key it runs in clearly labelled **demo mode**. The database (`data/storage/qassist.db`) and search index are created automatically on first start.

## 7. Optional: live Gemini answers
1. Create a key in Google AI Studio.
2. `Copy-Item .env.example .env` (PowerShell) or `cp .env.example .env`; set `GEMINI_API_KEY=...`.
3. Check the current stable model name at https://ai.google.dev/gemini-api/docs/models and set `GEMINI_MODEL` if needed (default `gemini-3.1-flash-lite`; older Gemini 2.5 models were scheduled for shutdown on 16 Oct 2026). If the SDK complains, `pip install -U google-genai`.
4. Restart the app; Settings → *Test LLM connection*.
Replies show **Live LLM** only when the model really answered; any failure shows demo mode plus the reason.

## 8. Useful commands (run from the project folder, venv active)
| Task | Command |
|---|---|
| Create DB (optional) | `python scripts/init_database.py` |
| Create DB + synthetic sample conversations | `python scripts/init_database.py --seed` |
| Index / update knowledge base | `python scripts/ingest_documents.py` (add `--force` to rebuild) |
| Run evaluation (optionally save to DB) | `python scripts/run_evaluation.py` (`--save`) |
| Fresh-question check | `python scripts/run_heldout_check.py` |
| Run tests | `pytest` (skips live API test) |
| Live API test (optional) | PowerShell: `$env:RUN_LIVE_TESTS="1"; pytest tests/test_live_api.py` |
| Reset demo data | `python scripts/reset_demo_data.py --yes` |

Add your own knowledge: drop `.txt`/`.pdf` files into `data/knowledge_base/` (or upload on the Knowledge base page); re-indexing only happens when files change.

## 9. Common errors
| Problem | Fix |
|---|---|
| `running scripts is disabled` (PowerShell) | `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` then activate again |
| `ModuleNotFoundError: src` | run commands from the project folder |
| pip fails on `torch` / very slow | use `requirements-lite.txt` (TF-IDF fallback) |
| "Sentence Transformers unavailable" note | offline or not installed → fallback is active; fine for the demo |
| `streamlit` not found | activate the venv; `pip install -r requirements.txt` |
| Mic button disabled / no transcript | use Chrome/Edge, allow microphone, or type instead |
| Transcript not inserted | use *Copy text* and paste into the message box |
| Answers say "Demo mode" | no/invalid API key (Settings page shows the reason) |
| Pinned version won't install | try a newer compatible version and report it |

## 10. Known limitations
See `docs/safety_and_limitations.md` and `docs/testing_report.md`. In short: keyword safety rules, rule-based intents, TF-IDF fallback is lexical, sessions are not authentication, voice is a browser prototype (no telephony), and **the database layer, UI and voice widgets were not executed during the build**.

## 11. Security and privacy
Fictional data only; don't type real personal/medical details. Key only via env/.env (git-ignored), never stored or displayed. Obvious identifiers redacted; urgent message text isn't stored. Retrieved documents are sanitised and treated as data. No encryption at rest.

## 12. Interview talking points
- Safety is deterministic code that runs *before* the LLM; the prompt is only defence in depth.
- RAG with a threshold: weak retrieval → fixed fallback, no model call, no invented citations.
- Honest demo mode: `answer_mode` live/demo/rule is stored and shown.
- Rule-match count ≠ probability; why I didn't invent confidence scores.
- Evaluation honesty: 24/27 first run → fixes → 27/27 on a tuned dev set, 11/12 on fresh questions; the miss is a TF-IDF plural limitation that dense embeddings should address.
- Trade-offs: NumPy index vs FAISS, rules vs ML classifier, browser voice vs telephony.
- Prompt-injection defences: delimiters, sanitiser, "data not instructions", user-input check.

## 13. Future improvements
Calibrate dense-embedding threshold · hybrid search + reranking · semantic, clinically reviewed safety classifier · streaming telephony voice · authentication, audit logs, encryption · larger human-labelled evaluation · LangChain/Chroma/FAISS variants · multilingual support.

Docs index: `docs/architecture.md`, `architecture_diagram.mmd`, `database_schema.md`, `database_erd.mmd`, `rag_pipeline.md`, `prompt_engineering.md`, `voice_agent.md`, `safety_and_limitations.md`, `testing_report.md`, `presentation_content.md`.

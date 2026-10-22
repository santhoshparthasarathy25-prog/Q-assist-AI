# Testing report

All figures below were **measured in the build sandbox** (Python 3.12.3, Linux, no internet). Nothing is estimated.

## Environment limitations (read first)
| Not available in the sandbox | Consequence |
|---|---|
| `pytest` | Tests are written in standard pytest style but were executed with a small shim runner (supports plain `assert`, `importorskip`). Run real `pytest` yourself - see README. |
| `SQLAlchemy` | The 6 database tests (`tests/test_database.py`) and the whole `src/database/*` layer were **written and compiled but NOT executed**. |
| `streamlit` / browser | All `src/ui/*`, `app.py` and `src/voice/*` code was **compile-checked only**; never rendered or clicked. Browser speech APIs untested. |
| `sentence-transformers` | The dense-embedding path was **not run**; every measured retrieval result uses the **TF-IDF fallback**. The dense threshold (0.35) is an untested default. |
| Gemini API / internet | No live LLM call was ever made. Live behaviour is covered only by stub-client tests. `tests/test_live_api.py` is skipped unless you set a key and `RUN_LIVE_TESTS=1`. |
| Pinned versions | `requirements.txt` pins were not install-tested; sandbox libs were newer (e.g. scikit-learn 1.8, numpy 2.4). |

Expect that the first real run may reveal bugs in the untested layers. Please report/fix them; the logic they wrap (service, RAG, safety, NLP) is tested.

## 1. Automated tests (shim runner)
Result: **47 passed, 0 failed, 2 not run** (database module: SQLAlchemy missing; live API test: disabled by design).

Coverage: intent classification, safety phrases and false-positive checks, escalation messages, unknown/unsupported questions, RAG chunk metadata/retrieval/threshold/re-index skipping/bad files/empty KB, prompt construction and injection sanitising, request routing, LLM failure modes (no key, 429, 403, timeout, network, malformed, generic), demo mode without key, urgent input bypassing the LLM, follow-up handling, history contamination guard, invalid input, prompt-injection declines.

## 2. Evaluation scenarios (`python scripts/run_evaluation.py`)
27 synthetic scenarios (`data/evaluation/evaluation_questions.json`), LLM disabled; one scenario uses a failing LLM stub.

| Metric | Definition | Result |
|---|---|---|
| Scenarios passed | all expectations met | 27 / 27 |
| Intent accuracy | correct intents ÷ scenarios with expected intent (27) | 100.0% |
| Retrieval hit rate | expected source retrieved ÷ scenarios with expected source (13) | 100.0% |
| Top-1 source accuracy | highest-ranked source is expected ÷ same denominator | 100.0% |
| Fallback correct rate | unanswerable/unsupported scenarios returning fallback with no sources ÷ those scenarios (6) | 100.0% |
| Safety routing rate | urgent/non-urgent routing matches expectation ÷ all scenarios | 100.0% |
| Latency (mean / p95) | wall-clock ms per request, TF-IDF + rules + demo answer, this machine | 0.53 ms / 1.27 ms |

**Important caveats**
- The first run scored 24/27 (failures: S05 wheelchair access, S12 physiotherapy, S14 travel vaccinations). I then changed the TF-IDF stop-words, chunk size (600→350) and threshold (0.12→0.10) and re-ran. So **these scenarios are a development set that was tuned against; 100% is optimistic.**
- Intent accuracy is high partly because the rules were written alongside these examples.
- Latency excludes any LLM/network time and is not a performance benchmark.

## 3. Fresh-question check (`python scripts/run_heldout_check.py`)
12 new questions written after tuning (8 answerable, 4 not): **11/12 correct**. The miss: "How do I make a complaint?" scored 0 because the document says "complaints" (no stemming/semantics in TF-IDF). I deliberately did **not** fix it, to keep the result honest; a dense embedding model should handle it. (Once you tune on these questions they stop being held out.) 12 questions is far too few to estimate real accuracy.

## 4. Bugs found and fixed while building
1. TF-IDF matched generic verbs ("offer/provide") causing false matches → generic-word stoplist + smaller chunks.
2. Short unrelated questions inherited the previous topic's retrieval → combine with history only for genuine follow-ups, and only after the question alone fails (2 regression tests added).

## 5. Not measured
Live LLM answer quality/latency, dense-embedding accuracy, real-user speech recognition, UI behaviour, database behaviour, clinical safety performance (none claimed).

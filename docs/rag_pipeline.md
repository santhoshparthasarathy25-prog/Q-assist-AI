# RAG pipeline

| Stage | Module | Notes |
|---|---|---|
| 1 Load | `document_loader.py` | TXT and PDF (pypdf). Bad/scanned files are skipped with a warning. |
| 2 Clean + chunk | `chunker.py` | Paragraph-aware, ~350 chars, 60 char overlap for long paragraphs; headings merged with the next paragraph; IDs like `sample_clinic_faq.txt::0003`. |
| 3 Embed | `embeddings.py` | `all-MiniLM-L6-v2` via Sentence Transformers (one-off ~90 MB download), else TF-IDF fallback. |
| 4 Store | `vector_store.py` | Exact cosine search in NumPy; saved to `data/storage/index/`. **Deviation:** the brief suggested FAISS/Chroma; for a few hundred chunks NumPy is simpler and has no native dependencies. The interface is FAISS-like for a later swap. |
| 5 Retrieve | `retriever.py` | top-k (default 3). |
| 6 Quality check | `retriever.py` | Explicit similarity threshold; below it the result is "not reliable". |
| 7-8 Generate | `receptionist_service.py` + `src/llm` | Only reliable chunks reach the prompt. |
| 9 Cite | UI source panel | Sources shown are exactly the retrieved chunks above threshold - never invented. |
| 10 Fallback | `escalation.NO_VERIFIED_INFO_MESSAGE` | No LLM call when retrieval is weak. |

**Avoiding repeated indexing:** `data/storage/index/manifest.json` stores the embedder name and a SHA-256 per file. `ingest()` returns `up_to_date` unless a file changed, was added/removed, or `force=True`.

**Thresholds:** TF-IDF 0.10 (calibrated on this small synthetic set — see testing report) and dense 0.35 (**an untested default**; recalibrate on your data via `THRESHOLD_DENSE`).

**Download note:** the first run with Sentence Transformers downloads the model from Hugging Face. If offline, the app falls back to TF-IDF automatically (Settings page shows which is active). Use `requirements-lite.txt` to avoid installing PyTorch.

**Security:** retrieved text is data. `prompt_builder.sanitise_context` removes instruction-like lines and look-alike tags before prompting.

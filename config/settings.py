"""Central configuration. Values come from environment variables (optionally a .env file).
No .env file is required: every setting has a safe default, so demo mode works out of the box."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # python-dotenv is optional at runtime
    load_dotenv = None

ROOT = Path(__file__).resolve().parent.parent
if load_dotenv:
    load_dotenv(ROOT / ".env")

PROMPT_VERSION = "1.0"


def _float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, default))
    except ValueError:
        return default


def _int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, default))
    except ValueError:
        return default


@dataclass(frozen=True)
class Settings:
    gemini_api_key: str
    gemini_model: str
    llm_timeout_seconds: float
    embedding_backend: str
    embedding_model: str
    retrieval_top_k: int
    log_level: str
    max_input_chars: int
    history_turns: int
    # similarity thresholds are per embedding backend because score scales differ
    threshold_tfidf: float
    threshold_dense: float
    kb_dir: Path
    storage_dir: Path
    eval_file: Path
    seed_file: Path
    prompt_file: Path
    db_path: Path

    @property
    def llm_configured(self) -> bool:
        return bool(self.gemini_api_key.strip())


def get_settings() -> Settings:
    """Read settings fresh each call so tests can change environment variables."""
    storage = ROOT / "data" / "storage"
    return Settings(
        gemini_api_key=os.getenv("GEMINI_API_KEY", ""),
        gemini_model=os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite"),
        llm_timeout_seconds=_float("LLM_TIMEOUT_SECONDS", 20.0),
        embedding_backend=os.getenv("EMBEDDING_BACKEND", "auto").lower(),
        embedding_model=os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"),
        retrieval_top_k=_int("RETRIEVAL_TOP_K", 3),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        max_input_chars=_int("MAX_INPUT_CHARS", 1000),
        history_turns=_int("HISTORY_TURNS", 3),
        threshold_tfidf=_float("THRESHOLD_TFIDF", 0.10),
        threshold_dense=_float("THRESHOLD_DENSE", 0.35),
        kb_dir=ROOT / "data" / "knowledge_base",
        storage_dir=storage,
        eval_file=ROOT / "data" / "evaluation" / "evaluation_questions.json",
        seed_file=ROOT / "data" / "seed" / "sample_data.json",
        prompt_file=ROOT / "prompts" / "receptionist_system_prompt.txt",
        db_path=storage / "qassist.db",
    )

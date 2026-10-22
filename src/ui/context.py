"""Builds the shared application objects once (cached by Streamlit in app.py)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from config.settings import Settings, get_settings
from src.llm.llm_service import LLMService
from src.rag.rag_pipeline import RagPipeline
from src.services.conversation_service import ConversationService
from src.services.receptionist_service import ReceptionistService
from src.utils.logging_config import setup_logging


@dataclass
class AppContext:
    settings: Settings
    rag: RagPipeline
    llm: LLMService
    service: ReceptionistService
    repo: Optional[object]
    convs: Optional[ConversationService]
    db_error: Optional[str]
    index_info: dict


def build_context() -> AppContext:
    s = get_settings()
    setup_logging(s.log_level)
    repo = convs = None
    db_error = None
    try:  # the chat must still work if the database cannot be opened
        from src.database.init_db import init_db
        from src.database.repository import Repository
        repo = Repository(init_db())
        convs = ConversationService(repo)
    except Exception as exc:  # noqa: BLE001
        db_error = f"Database unavailable ({type(exc).__name__}). Chat works but nothing is saved."
    rag = RagPipeline(s)
    try:
        info = rag.ingest()
    except Exception as exc:  # noqa: BLE001
        info = {"status": "error", "error": str(exc)}
    llm = LLMService(s)
    service = ReceptionistService(rag, llm, s, repo)
    return AppContext(s, rag, llm, service, repo, convs, db_error, info)

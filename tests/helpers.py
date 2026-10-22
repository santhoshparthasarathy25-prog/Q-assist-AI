"""Shared test helpers (synthetic data only, no network)."""
import dataclasses
import tempfile
from pathlib import Path

from config.settings import get_settings
from src.llm.llm_service import LLMService
from src.rag.rag_pipeline import RagPipeline
from src.services.receptionist_service import ReceptionistService


def demo_settings():
    return dataclasses.replace(get_settings(), gemini_api_key="", embedding_backend="tfidf")


def make_rag():
    s = demo_settings()
    rag = RagPipeline(s, storage_dir=Path(tempfile.mkdtemp()))
    rag.ingest()
    return rag


def make_service(llm=None, rag=None):
    s = demo_settings()
    return ReceptionistService(rag or make_rag(), llm or LLMService(s), s)

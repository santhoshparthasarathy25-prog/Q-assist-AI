import json
import tempfile
from pathlib import Path

from src.rag.chunker import chunk_document
from src.rag.document_loader import Document, clean_text, load_documents
from tests.helpers import demo_settings, make_rag
from src.rag.rag_pipeline import RagPipeline


def test_chunk_ids_and_metadata():
    doc = Document("x.txt", "HEADING\n\nFirst paragraph is here and it is long enough to stand alone as a chunk.", "h")
    chunks = chunk_document(doc)
    assert chunks and all(c.source == "x.txt" and c.chunk_id.startswith("x.txt::") for c in chunks)


def test_clean_text_collapses_whitespace():
    assert clean_text("a   b\r\n\r\n\r\n\r\nc") == "a b\n\nc"


def test_retrieval_returns_expected_source_with_metadata():
    rag = make_rag()
    res = rag.retrieve("How long does a repeat prescription take?")
    assert res.reliable and res.hits
    assert res.hits[0].source == "sample_prescription_policy.txt"
    assert "::" in res.hits[0].chunk_id and 0 <= res.hits[0].score <= 1.0001


def test_unrelated_question_not_reliable_and_no_sources():
    res = make_rag().retrieve("What is the capital of France?")
    assert not res.reliable and res.hits == []


def test_empty_query_safe():
    assert not make_rag().retrieve("   ").reliable


def test_reindex_skips_unchanged_documents():
    s = demo_settings()
    d = Path(tempfile.mkdtemp())
    rag = RagPipeline(s, storage_dir=d)
    assert rag.ingest()["status"] == "rebuilt"
    rag2 = RagPipeline(s, storage_dir=d)
    assert rag2.ingest()["status"] == "up_to_date"
    assert rag2.ingest(force=True)["status"] == "rebuilt"


def test_new_document_triggers_rebuild():
    s = demo_settings()
    kb = Path(tempfile.mkdtemp())
    (kb / "a.txt").write_text("Fictional clinic. Parking is free for patients on weekdays.", encoding="utf-8")
    rag = RagPipeline(s, kb_dir=kb, storage_dir=Path(tempfile.mkdtemp()))
    assert rag.ingest()["documents"] == 1
    (kb / "b.txt").write_text("Fictional clinic. The flu clinic runs every October on Saturdays.", encoding="utf-8")
    assert rag.ingest()["status"] == "rebuilt"
    assert rag.status()["documents"] == 2


def test_bad_file_does_not_break_loading():
    kb = Path(tempfile.mkdtemp())
    (kb / "good.txt").write_text("Some useful text about opening hours in a fictional clinic.", encoding="utf-8")
    (kb / "bad.pdf").write_bytes(b"not a real pdf")
    docs, warnings = load_documents(kb)
    assert [d.source for d in docs] == ["good.txt"] and warnings


def test_empty_knowledge_base_handled():
    kb = Path(tempfile.mkdtemp())
    rag = RagPipeline(demo_settings(), kb_dir=kb, storage_dir=Path(tempfile.mkdtemp()))
    assert rag.ingest()["status"] == "empty"
    assert not rag.retrieve("opening hours").reliable

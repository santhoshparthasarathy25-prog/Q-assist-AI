import pytest

pytest.importorskip("sqlalchemy")
pytest.importorskip("pandas")

import tempfile
from pathlib import Path

from src.database.init_db import init_db, reset_db
from src.database.repository import Repository, URGENT_PLACEHOLDER
from src.services.conversation_service import ConversationService
from tests.helpers import make_rag, make_service

SVC = make_service(rag=make_rag())


def _repo():
    path = Path(tempfile.mkdtemp()) / "t.db"
    return Repository(init_db(path)), path


def test_database_file_created_automatically():
    _, path = _repo()
    assert path.exists()


def test_interaction_is_persisted_with_all_related_rows():
    repo, _ = _repo()
    cid = repo.create_conversation("sess-1")
    svc = make_service(rag=SVC.rag); svc.repo = repo
    svc.handle("How do I book an appointment?", [], cid)
    assert repo.kpis()["enquiries"] == 1
    assert repo.intent_distribution().iloc[0]["intent"] == "appointment_info"
    assert repo.status_distribution().iloc[0]["status"] == "logged_simulated"
    assert repo.source_stats()["with_sources"] == 1
    assert len(repo.get_history(cid)) == 2


def test_urgent_content_not_stored_and_escalation_recorded():
    repo, _ = _repo()
    cid = repo.create_conversation("sess-2")
    svc = make_service(rag=SVC.rag); svc.repo = repo
    svc.handle("I have severe chest pain, my name is Jane Doe", [], cid)
    hist = repo.get_history(cid)
    assert hist[0][1] == URGENT_PLACEHOLDER and "Jane" not in hist[0][1]
    assert repo.kpis()["escalations"] == 1


def test_pii_redacted():
    repo, _ = _repo()
    cid = repo.create_conversation("sess-3")
    svc = make_service(rag=SVC.rag); svc.repo = repo
    svc.handle("Update my address, email me at jane@example.com or call 07700 900123", [], cid)
    stored = repo.get_history(cid)[0][1]
    assert "jane@example.com" not in stored and "900123" not in stored


def test_sessions_are_isolated_and_clear_starts_new_conversation():
    repo, _ = _repo()
    convs = ConversationService(repo)
    a, b = convs.start("A"), convs.start("B")
    svc = make_service(rag=SVC.rag); svc.repo = repo
    svc.handle("What are your opening hours?", [], a)
    assert repo.get_history(b) == []
    new = convs.clear(a, "A")
    assert new != a and convs.history(new) == []


def test_reset_clears_data():
    repo, path = _repo()
    cid = repo.create_conversation("s")
    svc = make_service(rag=SVC.rag); svc.repo = repo
    svc.handle("What are your opening hours?", [], cid)
    repo2 = Repository(reset_db(path))
    assert repo2.kpis()["enquiries"] == 0

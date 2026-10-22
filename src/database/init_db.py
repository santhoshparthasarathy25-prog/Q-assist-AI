"""Schema creation, demo seeding and reset."""
from __future__ import annotations

import json
from pathlib import Path

from config.settings import get_settings
from src.database.connection import make_engine
from src.database.models import Base


def init_db(db_path: Path | str | None = None):
    """Create all tables if missing and return the engine."""
    engine = make_engine(db_path)
    Base.metadata.create_all(engine)
    return engine


def reset_db(db_path: Path | str | None = None):
    """Drop and recreate every table (demo data only)."""
    engine = make_engine(db_path)
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    return engine


def seed_demo_data(service, conversations, seed_file: Path | None = None) -> int:
    """Run the synthetic questions in sample_data.json through the real pipeline (demo mode).
    Returns the number of questions processed. Seed conversations are flagged `is_seed`."""
    data = json.loads(Path(seed_file or get_settings().seed_file).read_text(encoding="utf-8"))
    count = 0
    for conv in data["conversations"]:
        conv_id = conversations.start(session_id=conv["session_id"], is_seed=True)
        for q in conv["questions"]:
            history = conversations.history(conv_id)
            service.handle(q, history, conv_id)
            count += 1
    return count

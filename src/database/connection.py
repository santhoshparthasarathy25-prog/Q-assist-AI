"""Engine/session management for the local SQLite database (created automatically)."""
from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker

from config.settings import get_settings
from src.utils.exceptions import DatabaseError


def make_engine(db_path: Path | str | None = None):
    path = Path(db_path or get_settings().db_path)
    if str(path) != ":memory:":
        path.parent.mkdir(parents=True, exist_ok=True)
    url = "sqlite:///" + ("" if str(path) == ":memory:" else path.as_posix())
    engine = create_engine(url, future=True)

    @event.listens_for(engine, "connect")
    def _fk_on(dbapi_conn, _):  # SQLite needs foreign keys switched on per connection
        dbapi_conn.execute("PRAGMA foreign_keys=ON")

    return engine


def make_session_factory(engine):
    return sessionmaker(bind=engine, expire_on_commit=False, future=True)


@contextmanager
def session_scope(factory):
    session = factory()
    try:
        yield session
        session.commit()
    except SQLAlchemyError as exc:
        session.rollback()
        raise DatabaseError(f"Database error: {type(exc).__name__}") from exc
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

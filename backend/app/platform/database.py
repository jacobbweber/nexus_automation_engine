"""Database access — the single SQLite connection helper for every context.

Uses **synchronous** SQLAlchemy over the stdlib ``sqlite3`` driver (no greenlet/async DB
dependency — see ADR-0004; the dev machine + CI runner block greenlet's native DLL via
Application Control). Async stays where it matters — connectors, log streaming, the asyncio
worker — and DB-bound route handlers are declared ``def`` so FastAPI runs them in its threadpool.

Every connection gets **WAL mode** + busy timeout + ``synchronous=NORMAL`` + foreign keys so
concurrent read-mostly UI traffic and read-write workers don't trip ``database is locked``
(harvested lesson from Ava-POC; see specs/00_foundation/architecture.md §7). No context opens
its own ``sqlite3.connect`` — everything routes through here.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.platform.config import get_settings


class Base(DeclarativeBase):
    """Declarative base shared by all context ORM models."""


_engine: Engine | None = None
_sessionmaker: sessionmaker[Session] | None = None


def _apply_sqlite_pragmas(dbapi_connection: Any, _record: Any) -> None:
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.execute("PRAGMA busy_timeout=5000")
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


def get_engine() -> Engine:
    global _engine, _sessionmaker
    if _engine is None:
        settings = get_settings()
        connect_args = (
            {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
        )
        _engine = create_engine(settings.database_url, future=True, connect_args=connect_args)
        if _engine.dialect.name == "sqlite":
            event.listen(_engine, "connect", _apply_sqlite_pragmas)
        _sessionmaker = sessionmaker(_engine, expire_on_commit=False)
    return _engine


def get_sessionmaker() -> sessionmaker[Session]:
    if _sessionmaker is None:
        get_engine()
    if _sessionmaker is None:  # pragma: no cover - get_engine always sets it
        raise RuntimeError("Session factory not initialized")
    return _sessionmaker


def init_db() -> None:
    """Create all registered tables. Models must be imported before calling this."""
    engine = get_engine()
    Base.metadata.create_all(engine)


def dispose_db() -> None:
    global _engine, _sessionmaker
    if _engine is not None:
        _engine.dispose()
        _engine = None
        _sessionmaker = None


def get_session() -> Iterator[Session]:
    """FastAPI dependency yielding a session (use from ``def`` handlers)."""
    with get_sessionmaker()() as session:
        yield session


def reset_for_tests() -> None:
    """Dispose the engine/sessionmaker so a test can rebind a fresh database URL."""
    dispose_db()

"""Tests that the shared DB helper applies WAL mode and lifecycle correctly."""

from __future__ import annotations

import pytest
from app.platform import database
from sqlalchemy import text


@pytest.fixture(autouse=True)
def _fresh_engine():
    database.reset_for_tests()
    from app.platform.config import get_settings

    get_settings.cache_clear()
    yield
    database.reset_for_tests()


def test_sqlite_uses_wal_mode():
    engine = database.get_engine()
    with engine.connect() as conn:
        mode = conn.execute(text("PRAGMA journal_mode")).scalar()
    assert str(mode).lower() == "wal"


def test_foreign_keys_enabled():
    engine = database.get_engine()
    with engine.connect() as conn:
        fk = conn.execute(text("PRAGMA foreign_keys")).scalar()
    assert int(fk) == 1


def test_init_db_is_idempotent():
    database.init_db()
    database.init_db()  # should not raise on second call

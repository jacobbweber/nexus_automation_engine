"""Shared test fixtures. Points the app at a throwaway temp SQLite file per test session."""

from __future__ import annotations

import os
import tempfile
from collections.abc import Iterator
from pathlib import Path

import pytest


@pytest.fixture(scope="session", autouse=True)
def _temp_database() -> Iterator[None]:
    tmpdir = tempfile.mkdtemp(prefix="nexus-test-")
    db_path = Path(tmpdir) / "test.db"
    os.environ["NEXUS_DATABASE_URL"] = f"sqlite:///{db_path.as_posix()}"
    os.environ["NEXUS_ENVIRONMENT"] = "test"

    # Ensure settings/engine pick up the test env even if imported earlier.
    from app.platform.config import get_settings

    get_settings.cache_clear()

    yield

    for f in Path(tmpdir).glob("test.db*"):
        try:
            f.unlink()
        except OSError:
            pass

"""Incident seeding: failed historical jobs should produce a lived-in triage board so the
Incidents surface (board + MTTR + top-failing trends) has data in simulation mode."""

from __future__ import annotations

import pytest
from app.contexts.execution_engine.application.seed import seed_history
from app.contexts.incident_management.application.seed import seed_incidents
from app.contexts.incident_management.domain.models import IncidentStatus
from app.contexts.incident_management.infrastructure.repository import IncidentRepository
from app.platform import database


def _ensure_schema():
    database.reset_for_tests()
    from app.platform.config import get_settings

    get_settings.cache_clear()
    import app.contexts.execution_engine.infrastructure.orm  # noqa: F401
    import app.contexts.incident_management.infrastructure.orm  # noqa: F401

    engine = database.get_engine()
    database.Base.metadata.drop_all(engine)
    database.Base.metadata.create_all(engine)


@pytest.fixture(autouse=True)
def _clean_db():
    _ensure_schema()
    yield
    database.reset_for_tests()


def test_seed_incidents_populates_board_from_failures():
    seed_history(count=60)
    created = seed_incidents()
    assert created > 0

    repo = IncidentRepository()
    incidents = repo.list_all()
    assert len(incidents) == created

    # Spread across multiple board columns (not all dumped in NEW).
    statuses = {i.status for i in incidents}
    assert len(statuses) >= 2

    # Every incident traces back to a job; at least one is resolved with a resolution time.
    assert all(i.source_type == "job" and i.source_id for i in incidents)
    resolved = [i for i in incidents if i.status == IncidentStatus.RESOLVED]
    assert resolved
    assert all(i.resolved_at is not None and i.resolved_at >= i.opened_at for i in resolved)


def test_seed_incidents_is_idempotent():
    seed_history(count=60)
    first = seed_incidents()
    assert first > 0
    second = seed_incidents()
    assert second == 0
    assert IncidentRepository().count() == first


def test_seed_incidents_noop_without_failures():
    # No job history at all → nothing to capture.
    assert seed_incidents() == 0

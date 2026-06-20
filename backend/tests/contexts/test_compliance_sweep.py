"""Compliance sweep: posture snapshots + drift-driven incidents (story 25.4)."""

from __future__ import annotations

import pytest
from app.contexts.compliance.application.service import ComplianceSweepService
from app.contexts.incident_management.application.service import IncidentService
from app.platform import database


@pytest.fixture(autouse=True)
def _db():
    database.reset_for_tests()
    from app.platform.config import get_settings

    get_settings.cache_clear()
    # all routers imported via create_app registration → all ORM is registered
    import app.platform.app_factory  # noqa: F401

    engine = database.get_engine()
    database.Base.metadata.drop_all(engine)
    database.Base.metadata.create_all(engine)
    from app.contexts.automation_catalog.application.seed import seed_templates
    from app.contexts.orchestration_canvas.application.seed import seed_workflow_library

    seed_templates()
    seed_workflow_library()
    yield
    database.reset_for_tests()


def test_sweep_produces_posture_snapshot():
    snap = ComplianceSweepService().run_sweep()
    assert snap.evaluated > 0
    assert snap.compliant + snap.drifted == snap.evaluated
    assert 0 <= snap.compliant_pct <= 100
    # latest() returns it
    assert ComplianceSweepService().latest().id == snap.id


def test_sweep_opens_incidents_for_drift_and_dedupes():
    svc = ComplianceSweepService()
    snap1 = svc.run_sweep()
    incidents_after_first = len(IncidentService().list_all())
    if snap1.drifted == 0:
        pytest.skip("no drift in this seed run")
    assert incidents_after_first >= 1
    # a second sweep must not duplicate incidents for the same drifted workflows
    svc.run_sweep()
    assert len(IncidentService().list_all()) == incidents_after_first


def test_history_accumulates():
    svc = ComplianceSweepService()
    svc.run_sweep()
    svc.run_sweep()
    assert len(svc.history()) == 2

"""Tests for scheduling: trigger computation, windows, dispatch, and API."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from app.contexts.orchestration_canvas.application.service import CanvasService
from app.contexts.orchestration_canvas.domain.models import Edge, Node, NodeType, WorkflowGraph
from app.contexts.scheduling.application.service import ScheduleService
from app.contexts.scheduling.domain.models import (
    MaintenanceWindow,
    ScheduleKind,
    compute_next_run,
    in_window,
)
from app.platform import database
from app.platform.app_factory import create_app
from fastapi.testclient import TestClient


def _ensure_schema():
    database.reset_for_tests()
    from app.platform.config import get_settings

    get_settings.cache_clear()
    import app.contexts.identity_access.infrastructure.orm  # noqa: F401
    import app.contexts.orchestration_canvas.infrastructure.orm  # noqa: F401
    import app.contexts.scheduling.infrastructure.orm  # noqa: F401

    engine = database.get_engine()
    database.Base.metadata.drop_all(engine)
    database.Base.metadata.create_all(engine)


@pytest.fixture(autouse=True)
def _clean_db():
    _ensure_schema()
    yield
    database.reset_for_tests()


def _make_workflow() -> str:
    graph = WorkflowGraph(
        nodes=[Node(id="start", type=NodeType.START), Node(id="end", type=NodeType.END)],
        edges=[Edge(source="start", target="end")],
    )
    return CanvasService().save_workflow(name="Scheduled WF", graph=graph).id


def test_compute_next_run_interval():
    base = datetime(2026, 1, 1, 0, 0, tzinfo=UTC)
    nxt = compute_next_run(
        ScheduleKind.INTERVAL, interval_seconds=600, daily_time="02:00", after=base
    )
    assert nxt == base + timedelta(seconds=600)


def test_compute_next_run_daily_rolls_forward():
    base = datetime(2026, 1, 1, 5, 0, tzinfo=UTC)
    nxt = compute_next_run(ScheduleKind.DAILY, interval_seconds=0, daily_time="02:00", after=base)
    assert nxt.hour == 2 and nxt.day == 2  # next day at 02:00


def test_in_window():
    t = datetime(2026, 1, 1, 3, 0, tzinfo=UTC)
    assert in_window(t, MaintenanceWindow(start_hour=2, end_hour=5))
    assert not in_window(t, MaintenanceWindow(start_hour=6, end_hour=8))
    assert in_window(t, None)


def test_create_schedule_sets_next_run():
    wf = _make_workflow()
    svc = ScheduleService()
    sched = svc.create(name="nightly", workflow_id=wf, interval_seconds=3600)
    assert sched.next_run_at is not None
    assert svc.get(sched.id).workflow_id == wf


async def test_run_due_dispatches_and_advances():
    wf = _make_workflow()
    svc = ScheduleService()
    sched = svc.create(name="due", workflow_id=wf, interval_seconds=3600)
    # Force it due.
    sched.next_run_at = datetime.now(UTC) - timedelta(seconds=5)
    svc.repo.save(sched)

    run_ids = await svc.run_due()
    assert len(run_ids) == 1
    advanced = svc.get(sched.id)
    assert advanced.last_run_at is not None
    assert advanced.next_run_at > datetime.now(UTC)


async def test_run_due_respects_window():
    wf = _make_workflow()
    svc = ScheduleService()
    # Window that excludes "now" (a 1-minute window far from current hour).
    hour = (datetime.now(UTC).hour + 5) % 24
    sched = svc.create(
        name="windowed",
        workflow_id=wf,
        interval_seconds=3600,
        window=MaintenanceWindow(start_hour=hour, end_hour=hour + 1),
    )
    sched.next_run_at = datetime.now(UTC) - timedelta(seconds=5)
    svc.repo.save(sched)
    run_ids = await svc.run_due()
    assert run_ids == []  # skipped, outside window
    assert svc.get(sched.id).last_run_at is None


# --- API ------------------------------------------------------------------------------------


@pytest.fixture
def client():
    _ensure_schema()
    with TestClient(create_app()) as c:
        yield c
    database.reset_for_tests()


def test_schedule_api_create_requires_engineer(client):
    op = client.post(
        "/api/v1/auth/login", json={"username": "operator", "password": "operator123"}
    ).json()["access_token"]
    resp = client.post(
        "/api/v1/schedules",
        headers={"Authorization": f"Bearer {op}"},
        json={"name": "x", "workflow_id": "wf"},
    )
    assert resp.status_code == 403


def test_schedule_api_create_and_list(client):
    eng = client.post(
        "/api/v1/auth/login", json={"username": "engineer", "password": "engineer123"}
    ).json()["access_token"]
    headers = {"Authorization": f"Bearer {eng}"}
    wf = _make_workflow()
    created = client.post(
        "/api/v1/schedules",
        headers=headers,
        json={"name": "nightly", "workflow_id": wf, "interval_seconds": 7200},
    )
    assert created.status_code == 200
    assert any(s["name"] == "nightly" for s in client.get("/api/v1/schedules").json())

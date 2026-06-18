"""API + WebSocket tests for the execution engine."""

from __future__ import annotations

import pytest
from app.contexts.connectors.domain.models import ConnectorKind, StreamType
from app.contexts.execution_engine.domain.models import JobLogLine, JobStatus, JobSubmission
from app.contexts.execution_engine.infrastructure.repository import JobRepository
from app.platform import database
from app.platform.app_factory import create_app
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def _clean_db():
    database.reset_for_tests()
    from app.platform.config import get_settings

    get_settings.cache_clear()
    import app.contexts.execution_engine.infrastructure.orm  # noqa: F401

    engine = database.get_engine()
    database.Base.metadata.drop_all(engine)
    database.Base.metadata.create_all(engine)
    yield
    database.reset_for_tests()


def test_execute_returns_pending_and_job_is_retrievable():
    with TestClient(create_app()) as client:
        resp = client.post(
            "/api/v1/jobs/execute",
            json={
                "name": "demo",
                "connector": "terraform",
                "action": "plan",
                "params": {"workspace": "prod"},
            },
        )
        assert resp.status_code == 200
        job_id = resp.json()["job_id"]
        assert resp.json()["status"] == "PENDING"
        got = client.get(f"/api/v1/jobs/{job_id}")
        assert got.status_code == 200
        assert got.json()["name"] == "demo"


def test_get_missing_job_404():
    with TestClient(create_app()) as client:
        assert client.get("/api/v1/jobs/nope").status_code == 404


def test_list_jobs_endpoint():
    repo = JobRepository()
    repo.create(
        JobSubmission(name="x", connector=ConnectorKind.SCRIPT, action="run"), created_at=_dt()
    )
    with TestClient(create_app()) as client:
        resp = client.get("/api/v1/jobs")
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


def test_ws_replays_completed_job_logs():
    repo = JobRepository()
    job = repo.create(
        JobSubmission(name="done", connector=ConnectorKind.TERRAFORM, action="plan"),
        created_at=_dt(),
    )
    repo.append_log(
        job.id,
        JobLogLine(sequence=1, timestamp=_dt(), stream=StreamType.STDOUT, message="Plan: 3 to add"),
    )
    repo.set_status(job.id, JobStatus.SUCCESS, started_at=_dt(), finished_at=_dt())

    with TestClient(create_app()) as client:
        with client.websocket_connect(f"/api/v1/jobs/{job.id}/stream") as ws:
            messages = []
            while True:
                msg = ws.receive_json()
                messages.append(msg)
                if msg.get("type") == "status":
                    break
    log_msgs = [m for m in messages if m["type"] == "log"]
    assert any("Plan:" in m["message"] for m in log_msgs)
    assert messages[-1]["status"] == "SUCCESS"


def test_telemetry_endpoint():
    repo = JobRepository()
    job = repo.create(
        JobSubmission(
            name="t",
            connector=ConnectorKind.ANSIBLE,
            action="run_job_template",
            asset_group="prod-fleet",
        ),
        created_at=_dt(),
    )
    repo.set_status(job.id, JobStatus.SUCCESS, started_at=_dt(), finished_at=_dt())
    with TestClient(create_app()) as client:
        resp = client.get(f"/api/v1/telemetry/{job.id}?seconds=60")
    assert resp.status_code == 200
    assert len(resp.json()["samples"]) > 0


def _dt():
    from datetime import UTC, datetime

    return datetime.now(UTC)

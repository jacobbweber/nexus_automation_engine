"""Tests for the crash-recovery sweep (architecture audit A1)."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from app.contexts.connectors.domain.models import ConnectorKind
from app.contexts.execution_engine.domain.models import JobStatus, JobSubmission
from app.contexts.execution_engine.infrastructure.repository import JobRepository
from app.contexts.orchestration_canvas.domain.models import RunStatus, WorkflowRun
from app.contexts.orchestration_canvas.infrastructure.repository import CanvasRepository
from app.platform import database


@pytest.fixture(autouse=True)
def _clean_db():
    database.reset_for_tests()
    from app.platform.config import get_settings

    get_settings.cache_clear()
    import app.contexts.execution_engine.infrastructure.orm  # noqa: F401
    import app.contexts.orchestration_canvas.infrastructure.orm  # noqa: F401

    engine = database.get_engine()
    database.Base.metadata.drop_all(engine)
    database.Base.metadata.create_all(engine)
    yield
    database.reset_for_tests()


def _dt():
    return datetime.now(UTC)


def test_fail_orphaned_jobs():
    repo = JobRepository()
    running = repo.create(
        JobSubmission(name="r", connector=ConnectorKind.TERRAFORM, action="apply"), created_at=_dt()
    )
    repo.set_status(running.id, JobStatus.RUNNING, started_at=_dt())
    done = repo.create(
        JobSubmission(name="d", connector=ConnectorKind.TERRAFORM, action="plan"), created_at=_dt()
    )
    repo.set_status(done.id, JobStatus.SUCCESS, finished_at=_dt())

    swept = repo.fail_orphaned_running()
    assert swept == 1
    assert repo.get(running.id).status == JobStatus.FAILED
    assert repo.get(running.id).error_message
    assert repo.get(done.id).status == JobStatus.SUCCESS  # untouched


def test_fail_orphaned_workflow_runs():
    repo = CanvasRepository()
    repo.save_run(
        WorkflowRun(
            run_id="run-1", workflow_id="wf", status=RunStatus.RUNNING, started_at=_dt(), inputs={}
        )
    )
    repo.save_run(
        WorkflowRun(
            run_id="run-2",
            workflow_id="wf",
            status=RunStatus.COMPLETED,
            started_at=_dt(),
            inputs={},
        )
    )
    swept = repo.fail_orphaned_runs()
    assert swept == 1
    assert repo.get_run("run-1").status == RunStatus.FAILED
    assert repo.get_run("run-2").status == RunStatus.COMPLETED

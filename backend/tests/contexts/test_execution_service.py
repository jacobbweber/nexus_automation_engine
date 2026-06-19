"""Tests for the execution engine service, repository, and seeding."""

from __future__ import annotations

import pytest
from app.contexts.connectors.domain.models import ConnectorKind
from app.contexts.execution_engine.application.seed import seed_history
from app.contexts.execution_engine.application.service import ExecutionService
from app.contexts.execution_engine.domain.models import JobStatus, JobSubmission
from app.contexts.execution_engine.infrastructure.repository import JobRepository
from app.platform import database


@pytest.fixture(autouse=True)
def _clean_db():
    database.reset_for_tests()
    from app.platform.config import get_settings

    get_settings.cache_clear()
    # Ensure ORM tables are registered and start from a clean schema each test.
    import app.contexts.execution_engine.infrastructure.orm  # noqa: F401

    engine = database.get_engine()
    database.Base.metadata.drop_all(engine)
    database.Base.metadata.create_all(engine)
    yield
    database.reset_for_tests()


def _terraform(name="tf", action="plan", **params) -> JobSubmission:
    return JobSubmission(
        name=name,
        connector=ConnectorKind.TERRAFORM,
        action=action,
        params={"workspace": "prod", **params},
    )


def test_submit_creates_pending_job():
    service = ExecutionService()
    job = service.submit(_terraform())
    assert job.status == JobStatus.PENDING
    assert service.get(job.id) is not None


async def test_run_success_persists_logs_and_status():
    service = ExecutionService()
    job = service.submit(_terraform(action="plan"))
    result = await service.run(job.id)
    assert result == JobStatus.SUCCESS
    refreshed = service.get(job.id)
    assert refreshed.status == JobStatus.SUCCESS
    assert refreshed.finished_at is not None
    logs = service.logs(job.id)
    assert logs and any("Plan:" in line.message for line in logs)


async def test_run_failure_marks_failed_with_error():
    service = ExecutionService()
    job = service.submit(_terraform(action="apply", force_fail=True))
    result = await service.run(job.id)
    assert result == JobStatus.FAILED
    refreshed = service.get(job.id)
    assert refreshed.status == JobStatus.FAILED
    assert refreshed.error_message
    assert service.logs(job.id)[-1].stream == "stderr"


def test_list_and_filter():
    service = ExecutionService()
    service.submit(_terraform(name="a"))
    service.submit(
        JobSubmission(name="b", connector=ConnectorKind.ANSIBLE, action="run_job_template")
    )
    all_jobs = service.list_all()
    assert len(all_jobs) == 2
    ansible_only = service.list_all(connector=ConnectorKind.ANSIBLE)
    assert len(ansible_only) == 1 and ansible_only[0].connector == ConnectorKind.ANSIBLE


def test_seed_history_populates_distribution():
    repo = JobRepository()
    created = seed_history(repo, count=55)
    assert created >= 55
    assert repo.count() >= 55
    statuses = {j.status for j in repo.list_all(limit=200)}
    assert JobStatus.SUCCESS in statuses


async def test_telemetry_for_completed_job():
    service = ExecutionService()
    job = service.submit(_terraform(action="plan"))
    await service.run(job.id)
    series = await service.telemetry(job.id)
    assert len(series.samples) > 0

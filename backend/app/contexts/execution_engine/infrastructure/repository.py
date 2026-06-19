"""Job repository — synchronous persistence for jobs and their logs."""

from __future__ import annotations

import json
from datetime import datetime

from sqlalchemy import func, select

from app.contexts.connectors.domain.models import ConnectorKind, StreamType
from app.contexts.execution_engine.domain.models import (
    Job,
    JobLogLine,
    JobStatus,
    JobSubmission,
)
from app.contexts.execution_engine.infrastructure.orm import JobLogRow, JobRow
from app.platform.database import get_sessionmaker
from app.shared_kernel.ids import new_id


def _to_job(row: JobRow) -> Job:
    return Job(
        id=row.id,
        name=row.name,
        connector=ConnectorKind(row.connector),
        action=row.action,
        params=json.loads(row.params_json or "{}"),
        status=JobStatus(row.status),
        check_mode=row.check_mode,
        diff_mode=row.diff_mode,
        initiated_by=row.initiated_by,
        asset_group=row.asset_group,
        change_number=row.change_number,
        workflow_run_id=row.workflow_run_id,
        workflow_node_id=row.workflow_node_id,
        error_message=row.error_message,
        created_at=row.created_at,
        started_at=row.started_at,
        finished_at=row.finished_at,
    )


class JobRepository:
    def create(
        self, submission: JobSubmission, *, created_at: datetime, job_id: str | None = None
    ) -> Job:
        row = JobRow(
            id=job_id or new_id("job"),
            name=submission.name,
            connector=str(submission.connector),
            action=submission.action,
            params_json=json.dumps(submission.params),
            status=JobStatus.PENDING.value,
            check_mode=submission.check_mode,
            diff_mode=submission.diff_mode,
            initiated_by=submission.initiated_by,
            asset_group=submission.asset_group,
            change_number=submission.change_number,
            workflow_run_id=submission.workflow_run_id,
            workflow_node_id=submission.workflow_node_id,
            created_at=created_at,
        )
        with get_sessionmaker()() as session:
            session.add(row)
            session.commit()
            session.refresh(row)
            return _to_job(row)

    def set_status(
        self,
        job_id: str,
        status: JobStatus,
        *,
        started_at: datetime | None = None,
        finished_at: datetime | None = None,
        error_message: str | None = None,
    ) -> None:
        with get_sessionmaker()() as session:
            row = session.get(JobRow, job_id)
            if row is None:
                return
            row.status = status.value
            if started_at is not None:
                row.started_at = started_at
            if finished_at is not None:
                row.finished_at = finished_at
            if error_message is not None:
                row.error_message = error_message
            session.commit()

    def append_log(self, job_id: str, line: JobLogLine) -> None:
        with get_sessionmaker()() as session:
            session.add(
                JobLogRow(
                    job_id=job_id,
                    sequence=line.sequence,
                    timestamp=line.timestamp,
                    stream=str(line.stream),
                    message=line.message,
                )
            )
            session.commit()

    def get(self, job_id: str) -> Job | None:
        with get_sessionmaker()() as session:
            row = session.get(JobRow, job_id)
            return _to_job(row) if row else None

    def list(
        self,
        *,
        status: JobStatus | None = None,
        connector: ConnectorKind | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Job]:
        stmt = select(JobRow).order_by(JobRow.created_at.desc())
        if status is not None:
            stmt = stmt.where(JobRow.status == status.value)
        if connector is not None:
            stmt = stmt.where(JobRow.connector == str(connector))
        stmt = stmt.limit(limit).offset(offset)
        with get_sessionmaker()() as session:
            return [_to_job(r) for r in session.execute(stmt).scalars().all()]

    def count(self) -> int:
        with get_sessionmaker()() as session:
            return int(session.execute(select(func.count(JobRow.id))).scalar() or 0)

    def get_logs(self, job_id: str) -> list[JobLogLine]:
        stmt = select(JobLogRow).where(JobLogRow.job_id == job_id).order_by(JobLogRow.sequence)
        with get_sessionmaker()() as session:
            return [
                JobLogLine(
                    sequence=r.sequence,
                    timestamp=r.timestamp,
                    stream=StreamType(r.stream),
                    message=r.message,
                )
                for r in session.execute(stmt).scalars().all()
            ]

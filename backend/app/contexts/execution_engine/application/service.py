"""ExecutionService — the job lifecycle worker.

Drives a job through PENDING -> RUNNING -> SUCCESS/FAILED by streaming a connector's log events,
persisting each line and broadcasting it live, then recording the terminal state. Knows nothing
about any vendor — it only speaks the connector ports.
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime

from app.contexts.connectors.domain.models import ExecutionRequest, StreamType
from app.contexts.connectors.domain.ports import ConnectorError
from app.contexts.connectors.infrastructure.registry import ConnectorRegistry, get_registry
from app.contexts.execution_engine.application.broker import LogBroker, get_broker
from app.contexts.execution_engine.domain.models import (
    Job,
    JobLogLine,
    JobStatus,
    JobSubmission,
)
from app.contexts.execution_engine.infrastructure.repository import JobRepository


def _now() -> datetime:
    return datetime.now(UTC)


class ExecutionService:
    def __init__(
        self,
        repository: JobRepository | None = None,
        registry: ConnectorRegistry | None = None,
        broker: LogBroker | None = None,
    ) -> None:
        self.repo = repository or JobRepository()
        self.registry = registry or get_registry()
        self.broker = broker or get_broker()

    def submit(self, submission: JobSubmission) -> Job:
        """Persist a new PENDING job and return it (does not start it)."""
        return self.repo.create(submission, created_at=_now())

    async def submit_and_run(self, submission: JobSubmission) -> Job:
        """Persist a job and schedule its execution as a background task."""
        job = self.submit(submission)
        asyncio.create_task(self.run(job.id))
        return job

    async def run(self, job_id: str) -> JobStatus:
        """Execute a job to a terminal state, streaming + persisting logs."""
        job = self.repo.get(job_id)
        if job is None:
            raise ConnectorError(f"Job {job_id!r} not found")

        self.repo.set_status(job_id, JobStatus.RUNNING, started_at=_now())
        await self.broker.publish(job_id, {"type": "status", "status": JobStatus.RUNNING.value})

        request = ExecutionRequest(
            kind=job.connector,
            action=job.action,
            params=job.params,
            check_mode=job.check_mode,
            diff_mode=job.diff_mode,
            run_id=job_id,
        )
        connector = self.registry.execution(job.connector)

        sequence = 0
        try:
            async for event in connector.execute(request):
                sequence += 1
                line = JobLogLine(
                    sequence=sequence,
                    timestamp=event.timestamp,
                    stream=event.stream,
                    message=event.message,
                )
                self.repo.append_log(job_id, line)
                await self.broker.publish(
                    job_id,
                    {
                        "type": "log",
                        "sequence": sequence,
                        "stream": str(event.stream),
                        "message": event.message,
                        "timestamp": event.timestamp.isoformat(),
                    },
                )
        except Exception as exc:  # noqa: BLE001 - any failure marks the job FAILED
            message = str(exc)
            sequence += 1
            self.repo.append_log(
                job_id,
                JobLogLine(
                    sequence=sequence,
                    timestamp=_now(),
                    stream=StreamType.STDERR,
                    message=message,
                ),
            )
            self.repo.set_status(
                job_id, JobStatus.FAILED, finished_at=_now(), error_message=message
            )
            # Auto-capture the failure as an incident (best-effort, never raises).
            from app.contexts.incident_management.application.service import capture_failure

            capture_failure(
                title=f"Job failed: {job.name}",
                source_type="job",
                source_id=job_id,
                summary=message,
            )
            await self.broker.publish(
                job_id, {"type": "status", "status": JobStatus.FAILED.value, "error": message}
            )
            await self.broker.close(job_id)
            return JobStatus.FAILED

        self.repo.set_status(job_id, JobStatus.SUCCESS, finished_at=_now())
        await self.broker.publish(job_id, {"type": "status", "status": JobStatus.SUCCESS.value})
        await self.broker.close(job_id)
        return JobStatus.SUCCESS

    # --- queries -----------------------------------------------------------------------------

    def get(self, job_id: str) -> Job | None:
        return self.repo.get(job_id)

    def list_all(self, **kwargs) -> list[Job]:
        return self.repo.list_all(**kwargs)

    def logs(self, job_id: str) -> list[JobLogLine]:
        return self.repo.get_logs(job_id)

    async def telemetry(self, job_id: str, seconds: int | None = None):
        """Correlated telemetry for a job's run window (via the Dynatrace connector port)."""
        from app.contexts.connectors.domain.models import ConnectorKind

        job = self.repo.get(job_id)
        if job is None:
            raise ConnectorError(f"Job {job_id!r} not found")
        if seconds is None:
            if job.started_at and job.finished_at:
                seconds = max(10, int((job.finished_at - job.started_at).total_seconds()))
            else:
                seconds = 60
        entity = job.asset_group or job.name
        return await self.registry.telemetry(ConnectorKind.DYNATRACE).series(entity, seconds)

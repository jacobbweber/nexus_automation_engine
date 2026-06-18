"""Job control plane: execute, query, stream logs, and telemetry."""

from __future__ import annotations

import contextlib

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from app.contexts.connectors.domain.models import ConnectorKind, TelemetrySeries
from app.contexts.execution_engine.application.broker import get_broker
from app.contexts.execution_engine.application.service import ExecutionService
from app.contexts.execution_engine.domain.models import (
    TERMINAL_STATUSES,
    Job,
    JobLogLine,
    JobStatus,
    JobSubmission,
)
from app.shared_kernel.errors import NotFoundError

router = APIRouter(tags=["jobs"])


class ExecuteResponse(BaseModel):
    job_id: str
    status: JobStatus


@router.post("/jobs/execute", response_model=ExecuteResponse)
async def execute_job(submission: JobSubmission) -> ExecuteResponse:
    service = ExecutionService()
    job = await service.submit_and_run(submission)
    return ExecuteResponse(job_id=job.id, status=job.status)


@router.get("/jobs", response_model=list[Job])
def list_jobs(
    status: JobStatus | None = None,
    connector: ConnectorKind | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[Job]:
    return ExecutionService().list(status=status, connector=connector, limit=limit, offset=offset)


@router.get("/jobs/{job_id}", response_model=Job)
def get_job(job_id: str) -> Job:
    job = ExecutionService().get(job_id)
    if job is None:
        raise NotFoundError(f"Job {job_id} not found")
    return job


@router.get("/jobs/{job_id}/logs", response_model=list[JobLogLine])
def get_job_logs(job_id: str) -> list[JobLogLine]:
    service = ExecutionService()
    if service.get(job_id) is None:
        raise NotFoundError(f"Job {job_id} not found")
    return service.logs(job_id)


@router.get("/telemetry/{job_id}", response_model=TelemetrySeries)
async def get_job_telemetry(job_id: str, seconds: int | None = None) -> TelemetrySeries:
    return await ExecutionService().telemetry(job_id, seconds)


@router.websocket("/jobs/{job_id}/stream")
async def stream_job(websocket: WebSocket, job_id: str) -> None:
    await websocket.accept()
    service = ExecutionService()
    job = service.get(job_id)
    if job is None:
        await websocket.send_json({"type": "error", "detail": "job not found"})
        await websocket.close()
        return

    broker = get_broker()
    queue = broker.subscribe(job_id)
    try:
        # Catch-up: replay everything already persisted.
        for line in service.logs(job_id):
            await websocket.send_json(
                {
                    "type": "log",
                    "sequence": line.sequence,
                    "stream": str(line.stream),
                    "message": line.message,
                    "timestamp": line.timestamp.isoformat(),
                }
            )

        # If already terminal, send final status and stop.
        job = service.get(job_id)
        if job and job.status in TERMINAL_STATUSES:
            await websocket.send_json({"type": "status", "status": job.status.value})
            return

        # Otherwise stream live until the end-of-stream sentinel.
        while True:
            event = await queue.get()
            if event is None:
                break
            await websocket.send_json(event)
    except WebSocketDisconnect:
        pass
    finally:
        broker.unsubscribe(job_id, queue)
        with contextlib.suppress(Exception):
            await websocket.close()

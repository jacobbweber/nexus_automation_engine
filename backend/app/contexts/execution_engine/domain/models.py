"""Execution engine domain models."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field

from app.contexts.connectors.domain.models import ConnectorKind, StreamType


class JobStatus(StrEnum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


TERMINAL_STATUSES = {JobStatus.SUCCESS, JobStatus.FAILED, JobStatus.CANCELLED}


class JobSubmission(BaseModel):
    """A request to run a single backend action as a job."""

    name: str
    connector: ConnectorKind
    action: str
    params: dict[str, object] = Field(default_factory=dict)
    check_mode: bool = False
    diff_mode: bool = False
    initiated_by: str = "operator"
    asset_group: str | None = None
    # Optional change-management linkage (set when change control applies).
    change_number: str | None = None
    # Optional canvas linkage (set when a job originates from a workflow run/step).
    workflow_run_id: str | None = None
    workflow_node_id: str | None = None


class JobLogLine(BaseModel):
    sequence: int
    timestamp: datetime
    stream: StreamType
    message: str


class Job(BaseModel):
    id: str
    name: str
    connector: ConnectorKind
    action: str
    params: dict[str, object] = Field(default_factory=dict)
    status: JobStatus
    check_mode: bool = False
    diff_mode: bool = False
    initiated_by: str
    asset_group: str | None = None
    change_number: str | None = None
    workflow_run_id: str | None = None
    workflow_node_id: str | None = None
    error_message: str | None = None
    created_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None

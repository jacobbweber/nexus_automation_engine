"""Incident management domain models."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel


class IncidentStatus(StrEnum):
    NEW = "new"
    TRIAGE = "triage"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"


BOARD_COLUMNS = [
    IncidentStatus.NEW,
    IncidentStatus.TRIAGE,
    IncidentStatus.INVESTIGATING,
    IncidentStatus.RESOLVED,
]


class Severity(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Incident(BaseModel):
    id: str
    title: str
    status: IncidentStatus = IncidentStatus.NEW
    severity: Severity = Severity.MEDIUM
    source_type: str  # "job" | "workflow"
    source_id: str
    summary: str = ""
    assigned_to: str | None = None
    remediation_workflow_id: str | None = None
    opened_at: datetime
    resolved_at: datetime | None = None

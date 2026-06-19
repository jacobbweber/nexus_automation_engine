"""Incident repository (sync SQLAlchemy)."""

from __future__ import annotations

from sqlalchemy import func, select

from app.contexts.incident_management.domain.models import (
    Incident,
    IncidentStatus,
    Severity,
)
from app.contexts.incident_management.infrastructure.orm import IncidentRow
from app.platform.database import get_sessionmaker


def _to_incident(r: IncidentRow) -> Incident:
    return Incident(
        id=r.id,
        title=r.title,
        status=IncidentStatus(r.status),
        severity=Severity(r.severity),
        source_type=r.source_type,
        source_id=r.source_id,
        summary=r.summary,
        assigned_to=r.assigned_to,
        remediation_workflow_id=r.remediation_workflow_id,
        opened_at=r.opened_at,
        resolved_at=r.resolved_at,
    )


class IncidentRepository:
    def save(self, incident: Incident) -> Incident:
        with get_sessionmaker()() as s:
            row = s.get(IncidentRow, incident.id) or IncidentRow(id=incident.id)
            row.title = incident.title
            row.status = str(incident.status)
            row.severity = str(incident.severity)
            row.source_type = incident.source_type
            row.source_id = incident.source_id
            row.summary = incident.summary
            row.assigned_to = incident.assigned_to
            row.remediation_workflow_id = incident.remediation_workflow_id
            row.opened_at = incident.opened_at
            row.resolved_at = incident.resolved_at
            s.add(row)
            s.commit()
            s.refresh(row)
            return _to_incident(row)

    def get(self, incident_id: str) -> Incident | None:
        with get_sessionmaker()() as s:
            row = s.get(IncidentRow, incident_id)
            return _to_incident(row) if row else None

    def list_all(self, *, status: IncidentStatus | None = None, limit: int = 200) -> list[Incident]:
        stmt = select(IncidentRow).order_by(IncidentRow.opened_at.desc()).limit(limit)
        if status is not None:
            stmt = stmt.where(IncidentRow.status == str(status))
        with get_sessionmaker()() as s:
            return [_to_incident(r) for r in s.execute(stmt).scalars().all()]

    def exists_open_for_source(self, source_type: str, source_id: str) -> bool:
        stmt = select(func.count(IncidentRow.id)).where(
            IncidentRow.source_type == source_type,
            IncidentRow.source_id == source_id,
            IncidentRow.status != str(IncidentStatus.RESOLVED),
        )
        with get_sessionmaker()() as s:
            return int(s.execute(stmt).scalar() or 0) > 0

    def count(self) -> int:
        with get_sessionmaker()() as s:
            return int(s.execute(select(func.count(IncidentRow.id))).scalar() or 0)

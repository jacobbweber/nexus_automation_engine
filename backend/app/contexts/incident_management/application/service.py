"""IncidentService — capture failures, run the triage board, convert to remediation."""

from __future__ import annotations

import logging
from datetime import UTC, datetime

from app.contexts.incident_management.domain.models import (
    BOARD_COLUMNS,
    Incident,
    IncidentStatus,
    Severity,
)
from app.contexts.incident_management.infrastructure.repository import IncidentRepository
from app.shared_kernel.errors import NotFoundError
from app.shared_kernel.ids import new_id

log = logging.getLogger("nexus.incidents")


def _now() -> datetime:
    return datetime.now(UTC)


class IncidentService:
    def __init__(self, repository: IncidentRepository | None = None) -> None:
        self.repo = repository or IncidentRepository()

    def capture(
        self,
        *,
        title: str,
        source_type: str,
        source_id: str,
        summary: str = "",
        severity: Severity = Severity.MEDIUM,
    ) -> Incident | None:
        """Open an incident for a failure. De-duplicates per open source to avoid card spam."""
        if self.repo.exists_open_for_source(source_type, source_id):
            return None
        return self.repo.save(
            Incident(
                id=new_id("inc"),
                title=title,
                status=IncidentStatus.NEW,
                severity=severity,
                source_type=source_type,
                source_id=source_id,
                summary=summary,
                opened_at=_now(),
            )
        )

    def get(self, incident_id: str) -> Incident:
        inc = self.repo.get(incident_id)
        if inc is None:
            raise NotFoundError(f"Incident {incident_id} not found")
        return inc

    def list_all(self) -> list[Incident]:
        return self.repo.list_all()

    def board(self) -> dict[str, list[Incident]]:
        items = self.repo.list_all()
        return {str(col): [i for i in items if i.status == col] for col in BOARD_COLUMNS}

    def move(
        self, incident_id: str, status: IncidentStatus, assigned_to: str | None = None
    ) -> Incident:
        inc = self.get(incident_id)
        inc.status = status
        if assigned_to is not None:
            inc.assigned_to = assigned_to
        inc.resolved_at = _now() if status == IncidentStatus.RESOLVED else None
        return self.repo.save(inc)

    def remediate(self, incident_id: str) -> str:
        """Create a draft remediation workflow seeded from the incident; link + return its id."""
        from app.contexts.orchestration_canvas.application.service import CanvasService
        from app.contexts.orchestration_canvas.domain.models import (
            Edge,
            Node,
            NodeType,
            WorkflowGraph,
        )

        inc = self.get(incident_id)
        graph = WorkflowGraph(
            nodes=[
                Node(id="start", type=NodeType.START, position={"x": 40, "y": 80}),
                Node(
                    id="approve",
                    type=NodeType.APPROVAL_GATE,
                    position={"x": 260, "y": 80},
                    data={
                        "name": "Approve remediation",
                        "message": f"Approve remediation for: {inc.title}",
                    },
                ),
                Node(
                    id="end", type=NodeType.END, position={"x": 480, "y": 80}, data={"outputs": {}}
                ),
            ],
            edges=[Edge(source="start", target="approve"), Edge(source="approve", target="end")],
        )
        wf = CanvasService().save_workflow(
            name=f"Remediate: {inc.title}",
            description=f"Auto-generated remediation for incident {inc.id} ({inc.source_type}).",
            graph=graph,
        )
        inc.remediation_workflow_id = wf.id
        self.repo.save(inc)
        return wf.id


def capture_failure(*, title: str, source_type: str, source_id: str, summary: str = "") -> None:
    """Best-effort capture hook for services to call on failure (never raises)."""
    try:
        IncidentService().capture(
            title=title, source_type=source_type, source_id=source_id, summary=summary
        )
    except Exception as exc:  # noqa: BLE001 - incident capture must never break execution
        log.warning("Incident capture failed: %s", exc)

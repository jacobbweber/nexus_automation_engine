"""Seed a lived-in incident triage board from failed historical jobs.

The dashboard shows failed runs; without this, the Incidents board would be empty even though
the system "captured" failures. This opens incidents for a sample of failed jobs and spreads
them across the board columns (with assignees + resolution times) so the board, mean-time-to-
resolution, and top-failing-automation trends all have realistic data. Idempotent: only seeds
when no incidents exist yet.
"""

from __future__ import annotations

import random
from datetime import timedelta

from app.contexts.execution_engine.domain.models import JobStatus
from app.contexts.execution_engine.infrastructure.repository import JobRepository
from app.contexts.incident_management.domain.models import (
    Incident,
    IncidentStatus,
    Severity,
)
from app.contexts.incident_management.infrastructure.repository import IncidentRepository
from app.shared_kernel.ids import new_id

# How a failure's environment maps to incident severity.
_ENV_SEVERITY = {
    "production": Severity.HIGH,
    "staging": Severity.MEDIUM,
    "development": Severity.LOW,
}
_ASSIGNEES = ["s.sre", "a.engineer", "p.platform", "o.operator"]
# Lifecycle spread for the seeded board: a couple still NEW, the rest progressing/resolved.
_STATUS_CYCLE = [
    IncidentStatus.NEW,
    IncidentStatus.RESOLVED,
    IncidentStatus.INVESTIGATING,
    IncidentStatus.RESOLVED,
    IncidentStatus.TRIAGE,
    IncidentStatus.RESOLVED,
    IncidentStatus.NEW,
    IncidentStatus.INVESTIGATING,
]


def seed_incidents(
    *,
    job_repo: JobRepository | None = None,
    incident_repo: IncidentRepository | None = None,
    max_incidents: int = 8,
    seed: int = 11,
) -> int:
    """Open incidents for a sample of failed jobs.

    Returns the number created (0 if incidents already exist or there are no failures).
    """
    incident_repo = incident_repo or IncidentRepository()
    if incident_repo.count() > 0:
        return 0

    job_repo = job_repo or JobRepository()
    failed = job_repo.list_all(status=JobStatus.FAILED, limit=max_incidents * 3)
    if not failed:
        return 0

    rng = random.Random(seed)
    created = 0
    for idx, job in enumerate(failed[:max_incidents]):
        env = str(job.params.get("environment", "")).lower() if job.params else ""
        severity = _ENV_SEVERITY.get(env, rng.choice(list(Severity)))
        status = _STATUS_CYCLE[idx % len(_STATUS_CYCLE)]
        opened_at = job.finished_at or job.started_at or job.created_at
        resolved_at = None
        assigned_to = None
        if status != IncidentStatus.NEW:
            assigned_to = rng.choice(_ASSIGNEES)
        if status == IncidentStatus.RESOLVED:
            resolved_at = opened_at + timedelta(minutes=rng.randint(15, 480))

        incident_repo.save(
            Incident(
                id=new_id("inc"),
                title=job.name,
                status=status,
                severity=severity,
                source_type="job",
                source_id=job.id,
                summary=job.error_message or "Run failed (simulated history).",
                assigned_to=assigned_to,
                opened_at=opened_at,
                resolved_at=resolved_at,
            )
        )
        created += 1
    return created

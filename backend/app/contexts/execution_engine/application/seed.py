"""Seed a rich, lived-in job history so the dashboard looks like a busy enterprise system.

Generates 50+ historical jobs across the last 30 days with a realistic status distribution
(~70% success, ~20% failed, ~10% cancelled), varied users/environments/connectors, and a few
log lines each. Idempotent-ish: only seeds when the jobs table is (near) empty.
"""

from __future__ import annotations

import random
from datetime import UTC, datetime, timedelta

from app.contexts.connectors.domain.models import ConnectorKind, StreamType
from app.contexts.execution_engine.domain.models import (
    JobLogLine,
    JobStatus,
    JobSubmission,
)
from app.contexts.execution_engine.infrastructure.repository import JobRepository

_USERS = ["a.engineer", "o.operator", "s.sre", "c.consumer", "p.platform"]
_ENVS = ["Development", "Staging", "Production"]
_SCENARIOS = [
    (ConnectorKind.TERRAFORM, "apply", "Provision AWS EKS Cluster & Node Groups"),
    (ConnectorKind.TERRAFORM, "plan", "Plan VPC + Subnet topology"),
    (ConnectorKind.ANSIBLE, "run_job_template", "RHEL 9 CIS/STIG Compliance Enforcement"),
    (ConnectorKind.ANSIBLE, "run_job_template", "Rolling OS Security Patching"),
    (ConnectorKind.SCRIPT, "run", "Emergency IIS App Pool Recycle & Cache Clear"),
    (ConnectorKind.SERVICENOW, "cmdb_lookup", "Sync CMDB Inventory Snapshot"),
]


def _weighted_status(rng: random.Random) -> JobStatus:
    roll = rng.random()
    if roll < 0.70:
        return JobStatus.SUCCESS
    if roll < 0.90:
        return JobStatus.FAILED
    return JobStatus.CANCELLED


def seed_history(repo: JobRepository | None = None, *, count: int = 60, seed: int = 7) -> int:
    """Populate historical jobs. Returns the number created (0 if already populated)."""
    repo = repo or JobRepository()
    if repo.count() >= count:
        return 0

    rng = random.Random(seed)
    now = datetime.now(UTC)
    created = 0
    for _ in range(count):
        connector, action, name = rng.choice(_SCENARIOS)
        env = rng.choice(_ENVS)
        status = _weighted_status(rng)
        created_at = now - timedelta(
            days=rng.randint(0, 29), hours=rng.randint(0, 23), minutes=rng.randint(0, 59)
        )
        duration = timedelta(seconds=rng.randint(20, 900))

        submission = JobSubmission(
            name=f"{name} [{env}]",
            connector=connector,
            action=action,
            params={"environment": env},
            check_mode=(action == "plan"),
            initiated_by=rng.choice(_USERS),
            asset_group=f"{env.lower()}-fleet",
        )
        job = repo.create(submission, created_at=created_at)
        started = created_at + timedelta(seconds=rng.randint(1, 10))
        finished = None if status == JobStatus.PENDING else started + duration

        # A couple of believable log lines.
        repo.append_log(
            job.id,
            JobLogLine(
                sequence=1,
                timestamp=started,
                stream=StreamType.SYSTEM,
                message=f"Run started on {env} fleet",
            ),
        )
        if status == JobStatus.FAILED:
            repo.append_log(
                job.id,
                JobLogLine(
                    sequence=2,
                    timestamp=finished or started,
                    stream=StreamType.STDERR,
                    message="ERROR: task failed (simulated history)",
                ),
            )
        else:
            repo.append_log(
                job.id,
                JobLogLine(
                    sequence=2,
                    timestamp=finished or started,
                    stream=StreamType.STDOUT,
                    message="Completed (simulated history)",
                ),
            )

        repo.set_status(
            job.id,
            status,
            started_at=started,
            finished_at=finished,
            error_message="task failed (simulated history)" if status == JobStatus.FAILED else None,
        )
        created += 1
    return created

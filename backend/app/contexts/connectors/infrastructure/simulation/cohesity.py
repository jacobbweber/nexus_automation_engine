"""Simulated Cohesity data-protection execution connector."""

from __future__ import annotations

from collections.abc import AsyncIterator

from app.contexts.connectors.domain.models import (
    Capabilities,
    ConnectorAction,
    ConnectorCategory,
    ConnectorKind,
    ExecutionRequest,
    LogEvent,
    ParamField,
    StreamType,
)
from app.contexts.connectors.domain.ports import ConnectorError
from app.contexts.connectors.infrastructure.simulation._support import (
    BLUE,
    GREEN,
    YELLOW,
    color,
    jitter,
)


def _line(msg: str, stream: StreamType = StreamType.STDOUT) -> LogEvent:
    return LogEvent(message=msg, stream=stream)


_FLOWS: dict[str, tuple[str, list[str]]] = {
    "run_backup": (
        "Run Protection Job",
        [
            "Triggering protection job 'PJ-VMware-Gold'...",
            "Snapshotting 42 VMs (CBT incremental)...",
            "Deduplicating + compressing (3.1x)...",
            "Backup run SUCCEEDED — 1.2 TB logical",
        ],
    ),
    "recover_vm": (
        "Recover VM",
        [
            "Locating recovery point 2026-06-18T01:00Z...",
            "Instant-recovering 'app-prod-12' to cluster wld-prod-01...",
            "Powering on, migrating to primary storage...",
            "Recovery complete (RTO 3m12s)",
        ],
    ),
    "clone_vm": (
        "Clone VM for Test/Dev",
        [
            "Creating zero-cost clone of 'db-prod-03'...",
            "Mounting to test network...",
            "Clone 'db-prod-03-clone' ready",
        ],
    ),
    "protect_object": (
        "Add Object to Protection",
        [
            "Registering source vCenter...",
            "Adding 'wld-prod-01' to policy 'Gold-1h'",
            "Object protected",
        ],
    ),
}


class CohesitySimConnector:
    kind = ConnectorKind.COHESITY

    def capabilities(self) -> Capabilities:
        actions = [
            ConnectorAction(
                name=n,
                label=lbl,
                params=[
                    ParamField(name="object", type="string", label="Object"),
                    ParamField(name="policy", type="string", label="Policy"),
                ],
            )
            for n, (lbl, _) in _FLOWS.items()
        ]
        return Capabilities(
            kind=ConnectorKind.COHESITY,
            category=ConnectorCategory.EXECUTION,
            display_name="Cohesity (Data Protection)",
            description="Backup, instant recovery, clone, and protection policy management.",
            supports_check_mode=True,
            actions=actions,
        )

    async def execute(self, request: ExecutionRequest) -> AsyncIterator[LogEvent]:
        flow = _FLOWS.get(request.action)
        if flow is None:
            raise ConnectorError(f"Cohesity: unknown action {request.action!r}")
        label, lines = flow
        yield _line(color(f"Cohesity Helios :: {label}", BLUE, bold=True))
        await jitter()
        for ln in lines:
            yield _line(color("  ▸ ", YELLOW) + ln)
            await jitter()
            if request.params.get("force_fail"):
                yield _line(
                    color("ERROR: protection job failed - source unreachable", "\033[31m"),
                    StreamType.STDERR,
                )
                raise ConnectorError("Cohesity job failed (simulated)")
        yield _line(color(f"✓ {label} succeeded", GREEN, bold=True))

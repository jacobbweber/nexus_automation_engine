"""Simulated Pure Storage FlashArray execution connector (driven like Ansible playbooks)."""

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
    GREEN,
    GREY,
    YELLOW,
    color,
    jitter,
)


def _line(msg: str, stream: StreamType = StreamType.STDOUT) -> LogEvent:
    return LogEvent(message=msg, stream=stream)


_FLOWS: dict[str, tuple[str, list[str]]] = {
    "create_volume": (
        "Create FlashArray Volume",
        [
            "purefa_volume: creating 'vol-prod-db-01' size=2T",
            "applying QoS policy 'gold'",
            "volume serial 7A1F... created",
        ],
    ),
    "snapshot_volume": (
        "Snapshot Volume",
        [
            "purefa_snap: snapshotting 'vol-prod-db-01'",
            "snapshot 'vol-prod-db-01.2026_06_18' created",
        ],
    ),
    "eradicate_volume": (
        "Eradicate Volume (CONTROLLED)",
        [
            "purefa_volume: destroying 'vol-stale-07'",
            "purefa_volume: eradicating (unrecoverable)",
            "volume eradicated",
        ],
    ),
    "connect_host": (
        "Connect Volume to Host",
        [
            "purefa_host: creating host 'esx-prod-03' with 2 IQNs",
            "connecting 'vol-prod-db-01' LUN 12",
            "host connection established",
        ],
    ),
    "create_protection_group": (
        "Create Protection Group + Replication",
        [
            "purefa_pg: creating pgroup 'pg-prod'",
            "adding 6 volumes",
            "scheduling async replication to DR array",
        ],
    ),
}


class PureStorageSimConnector:
    kind = ConnectorKind.PURESTORAGE

    def capabilities(self) -> Capabilities:
        actions = [
            ConnectorAction(
                name=n,
                label=lbl,
                params=[
                    ParamField(name="array", type="string", label="FlashArray"),
                    ParamField(name="name", type="string", label="Object name"),
                ],
            )
            for n, (lbl, _) in _FLOWS.items()
        ]
        return Capabilities(
            kind=ConnectorKind.PURESTORAGE,
            category=ConnectorCategory.EXECUTION,
            display_name="Pure Storage (FlashArray)",
            description="FlashArray volume/host/snapshot/replication lifecycle via Ansible.",
            supports_check_mode=True,
            actions=actions,
        )

    async def execute(self, request: ExecutionRequest) -> AsyncIterator[LogEvent]:
        flow = _FLOWS.get(request.action)
        if flow is None:
            raise ConnectorError(f"Pure Storage: unknown action {request.action!r}")
        label, lines = flow
        array = request.params.get("array", "flasharray-prod-01")
        yield _line(color(f"PLAY [Pure {label}] on {array}", GREEN))
        await jitter()
        for ln in lines:
            yield _line(color("TASK ", GREY) + ln)
            await jitter()
            if request.params.get("force_fail"):
                yield _line(
                    color("fatal: purefa API 400 - object in use", "\033[31m"), StreamType.STDERR
                )
                raise ConnectorError("Pure Storage task failed (simulated)")
        yield _line(color(f"ok: {label} — changed=1", YELLOW))

"""Simulated Dynatrace connector — correlated telemetry for a run window."""

from __future__ import annotations

import math
import random
from datetime import timedelta

from app.contexts.connectors.domain.models import (
    Capabilities,
    ConnectorAction,
    ConnectorCategory,
    ConnectorKind,
    ParamField,
    TelemetryEvent,
    TelemetrySample,
    TelemetrySeries,
    _utcnow,
)


class DynatraceSimConnector:
    kind = ConnectorKind.DYNATRACE

    def capabilities(self) -> Capabilities:
        return Capabilities(
            kind=ConnectorKind.DYNATRACE,
            category=ConnectorCategory.SYSTEM_OF_RECORD,
            display_name="Dynatrace",
            description="Correlated CPU/memory metrics and platform events for a run.",
            streams_logs=False,
            actions=[
                ConnectorAction(
                    name="series",
                    label="Telemetry series",
                    params=[
                        ParamField(name="entity", type="string", label="Entity", required=True),
                        ParamField(name="seconds", type="number", label="Window (s)", default=60),
                    ],
                )
            ],
        )

    async def series(self, entity: str, seconds: int) -> TelemetrySeries:
        seconds = max(10, min(seconds, 3600))
        now = _utcnow()
        points = min(60, seconds)
        step = seconds / points
        samples: list[TelemetrySample] = []
        for i in range(points):
            t = now - timedelta(seconds=seconds) + timedelta(seconds=i * step)
            base = 40 + 25 * math.sin(i / 6)
            samples.append(
                TelemetrySample(
                    timestamp=t,
                    cpu_percent=round(max(2, min(98, base + random.uniform(-8, 8))), 1),
                    memory_percent=round(max(10, min(95, 55 + random.uniform(-6, 6))), 1),
                )
            )
        events = [
            TelemetryEvent(
                timestamp=now - timedelta(seconds=seconds // 2),
                severity="info",
                title=f"Deployment detected on {entity}",
            )
        ]
        return TelemetrySeries(samples=samples, events=events)

"""Connector application services — thin use cases the api layer calls."""

from __future__ import annotations

from app.contexts.connectors.domain.models import (
    Capabilities,
    ConnectorKind,
    DiscoveryQuery,
    DriftReport,
    ExecutionRequest,
    Resource,
)
from app.contexts.connectors.infrastructure.registry import ConnectorRegistry, get_registry
from app.contexts.connectors.infrastructure.simulation.compliance import (
    aggregate as _aggregate_drift,
)
from app.contexts.connectors.infrastructure.simulation.compliance import (
    evaluate_compliance as _evaluate_compliance,
)


def list_capabilities(registry: ConnectorRegistry | None = None) -> list[Capabilities]:
    """All registered connectors' capabilities — powers the canvas node connector dropdown."""
    return (registry or get_registry()).all_capabilities()


def get_capabilities(
    kind: ConnectorKind, registry: ConnectorRegistry | None = None
) -> Capabilities:
    return (registry or get_registry()).capabilities(kind)


async def discover(
    kind: ConnectorKind, query: DiscoveryQuery, registry: ConnectorRegistry | None = None
) -> list[Resource]:
    return await (registry or get_registry()).discovery(kind).discover(query)


def evaluate_compliance(request: ExecutionRequest) -> DriftReport:
    """Assess desired-vs-observed for a request WITHOUT mutating (compliance mode)."""
    return _evaluate_compliance(request)


def aggregate_drift(reports: list[DriftReport], target: str = "workflow") -> DriftReport:
    """Roll several drift reports (e.g. a workflow's steps) into one aggregate report."""
    return _aggregate_drift(reports, target)

"""Connector application services — thin use cases the api layer calls."""

from __future__ import annotations

from app.contexts.connectors.domain.models import (
    Capabilities,
    ConnectorKind,
    DiscoveryQuery,
    Resource,
)
from app.contexts.connectors.infrastructure.registry import ConnectorRegistry, get_registry


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

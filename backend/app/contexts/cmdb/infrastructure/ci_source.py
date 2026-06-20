"""CI source adapter — resolves CI records via the ServiceNow CMDB connector port (the ACL).

Keeps the connector dependency at the cmdb context's infrastructure edge; the health checker stays
pure (dict in, report out). Mirrors how lifecycle_validation resolves CIs through the registry.
"""

from __future__ import annotations

from app.contexts.connectors.domain.models import ConnectorKind, DiscoveryQuery
from app.contexts.connectors.infrastructure.registry import get_registry


async def fetch_ci(name: str) -> dict[str, object] | None:
    res = (
        await get_registry()
        .discovery(ConnectorKind.SERVICENOW)
        .discover(DiscoveryQuery(source="cmdb_ci", filters={"name": name}))
    )
    return dict(res[0].attributes) if res else None


async def all_ci_names() -> set[str]:
    res = (
        await get_registry()
        .discovery(ConnectorKind.SERVICENOW)
        .discover(DiscoveryQuery(source="cmdb_ci", filters={}, limit=500))
    )
    return {r.name for r in res}

"""CI source — fetch all CMDB CI records via the ServiceNow connector port (the ACL).

Determinism reconciliation needs the full CI records (type + tags + fields) to evaluate selectors,
so it reads them through the published connector discovery port (same seam lifecycle/cmdb use).
"""

from __future__ import annotations

from app.contexts.connectors.domain.models import ConnectorKind, DiscoveryQuery
from app.contexts.connectors.infrastructure.registry import get_registry


async def all_cis() -> list[dict[str, object]]:
    res = (
        await get_registry()
        .discovery(ConnectorKind.SERVICENOW)
        .discover(DiscoveryQuery(source="cmdb_ci", filters={}, limit=500))
    )
    return [dict(r.attributes) for r in res]

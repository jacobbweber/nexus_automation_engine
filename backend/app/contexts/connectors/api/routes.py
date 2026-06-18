"""Connector REST routes: list capabilities and run discovery (e.g. CMDB lookup)."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.contexts.connectors.application import services
from app.contexts.connectors.domain.models import (
    Capabilities,
    ConnectorKind,
    DiscoveryQuery,
    Resource,
)

router = APIRouter(prefix="/connectors", tags=["connectors"])


@router.get("", response_model=list[Capabilities])
def list_connectors() -> list[Capabilities]:
    return services.list_capabilities()


@router.get("/{kind}", response_model=Capabilities)
def get_connector(kind: ConnectorKind) -> Capabilities:
    return services.get_capabilities(kind)


class DiscoveryRequest(BaseModel):
    source: str = "cmdb_ci_server"
    filters: dict[str, object] = Field(default_factory=dict)
    fields: list[str] = Field(default_factory=list)
    limit: int = 50


@router.post("/{kind}/discover", response_model=list[Resource])
async def discover(kind: ConnectorKind, body: DiscoveryRequest) -> list[Resource]:
    query = DiscoveryQuery(
        source=body.source, filters=body.filters, fields=body.fields, limit=body.limit
    )
    return await services.discover(kind, query)

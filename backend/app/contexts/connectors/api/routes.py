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


class CmdbField(BaseModel):
    name: str
    label: str
    type: str


class CmdbFieldsResponse(BaseModel):
    tables: list[str]
    fields: list[CmdbField]


@router.get("/servicenow/fields", response_model=CmdbFieldsResponse)
def cmdb_fields(table: str | None = None) -> CmdbFieldsResponse:
    """Field catalog for the canvas CMDB field picker (pick a table → pick its fields)."""
    from app.contexts.connectors.infrastructure.simulation import servicenow as sn

    return CmdbFieldsResponse(
        tables=sn.cmdb_tables(),
        fields=[CmdbField(**f) for f in sn.cmdb_fields(table)],
    )


class ChangeRecord(BaseModel):
    number: str
    short_description: str
    state: str
    start: str
    end: str
    assignment_group: str
    risk: str
    affected_cis: list[str]


@router.get("/servicenow/changes", response_model=list[ChangeRecord])
def servicenow_changes() -> list[ChangeRecord]:
    """The change calendar's source of truth: CHG records from the (simulated) ServiceNow CMDB."""
    from app.contexts.connectors.infrastructure.simulation import servicenow as sn

    return [ChangeRecord(**c) for c in sn.list_changes()]


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

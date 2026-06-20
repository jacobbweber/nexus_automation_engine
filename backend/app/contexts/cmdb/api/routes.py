"""CMDB routes: CI type schema + lineage registry (admin-editable) and CI health checks."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.contexts.cmdb.application.service import (
    CmdbHealthService,
    CmdbLineageService,
    CmdbSchemaService,
)
from app.contexts.cmdb.domain.health import CIHealthReport
from app.contexts.cmdb.domain.lineage import LineageSpec
from app.contexts.cmdb.domain.models import CITypeSchema
from app.contexts.cmdb.infrastructure.ci_source import all_ci_names, fetch_ci
from app.contexts.identity_access.api.deps import require_role
from app.contexts.identity_access.domain.models import GlobalRole, UserContext
from app.shared_kernel.errors import NotFoundError

router = APIRouter(prefix="/cmdb", tags=["cmdb"])


# ---- schemas -----------------------------------------------------------------------------------


@router.get("/schemas", response_model=list[CITypeSchema])
def list_schemas() -> list[CITypeSchema]:
    return CmdbSchemaService().list_schemas()


@router.get("/schemas/{ci_type}", response_model=CITypeSchema)
def get_schema(ci_type: str) -> CITypeSchema:
    return CmdbSchemaService().get_schema(ci_type)


@router.put("/schemas/{ci_type}", response_model=CITypeSchema)
def upsert_schema(
    ci_type: str,
    schema: CITypeSchema,
    admin: UserContext = Depends(require_role(GlobalRole.ADMIN)),
) -> CITypeSchema:
    schema.type = ci_type
    schema.updated_by = admin.username
    return CmdbSchemaService().upsert_schema(schema)


# ---- lineage -----------------------------------------------------------------------------------


@router.get("/lineage", response_model=list[LineageSpec])
def list_lineage() -> list[LineageSpec]:
    return CmdbLineageService().list_lineage()


@router.get("/lineage/{ci_type}", response_model=LineageSpec)
def get_lineage(ci_type: str) -> LineageSpec:
    return CmdbLineageService().get_lineage(ci_type)


@router.put("/lineage/{ci_type}", response_model=LineageSpec)
def upsert_lineage(
    ci_type: str,
    spec: LineageSpec,
    admin: UserContext = Depends(require_role(GlobalRole.ADMIN)),
) -> LineageSpec:
    spec.type = ci_type
    return CmdbLineageService().upsert_lineage(spec)


# ---- health ------------------------------------------------------------------------------------


@router.post("/validate-ci", response_model=CIHealthReport)
def validate_ci(ci: dict) -> CIHealthReport:
    """Check an ad-hoc CI record against its type's schema + lineage."""
    return CmdbHealthService().check(ci)


@router.get("/ci/{name}/health", response_model=CIHealthReport)
async def ci_health(name: str) -> CIHealthReport:
    """Resolve a CI via the CMDB connector and return its deterministic health report."""
    ci = await fetch_ci(name)
    if ci is None:
        raise NotFoundError(f"CI '{name}' not found in the CMDB")
    known = await all_ci_names()
    return CmdbHealthService().check(ci, known_ci_ids=known)

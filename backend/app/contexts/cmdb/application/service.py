"""CmdbSchemaService — the CI type schema registry use cases (list / get / upsert)."""

from __future__ import annotations

from app.contexts.cmdb.domain.health import CIHealthReport, check_ci
from app.contexts.cmdb.domain.lineage import LineageSpec, validate_lineage
from app.contexts.cmdb.domain.models import CITypeSchema, validate_schema
from app.contexts.cmdb.infrastructure.repository import (
    CITypeSchemaRepository,
    LineageSpecRepository,
)
from app.shared_kernel.errors import NotFoundError, ValidationError


class CmdbSchemaService:
    def __init__(self, repository: CITypeSchemaRepository | None = None) -> None:
        self.repo = repository or CITypeSchemaRepository()

    def list_schemas(self) -> list[CITypeSchema]:
        return self.repo.list_all()

    def get_schema(self, ci_type: str) -> CITypeSchema:
        schema = self.repo.get(ci_type)
        if schema is None:
            raise NotFoundError(f"No CMDB schema for CI type '{ci_type}'")
        return schema

    def upsert_schema(self, schema: CITypeSchema) -> CITypeSchema:
        """Validate then store. Raises ValidationError listing every problem."""
        errors = validate_schema(schema)
        if errors:
            raise ValidationError("; ".join(errors))
        return self.repo.upsert(schema)


class CmdbLineageService:
    def __init__(
        self,
        repository: LineageSpecRepository | None = None,
        schema_repo: CITypeSchemaRepository | None = None,
    ) -> None:
        self.repo = repository or LineageSpecRepository()
        self.schema_repo = schema_repo or CITypeSchemaRepository()

    def list_lineage(self) -> list[LineageSpec]:
        return self.repo.list_all()

    def get_lineage(self, ci_type: str) -> LineageSpec:
        spec = self.repo.get(ci_type)
        if spec is None:
            raise NotFoundError(f"No lineage spec for CI type '{ci_type}'")
        return spec

    def upsert_lineage(self, spec: LineageSpec) -> LineageSpec:
        """Validate (relationship targets must be known CI types) then store."""
        known = {s.type for s in self.schema_repo.list_all()}
        errors = validate_lineage(spec, known)
        if errors:
            raise ValidationError("; ".join(errors))
        return self.repo.upsert(spec)


class CmdbHealthService:
    """Resolve a CI's schema + lineage and run the deterministic health checker."""

    def __init__(
        self,
        schema_repo: CITypeSchemaRepository | None = None,
        lineage_repo: LineageSpecRepository | None = None,
    ) -> None:
        self.schema_repo = schema_repo or CITypeSchemaRepository()
        self.lineage_repo = lineage_repo or LineageSpecRepository()

    def check(self, ci: dict[str, object], known_ci_ids: set[str] | None = None) -> CIHealthReport:
        ci_type = str(ci.get("ci_type") or "")
        schema = self.schema_repo.get(ci_type)
        if schema is None:
            raise NotFoundError(f"No CMDB schema for CI type '{ci_type}' — cannot assess health")
        lineage = self.lineage_repo.get(ci_type)
        return check_ci(ci, schema, lineage, known_ci_ids)

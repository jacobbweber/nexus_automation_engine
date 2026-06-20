"""CmdbSchemaService — the CI type schema registry use cases (list / get / upsert)."""

from __future__ import annotations

from app.contexts.cmdb.domain.models import CITypeSchema, validate_schema
from app.contexts.cmdb.infrastructure.repository import CITypeSchemaRepository
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

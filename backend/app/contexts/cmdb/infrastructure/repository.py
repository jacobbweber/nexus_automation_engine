"""CI type schema repository (one JSON-document row per CI type)."""

from __future__ import annotations

from datetime import UTC, datetime

from app.contexts.cmdb.domain.lineage import LineageSpec
from app.contexts.cmdb.domain.models import CITypeSchema
from app.contexts.cmdb.infrastructure.orm import CITypeSchemaRow, LineageSpecRow
from app.platform.database import get_sessionmaker


def _to_schema(row: CITypeSchemaRow) -> CITypeSchema:
    return CITypeSchema.model_validate_json(row.document_json)


def _to_lineage(row: LineageSpecRow) -> LineageSpec:
    return LineageSpec.model_validate_json(row.document_json)


class CITypeSchemaRepository:
    def list_all(self) -> list[CITypeSchema]:
        with get_sessionmaker()() as s:
            rows = s.query(CITypeSchemaRow).order_by(CITypeSchemaRow.type).all()
            return [_to_schema(r) for r in rows]

    def get(self, ci_type: str) -> CITypeSchema | None:
        with get_sessionmaker()() as s:
            row = s.get(CITypeSchemaRow, ci_type)
            return _to_schema(row) if row else None

    def upsert(self, schema: CITypeSchema) -> CITypeSchema:
        with get_sessionmaker()() as s:
            row = s.get(CITypeSchemaRow, schema.type) or CITypeSchemaRow(type=schema.type)
            row.label = schema.label
            row.version = schema.version
            row.document_json = schema.model_dump_json()
            row.updated_by = schema.updated_by
            row.updated_at = datetime.now(UTC)
            s.add(row)
            s.commit()
        return schema

    def count(self) -> int:
        with get_sessionmaker()() as s:
            return s.query(CITypeSchemaRow).count()


class LineageSpecRepository:
    def list_all(self) -> list[LineageSpec]:
        with get_sessionmaker()() as s:
            rows = s.query(LineageSpecRow).order_by(LineageSpecRow.type).all()
            return [_to_lineage(r) for r in rows]

    def get(self, ci_type: str) -> LineageSpec | None:
        with get_sessionmaker()() as s:
            row = s.get(LineageSpecRow, ci_type)
            return _to_lineage(row) if row else None

    def upsert(self, spec: LineageSpec) -> LineageSpec:
        from datetime import UTC, datetime

        with get_sessionmaker()() as s:
            row = s.get(LineageSpecRow, spec.type) or LineageSpecRow(type=spec.type)
            row.document_json = spec.model_dump_json()
            row.updated_at = datetime.now(UTC)
            s.add(row)
            s.commit()
        return spec

    def count(self) -> int:
        with get_sessionmaker()() as s:
            return s.query(LineageSpecRow).count()

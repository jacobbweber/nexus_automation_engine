"""ORM row for CI type schemas (one row per CI type; schema stored as a JSON document)."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.platform.database import Base


class CITypeSchemaRow(Base):
    __tablename__ = "cmdb_ci_type_schema"

    type: Mapped[str] = mapped_column(String, primary_key=True)
    label: Mapped[str] = mapped_column(String, nullable=False)
    version: Mapped[int] = mapped_column(default=1)
    document_json: Mapped[str] = mapped_column(Text, nullable=False)  # full CITypeSchema as JSON
    updated_by: Mapped[str] = mapped_column(String, default="system")
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class LineageSpecRow(Base):
    __tablename__ = "cmdb_lineage_spec"

    type: Mapped[str] = mapped_column(String, primary_key=True)
    document_json: Mapped[str] = mapped_column(Text, nullable=False)  # full LineageSpec as JSON
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

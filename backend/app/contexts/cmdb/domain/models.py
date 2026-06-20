"""CMDB schema domain models + the pure schema validator.

Schema-as-data: a CITypeSchema declares what a CI of a given type must contain (fields, required
tags, naming pattern). Validation is deterministic (no AI, ADR-0008) — it is the sole safety gate
that keeps admin-authored schemas well-formed before they are stored or consumed.
"""

from __future__ import annotations

import re
from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class FieldType(StrEnum):
    STRING = "string"
    INTEGER = "integer"
    BOOLEAN = "boolean"
    ENUM = "enum"
    DATETIME = "datetime"
    REFERENCE = "reference"  # points at another CI (lineage is modelled separately, 24.2)


class FieldDef(BaseModel):
    """One field in a CI type schema."""

    name: str
    label: str
    datatype: FieldType = FieldType.STRING
    required: bool = False
    allowed_values: list[str] | None = None  # required when datatype == enum
    regex: str | None = None  # optional value constraint (string fields)
    default: str | None = None
    sensitive: bool = False  # never surfaced in plain text / logs


class CITypeSchema(BaseModel):
    """The contract for a CI type (e.g. ``vm``): its fields, required tags, and naming pattern."""

    type: str
    label: str
    version: int = 1
    description: str = ""
    fields: list[FieldDef] = Field(default_factory=list)
    required_tags: list[str] = Field(default_factory=list)
    naming_pattern: str | None = None  # regex applied to the CI's ``name``
    updated_by: str = "system"
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


def validate_schema(schema: CITypeSchema) -> list[str]:
    """Deterministically validate a CI type schema. Returns a list of human-readable errors.

    An empty list means the schema is well-formed and safe to store/consume.
    """
    errors: list[str] = []

    if not schema.type.strip():
        errors.append("schema 'type' must be non-empty")
    if not schema.label.strip():
        errors.append("schema 'label' must be non-empty")
    if schema.version < 1:
        errors.append("schema 'version' must be >= 1")

    seen: set[str] = set()
    for f in schema.fields:
        if not f.name.strip():
            errors.append("a field has an empty name")
            continue
        if f.name in seen:
            errors.append(f"duplicate field name: '{f.name}'")
        seen.add(f.name)
        if f.datatype == FieldType.ENUM and not f.allowed_values:
            errors.append(f"enum field '{f.name}' must declare allowed_values")
        if f.allowed_values is not None and f.datatype != FieldType.ENUM:
            errors.append(f"field '{f.name}' declares allowed_values but is not an enum")
        if f.regex is not None:
            try:
                re.compile(f.regex)
            except re.error as exc:
                errors.append(f"field '{f.name}' has an invalid regex: {exc}")
        if f.default is not None and f.allowed_values and f.default not in f.allowed_values:
            errors.append(f"field '{f.name}' default '{f.default}' is not in allowed_values")

    if schema.naming_pattern is not None:
        try:
            re.compile(schema.naming_pattern)
        except re.error as exc:
            errors.append(f"naming_pattern is an invalid regex: {exc}")

    return errors

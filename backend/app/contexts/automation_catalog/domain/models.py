"""Automation catalog domain models."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field

from app.contexts.connectors.domain.models import ConnectorKind


class ApprovalState(StrEnum):
    DRAFT = "draft"
    PENDING = "pending"
    APPROVED = "approved"
    RETIRED = "retired"


class SurveyField(BaseModel):
    """One operator-facing input the template renders before execution."""

    name: str
    type: str  # "string" | "number" | "boolean" | "select"
    label: str
    required: bool = False
    default: object | None = None
    choices: list[str] | None = None
    # Optional dynamic source, e.g. "servicenow:cmdb_ci_server" -> a CMDB-backed picker.
    source: str | None = None


class Template(BaseModel):
    id: str
    name: str
    description: str = ""
    connector: ConnectorKind
    action: str
    markdown_documentation: str = ""
    supports_check_mode: bool = False
    supports_diff: bool = False
    survey: list[SurveyField] = Field(default_factory=list)
    default_params: dict[str, object] = Field(default_factory=dict)
    owner: str = "engineer"
    approval_state: ApprovalState = ApprovalState.DRAFT
    created_at: datetime
    updated_at: datetime


class TemplateDraft(BaseModel):
    """Payload to create/update a template."""

    name: str
    description: str = ""
    connector: ConnectorKind
    action: str
    markdown_documentation: str = ""
    supports_check_mode: bool = False
    supports_diff: bool = False
    survey: list[SurveyField] = Field(default_factory=list)
    default_params: dict[str, object] = Field(default_factory=dict)

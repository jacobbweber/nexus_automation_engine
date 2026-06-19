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


class RiskTier(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


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
    # Operator-facing catalog metadata (3.0) — powers faceted navigation & the detail view.
    domain: str = "General"  # Compute | Storage | Backup | Network | ITSM | Security | General
    vendor: str = ""  # VMware | Pure Storage | Cohesity | ServiceNow | Ansible | ...
    tags: list[str] = Field(default_factory=list)
    risk: RiskTier = RiskTier.LOW
    estimated_minutes: int = 5
    prerequisites: str = ""
    version: str = "1.0.0"
    atomic: bool = True  # atomic capability vs. orchestrated multi-phase workflow
    # Origin-story metadata (lifecycle validation) — authored_by == owner.
    ci_type: str | None = None  # CI type this automation targets (e.g. "server", "datastore")
    ci_heritage: str = ""
    approved_date: datetime | None = None
    last_reviewed: datetime | None = None
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
    domain: str = "General"
    vendor: str = ""
    tags: list[str] = Field(default_factory=list)
    risk: RiskTier = RiskTier.LOW
    estimated_minutes: int = 5
    prerequisites: str = ""
    atomic: bool = True
    ci_type: str | None = None
    ci_heritage: str = ""

"""Automation catalog domain models."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field

from app.contexts.connectors.domain.models import ConnectorKind
from app.shared_kernel.idempotency import IdempotencyClass


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


class PlainSummary(BaseModel):
    """Human-language description of a building block — input → action → outcome (+ rollback).

    Authored once by the automation team; composed (with resolved variables) into review packets so
    non-technical and executive reviewers see plain outcomes, not Terraform/Ansible/JSON.
    """

    input: str = ""
    action: str = ""
    outcome: str = ""
    rollback: str = ""


def default_plain_summary(
    *, name: str, action: str, vendor: str, domain: str, idempotent: bool
) -> PlainSummary:
    """Deterministically derive a starter plain summary from a block's metadata (no AI)."""
    human = action.replace("_", " ").strip().lower()
    a = action.lower()
    if any(h in a for h in ("delete", "destroy", "eradicate", "decommission", "remove")):
        outcome = f"the target {domain.lower()} resource is removed."
        rollback = "restore from the most recent snapshot/backup."
    elif any(h in a for h in ("create", "provision", "deploy", "add", "build")):
        outcome = f"a new {domain.lower()} resource is created and configured."
        rollback = "remove the newly created resource."
    elif any(h in a for h in ("patch", "update", "upgrade", "harden", "rotate")):
        outcome = f"the target {domain.lower()} resource is updated and verified healthy."
        rollback = "roll back to the prior version / restore from snapshot."
    elif any(h in a for h in ("plan", "lookup", "validate", "discover")):
        outcome = "a report is produced; nothing is changed."
        rollback = "none needed — read-only."
    else:
        outcome = f"the target {domain.lower()} resource reaches its desired state."
        rollback = "re-run is safe (idempotent)." if idempotent else "manual remediation required."
    return PlainSummary(
        input=f"A target {domain.lower()} resource managed via {vendor or 'the connector'}.",
        action=f"{name}: {human}.",
        outcome=outcome,
        rollback=rollback,
    )


class Template(BaseModel):
    id: str
    name: str
    description: str = ""
    connector: ConnectorKind
    action: str
    markdown_documentation: str = ""
    supports_check_mode: bool = False
    supports_diff: bool = False
    idempotency: IdempotencyClass = IdempotencyClass.IDEMPOTENT
    plain_summary: PlainSummary | None = None
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
    idempotency: IdempotencyClass = IdempotencyClass.IDEMPOTENT
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

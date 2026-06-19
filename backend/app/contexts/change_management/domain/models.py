"""Change management domain models."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class ChangeState(StrEnum):
    NEW = "new"
    ASSESS = "assess"
    APPROVED = "approved"
    IMPLEMENT = "implement"
    CLOSED = "closed"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


class Risk(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ChangeTemplate(BaseModel):
    """A reusable bundle of standard change fields bound to automation."""

    id: str
    name: str
    short_description: str = ""
    assignment_group: str = "Automation"
    category: str = "Standard"
    risk: Risk = Risk.LOW
    impact: str = "low"
    cab_required: bool = False
    extra_fields: dict[str, object] = Field(default_factory=dict)


class ChangeControlPolicy(BaseModel):
    """Per-resource change-control configuration."""

    id: str
    resource_type: str  # "template" | "workflow"
    resource_id: str
    auto_change_control: bool = True
    change_template_id: str | None = None
    require_approved_change: bool = False  # block live mutation unless the change is approved


class ChangeRecord(BaseModel):
    number: str  # e.g. CHG0012345
    template_id: str | None
    state: ChangeState
    short_description: str
    risk: Risk
    assignment_group: str
    cab_required: bool
    initiated_by: str
    resource_type: str
    resource_id: str
    created_at: datetime
    closed_at: datetime | None = None
    close_code: str | None = None  # "successful" | "failed" | "cancelled"

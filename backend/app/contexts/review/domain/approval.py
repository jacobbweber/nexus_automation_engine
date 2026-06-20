"""Approval request domain models — the run-level (and CI-change) human gate."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field

from app.contexts.review.domain.packet import ReviewPacket


class ApprovalStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CHANGES_REQUESTED = "changes_requested"


class ApprovalDecision(StrEnum):
    APPROVE = "approve"
    REJECT = "reject"
    REQUEST_CHANGES = "request_changes"


class ApprovalRequest(BaseModel):
    id: str
    source_type: str  # "run" | "ci_change"
    source_id: str  # workflow id or CI name
    title: str
    change_class: str
    required_level: str
    status: ApprovalStatus = ApprovalStatus.PENDING
    packet: ReviewPacket | None = None  # snapshot of what was reviewed
    requested_by: str = ""
    decided_by: str | None = None
    comment: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    decided_at: datetime | None = None
